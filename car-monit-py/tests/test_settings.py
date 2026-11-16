"""Configuration parity tests.

# Migrated from: ruoyi-admin/src/main/resources/application.yml
# Migrated from: ruoyi-admin/src/main/resources/application-druid.yml

目的：如果有人改坏了 `config/application.yml` 或 `settings.py` 的字段映射，
这些用例会立刻失败 —— 它们断言的数值全部来自 Java 的 YAML，不是 Python 的默认值。
"""

from __future__ import annotations

import pytest

from app.settings import _parse_spring_duration, _snake, get_settings, reset_settings_cache


class TestRuoYiSection:
    """``ruoyi.*`` -> ``com.ruoyi.common.config.RuoYiConfig``."""

    def test_values(self, settings) -> None:
        assert settings.ruoyi.name == "系统"
        assert settings.ruoyi.version == "3.8.7"
        assert settings.ruoyi.copyright_year == 2024
        assert settings.ruoyi.profile == "D:/ruoyi/uploadPath"
        assert settings.ruoyi.address_enabled is False
        assert settings.ruoyi.captcha_type == "math"


class TestServerSection:
    """``server.*``."""

    def test_port_matches_java(self, settings) -> None:
        assert settings.server.port == 9989

    def test_context_path_root_means_mounted_at_root(self, settings) -> None:
        # Java: server.servlet.context-path: "/" -> 所有路径挂在根上
        assert settings.server.servlet.context_path == "/"
        assert settings.context_path == ""

    def test_tomcat_threads(self, settings) -> None:
        """``server.tomcat.threads.max`` 被 main.py 用来设定 anyio 线程池上限。"""
        assert settings.server.tomcat.threads.max == 800
        assert settings.server.tomcat.threads.min_spare == 100


class TestTokenSection:
    def test_expire_time_is_minutes_and_reads_120(self, settings) -> None:
        import os
        assert settings.token.header == "Authorization"
        # JWT 密钥已改为环境变量注入，不再有内置默认值
        # pydantic env_nested_delimiter='__'，CI 注入 TOKEN__SECRET 覆盖 token.secret
        expected = os.environ.get("TOKEN__SECRET") or os.environ.get("JWT_SECRET", "")
        assert settings.token.secret == expected
        # 注意：Java 注释写「默认30分钟」，实际配置是 120
        assert settings.token.expire_time == 120


class TestRedisSection:
    def test_values(self, settings) -> None:
        assert settings.spring.redis.host == "127.0.0.1"
        assert settings.spring.redis.port == 6379
        assert settings.spring.redis.database == 0
        assert settings.spring.redis.password is None

    def test_timeout_10s_parses_to_10_seconds(self, settings) -> None:
        assert settings.spring.redis.timeout == "10s"
        assert settings.spring.redis.timeout_seconds == pytest.approx(10.0)

    def test_lettuce_pool(self, settings) -> None:
        pool = settings.spring.redis.pool
        assert pool.min_idle == 0
        assert pool.max_idle == 8
        assert pool.max_active == 8
        assert pool.max_wait == "-1ms"


class TestMonitorSection:
    def test_values(self, settings) -> None:
        assert settings.monitor.enabled is True
        assert settings.monitor.slow_request_threshold == 3000
        assert settings.monitor.slow_method_threshold == 500
        assert settings.monitor.slow_sql_threshold == 1000
        assert settings.monitor.trace_id_header == "X-Trace-Id"
        assert settings.monitor.alert_window_ms == 60000
        assert settings.monitor.alert_max_count == 5


class TestDataSourceSection:
    def test_jdbc_url_is_translated_not_copied(self, settings) -> None:
        url = settings.database_url
        # p6spy wrapper 被剥离; mysql -> mysql+pymysql。口令已改为运行时注入，
        # 默认空，不再断言硬编码的 root:root。
        assert url.startswith("mysql+pymysql://root:")
        assert "@127.0.0.1:3307/carmonitdb" in url
        assert "p6spy" not in url
        assert "charset=utf8" in url

    def test_timezone_from_jdbc_url(self, settings) -> None:
        """Java: serverTimezone=GMT%2B8 -> MySQL 会话时区 '+08:00'。"""
        assert settings.database_timezone == "+08:00"

    def test_connect_args_mirror_druid_timeouts(self, settings) -> None:
        args = settings.database_connect_args
        # connectTimeout: 30000ms -> 30s ; socketTimeout: 60000ms -> 60s
        assert args["connect_timeout"] == 30
        assert args["read_timeout"] == 60
        assert args["write_timeout"] == 60
        assert args["init_command"] == "SET time_zone='+08:00'"

    def test_druid_pool_sizes(self, settings) -> None:
        druid = settings.spring.datasource.druid
        assert druid.initial_size == 5
        assert druid.min_idle == 10
        assert druid.max_active == 200
        assert druid.max_wait == 60000
        assert druid.validation_query == "SELECT 1 FROM DUAL"


class TestSwaggerSection:
    def test_swagger_disabled_like_java(self, settings) -> None:
        """``swagger.enabled: false`` + SecurityConfig denyAll -> 文档不暴露。"""
        assert settings.swagger.enabled is False


class TestPythonOnlySwitches:
    """``app.*`` 不在 Java 配置里；每个开关都在 COMPATIBILITY.md 中有说明。"""

    def test_defaults_mirror_java_runtime(self, settings) -> None:
        # Finding A: Java 没有 @EnableScheduling -> 9 个 @Scheduled 永不触发
        assert settings.app.scheduled_annotations_enabled is False
        # Finding B: Boot 的 QuartzAutoConfiguration 提供内存 Scheduler -> 默认开启
        assert settings.app.scheduler_enabled is True
        # 运行环境里 9092 / MinIO 不可达 -> 默认关闭，启动时告警
        assert settings.app.kafka_enabled is False
        assert settings.app.oss_enabled is False
        assert settings.app.elasticsearch_enabled is True


class TestSpringHelpers:
    """Spring 语法兼容层。"""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("10s", 10.0), ("500ms", 0.5), ("-1ms", -0.001), ("2m", 120.0), ("1h", 3600.0), ("1000", 1.0)],
    )
    def test_parse_spring_duration(self, raw: str, expected: float) -> None:
        assert _parse_spring_duration(raw) == pytest.approx(expected)

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("copyrightYear", "copyright_year"),
            ("slow-request-threshold", "slow_request_threshold"),
            ("ACCESS_KEY", "access_key"),
            # 点号必须保留：logging.level.com.ruoyi 是 logger 名，不是嵌套层级
            ("logging.level.com.ruoyi", "logging.level.com.ruoyi"),
        ],
    )
    def test_snake_normalisation(self, raw: str, expected: str) -> None:
        assert _snake(raw) == expected


class TestSourcePrecedence:
    """Spring: 环境变量 > application.yml。

    回归用例：早期实现把 YAML 当构造参数传入，而 pydantic-settings 中构造参数优先级
    最高，导致环境变量永远无法覆盖 YAML —— 与 Spring 恰好相反。
    """

    def test_env_var_overrides_yaml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SERVER__PORT", "9991")
        reset_settings_cache()
        try:
            assert get_settings().server.port == 9991
        finally:
            reset_settings_cache()

    def test_env_var_overrides_nested_leaf(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SPRING__REDIS__HOST", "10.0.0.5")
        reset_settings_cache()
        try:
            assert get_settings().spring.redis.host == "10.0.0.5"
            # 未覆盖的兄弟字段仍来自 YAML
            assert get_settings().spring.redis.port == 6379
        finally:
            reset_settings_cache()

    def test_yaml_still_applies_when_env_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SERVER__PORT", raising=False)
        reset_settings_cache()
        try:
            assert get_settings().server.port == 9989
        finally:
            reset_settings_cache()


@pytest.fixture(scope="module")
def settings():
    """Fresh settings object (bypasses the process-wide lru_cache)."""
    from app.settings import reset_settings_cache

    reset_settings_cache()
    loaded = get_settings()
    yield loaded
    reset_settings_cache()
