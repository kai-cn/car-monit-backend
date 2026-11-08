"""Application settings.

# Migrated from: ruoyi-admin/src/main/resources/application.yml
# Migrated from: ruoyi-admin/src/main/resources/application-druid.yml
# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/admin/config/ShardingSphereConfig.java

Java equivalent
---------------
The Java project reads configuration in three ways:
  1. ``application.yml``               -> nested ``@ConfigurationProperties`` beans and ``@Value``
  2. ``application-druid.yml``         -> ``spring.datasource.druid.*`` (Druid connection pool)
  3. ``.idea`` / environment variables -> Spring relaxed binding (``a-b`` == ``aB`` == ``a_b``)

Python equivalent
-----------------
* ``pydantic_settings.BaseSettings`` replaces ``@ConfigurationProperties``.
* Section nesting is preserved 1:1 so that ``application.yml`` can be diffed against
  :class:`AppSettings` line by line (see ``MIGRATION_GUIDE.md`` -> Configuration parity).
* Spring "relaxed binding" is emulated by :func:`_normalize_keys`, which converts
  ``slow-request-threshold`` / ``copyrightYear`` into ``slow_request_threshold`` /
  ``copyright_year`` before validation.
* Environment variables override YAML. Nested keys use ``__`` as separator, e.g.
  ``SPRING__REDIS__HOST=10.0.0.5`` or ``TOKEN__SECRET=...``.
"""

from __future__ import annotations

import functools
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Project root = .../car-monit-py
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
# Directory holding the YAML mirror of the Java resources (config/application.yml).
CONFIG_DIR: Path = PROJECT_ROOT / "config"

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _snake(name: str) -> str:
    """Convert a Spring/camelCase config key to snake_case.

    ``copyrightYear``          -> ``copyright_year``
    ``slow-request-threshold`` -> ``slow_request_threshold``

    Dots are preserved on purpose: ``logging.level.com.ruoyi`` is a *logger name*
    key, so turning it into ``com_ruoyi`` would break the logger mapping.
    """
    name = name.replace("-", "_")
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def _normalize_keys(value: Any) -> Any:
    """Recursively normalize dict keys; emulate Spring relaxed binding."""
    if isinstance(value, dict):
        return {_snake(str(k)): _normalize_keys(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_keys(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Section models  (one class per top-level YAML block)
# ---------------------------------------------------------------------------
class _Section(BaseModel):
    """Base for every YAML section: tolerate unknown keys, allow snake_case init."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class RuoYiSection(_Section):
    """``ruoyi.*`` -- mapped to ``com.ruoyi.common.config.RuoYiConfig``.

    Java 的 ``RuoYiConfig`` 只有 6 个字段，但 ``profile`` 派生出 4 个上传子目录；
    派生值在 Java 里是静态方法（``getAvatarPath()`` 等），这里落成只读属性，
    调用点仍然读作 ``get_settings().ruoyi.avatar_path``。拼接规则逐字复制
    （``getDownloadPath()`` 末尾那一个 ``/`` 也在）。
    """

    name: str = "系统"
    version: str = "3.8.7"
    copyright_year: int = 2024
    profile: str = "D:/ruoyi/uploadPath"
    address_enabled: bool = False
    captcha_type: str = "math"  # math | char

    # Java: public static String getImportPath() -> getProfile() + "/import"
    @property
    def import_path(self) -> str:
        return self.profile + "/import"

    # Java: public static String getAvatarPath() -> getProfile() + "/avatar"
    @property
    def avatar_path(self) -> str:
        return self.profile + "/avatar"

    # Java: public static String getDownloadPath() -> getProfile() + "/download/"
    @property
    def download_path(self) -> str:
        return self.profile + "/download/"

    # Java: public static String getUploadPath() -> getProfile() + "/upload"
    @property
    def upload_path(self) -> str:
        return self.profile + "/upload"


class ProfilesSection(_Section):
    """``spring.profiles.active``."""

    active: str = "druid"


class MessagesSection(_Section):
    """``spring.messages`` -- i18n bundle location."""

    basename: str = "i18n/messages"


class ServletSection(_Section):
    context_path: str = "/"


class TomcatThreadsSection(_Section):
    """``server.tomcat.threads`` -- accepted for parity, not enforced by uvicorn."""

    max: int = 800
    min_spare: int = 100


class TomcatSection(_Section):
    """``server.tomcat`` -- Tomcat-only settings kept for documentation parity."""

    uri_encoding: str = "UTF-8"
    accept_count: int = 1000
    threads: TomcatThreadsSection = Field(default_factory=TomcatThreadsSection)


class ServerSection(_Section):
    """``server.*`` -- only ``port`` and ``servlet.context_path`` change behaviour."""

    port: int = 9989
    servlet: ServletSection = Field(default_factory=ServletSection)
    tomcat: TomcatSection = Field(default_factory=TomcatSection)


class LoggingSection(_Section):
    """``logging.level.*`` -- logger name -> level."""

    level: Dict[str, str] = Field(default_factory=lambda: {"com.ruoyi": "debug", "org.springframework": "warn"})


class MonitorSection(_Section):
    """``monitor.*`` -- custom tracing / slow-request / alerting subsystem."""

    enabled: bool = True
    slow_request_threshold: int = 3000
    slow_method_threshold: int = 500
    slow_sql_threshold: int = 1000
    trace_id_header: str = "X-Trace-Id"
    alert_window_ms: int = 60000
    alert_max_count: int = 5


class PasswordSection(_Section):
    max_retry_count: int = 5
    lock_time: int = 10


class UserSection(_Section):
    password: PasswordSection = Field(default_factory=PasswordSection)


class MultipartSection(_Section):
    max_file_size: str = "40MB"
    max_request_size: str = "200MB"


class ServletMultipartSection(_Section):
    multipart: MultipartSection = Field(default_factory=MultipartSection)


class LettucePoolSection(_Section):
    """``spring.redis.lettuce.pool``."""

    min_idle: int = 0
    max_idle: int = 8
    max_active: int = 8
    max_wait: str = "-1ms"


class LettuceSection(_Section):
    pool: LettucePoolSection = Field(default_factory=LettucePoolSection)


class RedisSection(_Section):
    host: str = "127.0.0.1"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    timeout: str = "10s"
    lettuce: LettuceSection = Field(default_factory=LettuceSection)

    @property
    def timeout_seconds(self) -> float:
        """Parse Spring duration syntax (``10s`` / ``500ms``) into seconds."""
        return _parse_spring_duration(self.timeout)

    @property
    def pool(self) -> LettucePoolSection:
        """Shortcut mirroring ``spring.redis.lettuce.pool``."""
        return self.lettuce.pool


class MasterDataSourceSection(_Section):
    """``spring.datasource.druid.master.*`` -- Druid master pool."""

    url: str = (
        "jdbc:p6spy:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8"
        "&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true"
    )
    username: str = "root"
    password: str = "root"


class DruidSection(_Section):
    master: MasterDataSourceSection = Field(default_factory=MasterDataSourceSection)
    # slave is declared in application-druid.yml but enabled: false -> master only.
    initial_size: int = 5
    min_idle: int = 10
    max_active: int = 200
    max_wait: int = 60000
    connect_timeout: int = 30000
    socket_timeout: int = 60000
    validation_query: str = "SELECT 1 FROM DUAL"
    # Druid console (``/druid/**``) is denyAll() in SecurityConfig -> not ported as a feature.
    stat_view_servlet_enabled: bool = True


class DataSourceSection(_Section):
    driver_class_name: str = "com.p6spy.engine.spy.P6SpyDriver"
    druid: DruidSection = Field(default_factory=DruidSection)


class SpringSection(_Section):
    profiles: ProfilesSection = Field(default_factory=ProfilesSection)
    messages: MessagesSection = Field(default_factory=MessagesSection)
    servlet: ServletMultipartSection = Field(default_factory=ServletMultipartSection)
    redis: RedisSection = Field(default_factory=RedisSection)
    datasource: DataSourceSection = Field(default_factory=DataSourceSection)

    @property
    def profiles_active(self) -> str:
        """``spring.profiles.active`` (only ``druid`` exists in this project)."""
        return self.profiles.active

    @property
    def messages_basename(self) -> str:
        """``spring.messages.basename``."""
        return self.messages.basename


class TokenSection(_Section):
    header: str = "Authorization"
    secret: str = "abcdefghijklmnopqrstuvwxyz"
    # application.yml: expireTime: 120  (minutes, RuoYi default comment says 30)
    expire_time: int = 120


class MyBatisPlusDbConfig(_Section):
    id_type: str = "ASSIGN_ID"
    table_underline: bool = True


class MyBatisPlusGlobalConfig(_Section):
    banner: bool = False
    db_config: MyBatisPlusDbConfig = Field(default_factory=MyBatisPlusDbConfig)


class MyBatisPlusSection(_Section):
    global_config: MyBatisPlusGlobalConfig = Field(default_factory=MyBatisPlusGlobalConfig)
    type_aliases_package: str = "com.ruoyi.**.domain,com.ruoyi.**.bean"
    mapper_locations: str = "classpath*:mapper/**/*Mapper.xml"
    config_location: str = "classpath:mybatis/mybatis-config.xml"


class PageHelperSection(_Section):
    helper_dialect: str = "mysql"
    support_methods_arguments: bool = True
    params: str = "count=countSql"


class SwaggerSection(_Section):
    enabled: bool = False
    path_mapping: str = "/dev-api"


class XssSection(_Section):
    enabled: bool = True
    excludes: str = "/system/notice"
    url_patterns: str = "/system/*,/monitor/*,/tool/*"


class OssSection(_Section):
    """``oss.*`` -- MinIO/S3, mapped to ``OssAutoConfiguration`` + aws-sdk-s3.

    ``application.yml`` 只写了 4 个键（``endpoint`` / ``accessKey`` / ``secretKey`` /
    ``bucketName``），其余 5 个是 :class:`OssProperties` 的 Lombok 字段默认值，逐个抄下来
    —— 少抄一个就会把 ``region=null`` 传给 SDK 而改变建连参数。

    另外两个键不来自 ``OssProperties``，而来自 ``OssAutoConfiguration`` 上的
    ``@ConditionalOnProperty``：

    * ``oss.enable`` —— ``matchIfMissing = true``，所以**缺省为真**；
    * ``oss.info``   —— 缺省 ``false``，因此 ``OssEndpoint`` 的 ``/oss/**`` 端点默认
      根本不会被注册（本项目也没有装）。
    """

    endpoint: str = "http://172.30.100.102:9002"
    access_key: str = "jtwl_access_key"
    secret_key: str = "minio.prod"
    bucket_name: str = "developer"
    #: true = path-style（``http://endpoint/bucketname``），false = virtual-hosted-style
    path_style_access: bool = True
    app_id: Optional[str] = None
    region: Optional[str] = None
    max_connections: int = 100
    enable: bool = True
    info: bool = False


class SmsSection(_Section):
    """``sms.*`` -- Aliyun SMS.

    All keys ship **empty** in ``application.yml`` (``signature:`` with no value), which
    YAML parses as ``null``, not ``""``. Spring binds them to ``null`` String fields, so
    the Python types are ``Optional[str] = None`` -- using ``""`` here would silently
    change a null check such as ``if (StringUtils.isNotEmpty(signature))``.
    """

    signature: Optional[str] = None
    access_key_id: Optional[str] = None
    access_key_secret: Optional[str] = None
    send_code_templete: Optional[str] = None
    send_check_person_notice_templete: Optional[str] = None
    send_expert_notice_templete: Optional[str] = None
    send_supplier_invitations_notice_templete: Optional[str] = None
    send_invitation_supplier_template: Optional[str] = None
    send_yckb_supplier_template: Optional[str] = None


class ForestSection(_Section):
    """``forest.*`` -- declarative HTTP client."""

    bean_id: str = "forestConfiguration"
    backend: str = "httpclient"
    max_connections: int = 1000
    max_route_connections: int = 500
    timeout: int = 60000
    connect_timeout: int = 60000
    log_enabled: bool = True
    retryer: str = "com.dtflys.forest.retryer.BackOffRetryer"
    retry_count: int = 2
    max_retry_interval: int = 1000
    variables: Dict[str, str] = Field(default_factory=lambda: {"hendaUrl": "http://36.200.20.14:7890/8809/geoserver-pg/rest"})


class HengdaSection(_Section):
    appid: str = "YHZS"
    secret: str = "b48381c4b98311ea90b100155d14fa3b"


class VehicleMonitorSection(_Section):
    base_url: str = "http://127.0.0.1:9901"


class KafkaConsumerSection(_Section):
    group_id: str = "snapshot-flow-consumer-group"
    enable_auto_commit: bool = False
    auto_offset_reset: str = "earliest"
    key_deserializer: str = "org.apache.kafka.common.serialization.StringDeserializer"
    value_deserializer: str = "org.apache.kafka.common.serialization.StringDeserializer"
    max_poll_records: int = 500
    max_poll_interval_ms: int = 300000
    fetch_max_bytes: int = 52428800
    session_timeout_ms: int = 60000


class KafkaProducerSection(_Section):
    key_serializer: str = "org.apache.kafka.common.serialization.StringSerializer"
    value_serializer: str = "org.apache.kafka.common.serialization.StringSerializer"
    acks: str = "all"
    retries: int = 3


class KafkaTopicSection(_Section):
    snapshot_flow: str = "ods-rt-szdn-snapshot-flow"
    snapshot_flow_dlq: str = "ods-rt-szdn-snapshot-flow-dlq"


class KafkaListenerSection(_Section):
    ack_mode: str = "manual_immediate"
    concurrency: int = 3


class KafkaSection(_Section):
    bootstrap_servers: str = "127.0.0.1:9092"
    topic: KafkaTopicSection = Field(default_factory=KafkaTopicSection)
    consumer: KafkaConsumerSection = Field(default_factory=KafkaConsumerSection)
    producer: KafkaProducerSection = Field(default_factory=KafkaProducerSection)
    listener: KafkaListenerSection = Field(default_factory=KafkaListenerSection)


class ElasticsearchSection(_Section):
    """``elasticsearch.*``.

    NOTE: in ``application.yml`` the index key is written as::

        index:
          snapshot-flow

    which YAML parses as the plain string ``"snapshot-flow"``. Java binds it with
    ``@Value("${elasticsearch.index:snapshot-flow}")`` on a ``String`` field
    (``SnapshotFlowElasticsearchService``), so the type here is ``str`` too.
    """

    host: str = "127.0.0.1"
    port: int = 9200
    index: str = "snapshot-flow"


class IdempotentRedisSection(_Section):
    prefix: str = "snapshot:flow:idempotent_"
    expire_time: int = 86400


class IdempotentSection(_Section):
    redis: IdempotentRedisSection = Field(default_factory=IdempotentRedisSection)


class SnapshotFlowShardingSection(_Section):
    enabled: bool = True
    table_prefix: str = "ods_rt_szdn_snapshot_flow_"
    sharding_field: str = "snapshottime"
    sharding_type: str = "month"


class SnapshotFlowSection(_Section):
    sharding: SnapshotFlowShardingSection = Field(default_factory=SnapshotFlowShardingSection)


class SnapshotSection(_Section):
    flow: SnapshotFlowSection = Field(default_factory=SnapshotFlowSection)


class GeneratorMyBatisPlusSection(_Section):
    enable: bool = True


class GeneratorCodeSection(_Section):
    mybatis_plus: GeneratorMyBatisPlusSection = Field(default_factory=GeneratorMyBatisPlusSection)


class AppSection(_Section):
    """Python-only switches.

    Not present in application.yml. Each one exists to *preserve* Java runtime
    behaviour rather than to add features -- see ``COMPATIBILITY.md``.
    """

    # Phase 5 requirement: health probe. Java has no actuator; ``/`` is the only
    # existing liveness endpoint. This flag enables an extra ``/health`` route.
    health_endpoint_enabled: bool = True
    # Finding B: Quartz auto-configures an in-memory scheduler that reloads
    # sys_job on boot. app/quartz/util/scheduler.py mirrors that (no APScheduler).
    # Set false to boot without it.
    scheduler_enabled: bool = True
    # Finding A: no @EnableScheduling exists in the Java project, so the nine
    # @Scheduled methods never fire. Keep false to mirror that behaviour.
    scheduled_annotations_enabled: bool = False
    # Middleware toggles -- Kafka and MinIO are currently unreachable.
    kafka_enabled: bool = False
    elasticsearch_enabled: bool = True
    oss_enabled: bool = False
    # Emit the RuoYi startup banner / banner.txt equivalent to stdout.
    banner_enabled: bool = True


# ---------------------------------------------------------------------------
# Spring helpers
# ---------------------------------------------------------------------------
_DURATION_UNITS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


def _parse_spring_duration(value: str) -> float:
    """Parse Spring ``Duration`` shorthand: ``10s``, ``500ms``, ``-1ms``, ``2m``.

    A bare number is interpreted as milliseconds (Spring's default unit for
    ``spring.redis.timeout`` is milliseconds).
    """
    text = str(value).strip()
    match = re.fullmatch(r"(-?\d+(?:\.\d+)?)(ms|s|m|h)?", text)
    if not match:
        raise ValueError(f"Unsupported Spring duration: {value!r}")
    amount = float(match.group(1))
    unit = match.group(2) or "ms"
    return amount * _DURATION_UNITS[unit]


def jdbc_to_sqlalchemy_url(jdbc_url: str, username: str, password: str) -> str:
    """Translate a Spring JDBC URL into a SQLAlchemy URL.

    ``jdbc:p6spy:mysql://host:port/db?...`` -> ``mysql+pymysql://user:pwd@host:port/db?charset=utf8``

    The ``p6spy`` wrapper is dropped: its purpose in Java was SQL logging, which
    is re-implemented as a SQLAlchemy ``before_cursor_execute`` listener.
    """
    url = jdbc_url
    for prefix in ("jdbc:p6spy:", "jdbc:"):
        if url.startswith(prefix):
            url = url[len(prefix):]
            break
    if url.startswith("mysql://"):
        url = "mysql+pymysql://" + url[len("mysql://"):]

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    # Java sends characterEncoding=utf8; PyMySQL expects charset.
    charset = (query.get("characterEncoding") or query.get("charset") or ["utf8"])[0]
    # Java sends serverTimezone=GMT+8 (URL-encoded); reused by database_connect_args.
    timezone = (query.get("serverTimezone") or [""])[0]
    del timezone  # validated for parity only; consumed by AppSettings.database_timezone

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 3306
    database = (parsed.path or "/").lstrip("/")

    from urllib.parse import quote_plus

    auth = f"{quote_plus(username)}:{quote_plus(password)}" if username else ""
    # NOTE: serverTimezone is *not* appended to the URL. PyMySQL expects
    # ``init_command`` as a connect_arg (see AppSettings.database_connect_args),
    # because the statement contains ``=``, ``+`` and quotes that would corrupt
    # the query string.
    return f"mysql+pymysql://{auth}@{host}:{port}/{database}?charset={charset}"


def _tz_offset(spring_tz: str) -> str:
    """``GMT+8`` -> ``+08:00``; ``Asia/Shanghai`` passes through."""
    match = re.fullmatch(r"(?:GMT|UTC)?([+-])(\d{1,2})", spring_tz)
    if match:
        sign, hours = match.group(1), int(match.group(2))
        return f"{sign}{hours:02d}:00"
    return spring_tz


class _AppEnvSettingsSource(EnvSettingsSource):
    """OS 环境变量源：屏蔽与 section 同名的系统变量。

    根配置没有 env_prefix，``user`` section 会和 shell / CI / 容器几乎必设的
    ``USER`` 撞名（``USER=runner`` 会被当成嵌套模型去解析）。这里让 ``user``
    只认显式的 ``APP_USER``（JSON），其他字段仍走默认规则。
    """

    _FIELD_ALIASES = {"user": "app_user"}

    def get_field_value(self, field, field_name):
        alias = self._FIELD_ALIASES.get(field_name)
        if alias is not None:
            raw = self.env_vars.get(alias)
            if raw is None:
                raw = self.env_vars.get(alias.upper())
            return (raw, field_name, True)
        return super().get_field_value(field, field_name)


# ---------------------------------------------------------------------------
# Root settings
# ---------------------------------------------------------------------------
class AppSettings(BaseSettings):
    """Root configuration object; one attribute per ``application.yml`` top-level block."""

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    ruoyi: RuoYiSection = Field(default_factory=RuoYiSection)
    server: ServerSection = Field(default_factory=ServerSection)
    logging: LoggingSection = Field(default_factory=LoggingSection)
    monitor: MonitorSection = Field(default_factory=MonitorSection)
    # 环境变量入口固定为 APP_USER。否则几乎每个 shell / CI / 容器都会设置的
    # USER（如 USER=runner）会被当成嵌套模型解析，直接 SettingsError 起不来。
    # 见下方 _AppEnvSettingsSource。
    user: UserSection = Field(default_factory=UserSection)
    spring: SpringSection = Field(default_factory=SpringSection)
    token: TokenSection = Field(default_factory=TokenSection)
    mybatis_plus: MyBatisPlusSection = Field(default_factory=MyBatisPlusSection)
    pagehelper: PageHelperSection = Field(default_factory=PageHelperSection)
    generator_code: GeneratorCodeSection = Field(default_factory=GeneratorCodeSection)
    swagger: SwaggerSection = Field(default_factory=SwaggerSection)
    xss: XssSection = Field(default_factory=XssSection)
    oss: OssSection = Field(default_factory=OssSection)
    sms: SmsSection = Field(default_factory=SmsSection)
    forest: ForestSection = Field(default_factory=ForestSection)
    hengda: HengdaSection = Field(default_factory=HengdaSection)
    vehicle_monitor: VehicleMonitorSection = Field(default_factory=VehicleMonitorSection)
    is_localhost: str = "local"
    tx_service_url: str = "https://apis.map.qq.com"
    road_path_url: str = "http://36.200.30.117:8080"
    kafka: KafkaSection = Field(default_factory=KafkaSection)
    elasticsearch: ElasticsearchSection = Field(default_factory=ElasticsearchSection)
    idempotent: IdempotentSection = Field(default_factory=IdempotentSection)
    snapshot: SnapshotSection = Field(default_factory=SnapshotSection)
    app: AppSection = Field(default_factory=AppSection)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Spring-compatible source precedence (first = highest).

        Spring: 命令行参数 > OS 环境变量 > application.yml > 默认值
        Python: 构造参数 > OS 环境变量 > .env > config/application.yml > secrets > 字段默认值
        """
        return (
            init_settings,
            _AppEnvSettingsSource(settings_cls),
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls, _yaml_path()),
            file_secret_settings,
        )

    # -- derived helpers -------------------------------------------------
    @property
    def database_url(self) -> str:
        """SQLAlchemy URL built from the Druid master JDBC URL."""
        master = self.spring.datasource.druid.master
        return jdbc_to_sqlalchemy_url(master.url, master.username, master.password)

    @property
    def database_timezone(self) -> str:
        """``serverTimezone`` from the JDBC URL, normalised to a MySQL offset (``+08:00``)."""
        master_url = self.spring.datasource.druid.master.url
        query = parse_qs(urlparse(master_url).query)
        raw = (query.get("serverTimezone") or [""])[0]
        return _tz_offset(raw) if raw else "+08:00"

    @property
    def database_connect_args(self) -> Dict[str, Any]:
        """PyMySQL connect args mirroring the Druid ``connectTimeout``/``socketTimeout``."""
        druid = self.spring.datasource.druid
        return {
            # Java: serverTimezone=GMT+8 -> session time zone on every new connection.
            "init_command": f"SET time_zone='{self.database_timezone}'",
            # Java: connectTimeout: 30000 ms, socketTimeout: 60000 ms
            "connect_timeout": max(1, druid.connect_timeout // 1000),
            "read_timeout": max(1, druid.socket_timeout // 1000),
            "write_timeout": max(1, druid.socket_timeout // 1000),
        }

    @property
    def context_path(self) -> str:
        """``server.servlet.context-path``; ``/`` means "mount at root"."""
        path = self.server.servlet.context_path or "/"
        return "" if path == "/" else path.rstrip("/")

    def log_levels(self) -> Dict[str, str]:
        """Translate ``logging.level.com.ruoyi`` into Python logger names."""
        levels: Dict[str, str] = {}
        for name, level in self.logging.level.items():
            levels[name] = level.upper()
        return levels


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        return {}
    return _normalize_keys(loaded)


def _yaml_path() -> Path:
    """``config/application.yml``, overridable with ``CM_CONFIG_FILE``."""
    configured = os.environ.get("CM_CONFIG_FILE")
    return Path(configured) if configured else CONFIG_DIR / "application.yml"


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Lowest-priority settings source: the YAML mirror of ``application.yml``.

    为什么不把 YAML 直接当构造参数传？
        pydantic-settings 中**构造函数参数优先级最高**，高于环境变量。若写成
        ``AppSettings(**yaml)``，环境变量和 ``.env`` 就永远无法覆盖 YAML，
        与 Spring 的优先级（命令行 > 环境变量 > application.yml）恰好相反。

    实现为独立 source 之后，优先级由 :meth:`AppSettings.settings_customise_sources`
    决定，与 Spring 一致：

        构造参数 > 环境变量 > .env > config/application.yml > secrets > 字段默认值
    """

    def __init__(self, settings_cls: type[BaseSettings], yaml_path: Path) -> None:
        super().__init__(settings_cls)
        self._yaml_path = yaml_path

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        """Unused: the whole mapping is returned by :meth:`__call__`."""
        return None, field_name, False

    def __call__(self) -> Dict[str, Any]:
        return _load_yaml(self._yaml_path)


@functools.lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load settings once per process.

    Precedence (highest first):
      1. environment variables / ``.env``   (``SPRING__REDIS__HOST=...``)
      2. ``config/application.yml``         (mirror of the Java resources)
      3. defaults declared on the section models

    实际优先级由 :meth:`AppSettings.settings_customise_sources` 实现：
    构造参数 > 环境变量 > ``.env`` > ``config/application.yml`` > 字段默认值。
    这里不再把 YAML 当构造参数传入，否则会盖掉环境变量。
    """
    return AppSettings()


def reset_settings_cache() -> None:
    """Test helper: drop the cached settings object."""
    get_settings.cache_clear()
