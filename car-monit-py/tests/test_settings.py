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
        assert settings.token.header == "Authorization"
        # 密钥不再有内置默认值；测试进程由 conftest 注入测试专用值。
        assert settings.token.secret == (
            "cHl0ZXN0LW9ubHktand0LXNpZ25pbmcta2V5LTAxMjM0NTY3ODlhYmNkZWZnaGlqa2xtbg=="
        )
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
        # p6spy wrapper 被剥离; mysql -> mysql+pymysql；口令来自测试环境变量
        assert url.startswith("mysql+pymysql://root:test-db-password@127.0.0.1:3307/carmonitdb")
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
        # 请求线程池上限默认与 Druid maxActive 对齐（不是 Tomcat 的 800）
        assert settings.app.request_thread_limit == 200


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


class TestFailClosedSecrets:
    """密钥缺失/内置演示值/占位值必须拒绝启动（所有环境；local 不再豁免）.

    统一用 ``_env_file=None`` 隔离 cwd 的 ``.env``：否则本地开发机按文档建了
    ``.env`` 后，"密钥缺失"用例会被 dotenv 悄悄补齐而变成假绿。
    """

    _REQUIRED = (
        "TOKEN__SECRET",
        "SPRING__DATASOURCE__DRUID__MASTER__PASSWORD",
        "HENGDA__SECRET",
    )

    _VALID_TOKEN = (
        "cHl0ZXN0LW9ubHktand0LXNpZ25pbmcta2V5LTAxMjM0NTY3ODlhYmNkZWZnaGlqa2xtbg=="
    )
    _VALID_HENGDA = "pytest-only-hengda-signing-key-4d8e1a6b2f9c0357"

    def _base(self) -> dict:
        """一套合法配置；各用例只在需要验证的分支上做替换。"""
        return {
            "is_localhost": "prod",
            "token": {"secret": self._VALID_TOKEN},
            "spring": {"datasource": {"druid": {"master": {"password": "prod-db-password"}}}},
            "hengda": {"secret": self._VALID_HENGDA},
        }

    def _clear_required(self, monkeypatch) -> None:
        for name in self._REQUIRED:
            monkeypatch.delenv(name, raising=False)

    def test_missing_secrets_reject_startup_even_in_local(self, monkeypatch) -> None:
        from pydantic import ValidationError

        from app.settings import AppSettings

        self._clear_required(monkeypatch)
        with pytest.raises(ValidationError) as excinfo:
            AppSettings(_env_file=None, is_localhost="local")
        message = str(excinfo.value)
        assert "TOKEN__SECRET" in message
        assert "SPRING__DATASOURCE__DRUID__MASTER__PASSWORD" in message
        assert "HENGDA__SECRET" in message

    def test_missing_secrets_survive_a_cwd_dotenv(self, tmp_path, monkeypatch) -> None:
        """本机按文档建了 ``.env`` 时，"密钥缺失"用例不能被 dotenv 悄悄补齐。

        没有 ``_env_file=None`` 时，下面的 ``AppSettings`` 会读到 tmp_path/.env 并
        成功构造，``pytest.raises`` 直接失败 —— 这正是 CI 无 .env、本地必红的成因。
        """
        from pydantic import ValidationError

        from app.settings import AppSettings

        self._clear_required(monkeypatch)
        (tmp_path / ".env").write_text(
            f"TOKEN__SECRET={self._VALID_TOKEN}\n"
            "SPRING__DATASOURCE__DRUID__MASTER__PASSWORD=prod-db-password\n"
            f"HENGDA__SECRET={self._VALID_HENGDA}\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        # 正对照：不隔离时 dotenv 确实会补齐（证明下面的负用例有意义）。
        assert AppSettings(is_localhost="local").token.secret == self._VALID_TOKEN

        with pytest.raises(ValidationError, match="TOKEN__SECRET"):
            AppSettings(_env_file=None, is_localhost="local")

    def test_legacy_demo_values_are_rejected(self, monkeypatch) -> None:
        from pydantic import ValidationError

        from app.settings import AppSettings

        monkeypatch.setenv("TOKEN__SECRET", "abcdefghijklmnopqrstuvwxyz")
        monkeypatch.setenv("SPRING__DATASOURCE__DRUID__MASTER__PASSWORD", "root")
        monkeypatch.setenv("HENGDA__SECRET", "b48381c4b98311ea90b100155d14fa3b")

        with pytest.raises(ValidationError, match="TOKEN__SECRET"):
            AppSettings(_env_file=None, is_localhost="local")

    @pytest.mark.parametrize(
        ("name", "override"),
        [
            ("TOKEN__SECRET", {"token": {"secret": "dev-only-jwt-secret-please-change"}}),
            ("HENGDA__SECRET", {"hengda": {"secret": "dev-only-hengda-secret-please-change"}}),
        ],
    )
    def test_env_example_placeholders_are_rejected_on_each_branch(
        self, name: str, override: dict
    ) -> None:
        """``.env.example`` 曾内置的两个占位值必须在 prod 下被拒绝。

        每个分支单独提供**其它合法密钥**，这样删掉 token/hengda 的任一指纹判断
        都会立刻变红，而不是被"token 先报错"掩盖。
        """
        from pydantic import ValidationError

        from app.settings import AppSettings

        values = self._base()
        values.update(override)
        with pytest.raises(ValidationError, match=name):
            AppSettings(_env_file=None, **values)

    def test_env_example_ships_no_active_secret_or_profile_value(self) -> None:
        """示例文件必须让部署者显式生成密钥/选择环境，不能直接启动。"""
        from app.settings import PROJECT_ROOT

        lines = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
        active = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
        forbidden_prefixes = (
            "IS_LOCALHOST=",
            "TOKEN__SECRET=",
            "HENGDA__SECRET=",
            "SPRING__DATASOURCE__DRUID__MASTER__PASSWORD=",
        )
        assert [line for line in active if line.startswith(forbidden_prefixes)] == []

    def test_each_legacy_fingerprint_kind_still_matches(self) -> None:
        """四个指纹分支各自独立：删掉任一分支的比对都会让本用例变红."""
        from app.settings import _is_legacy_demo_secret

        assert _is_legacy_demo_secret("abcdefghijklmnopqrstuvwxyz", "token")
        assert _is_legacy_demo_secret("b48381c4b98311ea90b100155d14fa3b", "hengda")
        assert _is_legacy_demo_secret("jtwl_access_key", "oss_access")
        assert _is_legacy_demo_secret("minio.prod", "oss_secret")
        assert not _is_legacy_demo_secret(self._VALID_TOKEN, "token")
        assert not _is_legacy_demo_secret(None, "token")

    def test_legacy_hengda_fingerprint_is_rejected_independently(self) -> None:
        from pydantic import ValidationError

        from app.settings import AppSettings

        values = self._base()
        values["hengda"] = {"secret": "b48381c4b98311ea90b100155d14fa3b"}
        with pytest.raises(ValidationError, match="HENGDA__SECRET"):
            AppSettings(_env_file=None, **values)

    @pytest.mark.parametrize("weak", ["short-secret", "a" * 40, "your-secret-here-" + "0" * 20])
    def test_short_low_entropy_and_placeholder_values_are_rejected(self, weak: str) -> None:
        """长度/熵/占位词校验挡住与 ``.env.example`` 同类的示例值。"""
        from pydantic import ValidationError

        from app.settings import AppSettings

        values = self._base()
        values["token"] = {"secret": weak}
        with pytest.raises(ValidationError, match="TOKEN__SECRET"):
            AppSettings(_env_file=None, **values)

    def test_local_still_allows_the_bundled_mysql_root_password(self, monkeypatch) -> None:
        from app.settings import AppSettings

        monkeypatch.setenv("SPRING__DATASOURCE__DRUID__MASTER__PASSWORD", "root")
        loaded = AppSettings(_env_file=None, is_localhost="local")
        assert loaded.spring.datasource.druid.master.password == "root"

    def test_non_local_rejects_root_db_password(self, monkeypatch) -> None:
        from pydantic import ValidationError

        from app.settings import AppSettings

        monkeypatch.setenv("SPRING__DATASOURCE__DRUID__MASTER__PASSWORD", "root")
        with pytest.raises(ValidationError, match="SPRING__DATASOURCE__DRUID__MASTER__PASSWORD"):
            AppSettings(_env_file=None, is_localhost="prod")

    def test_real_secrets_are_accepted(self) -> None:
        from app.settings import AppSettings

        loaded = AppSettings(_env_file=None, **self._base())
        assert loaded.insecure_secret_env_vars() == []

    def test_oss_keys_are_checked_only_when_enabled(self) -> None:
        from pydantic import ValidationError

        from app.settings import AppSettings

        values = self._base()
        # app.oss_enabled 默认 False -> 不校验 OSS 凭据
        AppSettings(_env_file=None, **values)

        with pytest.raises(ValidationError, match="OSS__ACCESS_KEY"):
            AppSettings(_env_file=None, **values, app={"oss_enabled": True})

    @pytest.mark.parametrize(
        ("name", "oss"),
        [
            ("OSS__ACCESS_KEY", {"access_key": "jtwl_access_key", "secret_key": "minio.prod"}),
            ("OSS__SECRET_KEY", {"access_key": "AKIAIOSFODNN7EXAMPLE", "secret_key": "minio.prod"}),
        ],
    )
    def test_oss_legacy_values_are_rejected_on_each_branch(
        self, name: str, oss: dict
    ) -> None:
        """OSS 的两个指纹分支各自独立覆盖（删除任一条都会变红）。"""
        from pydantic import ValidationError

        from app.settings import AppSettings

        values = self._base()
        values["app"] = {"oss_enabled": True}
        values["oss"] = oss
        with pytest.raises(ValidationError, match=name):
            AppSettings(_env_file=None, **values)


class TestThreadParity:
    """``_apply_tomcat_thread_parity`` 必须在 lifespan 启动时被调用."""

    def test_lifespan_calls_the_thread_parity_helper(self, monkeypatch) -> None:
        from fastapi.testclient import TestClient

        from app import main as main_module
        from app.settings import AppSettings

        called = []

        def spy(settings) -> None:
            called.append(settings.app.request_thread_limit)

        monkeypatch.setattr(main_module, "_apply_tomcat_thread_parity", spy)
        test_settings = AppSettings(app={"scheduler_enabled": False})
        with TestClient(main_module.create_app(test_settings)) as client:
            assert client.get("/health").status_code == 200

        # 删掉 lifespan 里的调用，called 为空 -> 变红
        assert called == [200]

    def test_helper_sets_anyio_total_tokens(self, settings) -> None:
        import asyncio

        from app.main import _apply_tomcat_thread_parity

        async def run() -> int:
            import anyio.to_thread

            limiter = anyio.to_thread.current_default_thread_limiter()
            before = limiter.total_tokens
            try:
                _apply_tomcat_thread_parity(settings)
                return limiter.total_tokens
            finally:
                limiter.total_tokens = before

        assert asyncio.run(run()) == 200


class TestPackagedConfigAssets:
    """wheel 必须带上 ``config/`` 的全部 61 个运行期资产."""

    def test_pyproject_data_files_cover_all_config_assets(self) -> None:
        import tomllib

        from app.settings import PROJECT_ROOT

        pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        data_files = pyproject["tool"]["setuptools"]["data-files"]

        matched = set()
        for patterns in data_files.values():
            for pattern in patterns:
                matched.update(PROJECT_ROOT.glob(pattern))

        # 清单断言：新增/删除资产必须同步更新 pyproject 与这里，避免 wheel 漏文件。
        assert len(matched) == 61
        for path in matched:
            assert path.is_file()
            assert path.stat().st_size > 0


class TestYamlPath:
    """非 editable 安装：源码目录没有 config/，要回退到 data-files 安装位置."""

    def test_config_dir_falls_back_to_prefix_install(self, tmp_path, monkeypatch) -> None:
        from app import settings as settings_module

        monkeypatch.setattr(settings_module, "PROJECT_ROOT", tmp_path / "src")
        monkeypatch.setattr(settings_module.sys, "prefix", str(tmp_path / "prefix"))
        installed = tmp_path / "prefix" / "config"
        installed.mkdir(parents=True)

        assert settings_module._config_dir() == installed

    def test_installed_data_file_is_the_fallback(self, tmp_path, monkeypatch) -> None:
        from app import settings as settings_module

        monkeypatch.delenv("CM_CONFIG_FILE", raising=False)
        monkeypatch.setattr(settings_module, "CONFIG_DIR", tmp_path / "missing")
        monkeypatch.setattr(settings_module.sys, "prefix", str(tmp_path / "prefix"))
        installed = tmp_path / "prefix" / "config" / "application.yml"
        installed.parent.mkdir(parents=True)
        installed.write_text("server:\n  port: 1234\n", encoding="utf-8")

        assert settings_module._yaml_path() == installed

    def test_env_override_wins(self, tmp_path, monkeypatch) -> None:
        from app import settings as settings_module

        explicit = tmp_path / "custom.yml"
        explicit.write_text("server:\n  port: 1\n", encoding="utf-8")
        monkeypatch.setenv("CM_CONFIG_FILE", str(explicit))

        assert settings_module._yaml_path() == explicit


@pytest.fixture(scope="module")
def settings():
    """Fresh settings object (bypasses the process-wide lru_cache)."""
    from app.settings import reset_settings_cache

    reset_settings_cache()
    loaded = get_settings()
    yield loaded
    reset_settings_cache()
