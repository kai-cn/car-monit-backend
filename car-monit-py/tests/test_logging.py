"""Logging parity tests.

# Migrated from: ruoyi-admin/src/main/resources/logback.xml
# Migrated from: ruoyi-admin/src/main/resources/application.yml (``logging.level``)

只验证「配置是否被正确应用」，不去断言日志正文 —— 正文由各模块自己的用例覆盖。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

from app.common.core.context.trace_context import remove_trace_id, set_trace_id
from app.logging_config import MilliSecondFormatter, TraceIdFilter, configure_logging, reset_logging
from app.settings import get_settings, reset_settings_cache


@pytest.fixture(scope="module", autouse=True)
def _configured_logging():
    reset_settings_cache()
    reset_logging()
    configure_logging(get_settings())
    yield
    reset_logging()


class TestLoggerLevels:
    """Java: logback.xml 的 ``<logger>`` + application.yml 的 ``logging.level``。"""

    def test_com_ruoyi_is_debug(self) -> None:
        # Java: logging.level.com.ruoyi: debug 覆盖 logback 的 info
        assert logging.getLogger("app").level == logging.DEBUG

    def test_org_springframework_is_warn(self) -> None:
        assert logging.getLogger("uvicorn").level == logging.WARNING
        assert logging.getLogger("fastapi").level == logging.WARNING

    def test_sqlalchemy_engine_echo_suppressed(self) -> None:
        """SQLAlchemy 的 engine echo 会打印方言探测语句，Java 侧不存在这种输出。

        每条语句的输出由 ``app.config.database`` 的监听器（p6spy 等价）负责。
        """
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING
        assert logging.getLogger("sqlalchemy.pool").level == logging.WARNING

    def test_uvicorn_handlers_cleared_so_output_is_unified(self) -> None:
        """uvicorn 自带 handler 会绕过 logback 风格格式，必须清空并 propagate。"""
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            logger = logging.getLogger(name)
            assert logger.handlers == []
            assert logger.propagate is True


class TestLevelFilter:
    """Java ``LevelFilter`` 是精确匹配单一级别，不是"该级别及以上"。"""

    def test_accepts_only_configured_level(self) -> None:
        from app.logging_config import _LevelFilter

        level_filter = _LevelFilter(logging.INFO)

        def record(level: int) -> logging.LogRecord:
            return logging.LogRecord("x", level, __file__, 1, "msg", None, None)

        assert level_filter.filter(record(logging.INFO)) is True
        for level in (logging.DEBUG, logging.WARNING, logging.ERROR):
            assert level_filter.filter(record(level)) is False


class TestSlowLogIsolation:
    """Java: ``TraceIdFilter`` / ``SqlLogInterceptor`` 的 ``additivity="false"``。"""

    def test_trace_logger_only_feeds_slow_file(self) -> None:
        trace_logger = logging.getLogger("app.middleware.trace_id")
        assert trace_logger.propagate is False
        assert len(trace_logger.handlers) == 1
        assert trace_logger.handlers[0].baseFilename.endswith("sys-slow.log")  # type: ignore[attr-defined]


class TestLogCapacity:
    """容量保护：单文件阈值 / 保留份数可配，目录总量按最旧优先清理。"""

    def test_rotating_handlers_use_configured_caps(self) -> None:
        from app.logging_config import _CappedRotatingFileHandler
        from app.settings import get_settings

        settings = get_settings()
        handlers = [h for h in logging.getLogger().handlers if isinstance(h, _CappedRotatingFileHandler)]
        assert len(handlers) == 2  # root: sys-info + sys-error
        for handler in handlers:
            assert handler.maxBytes == settings.logging.file_max_bytes
            assert handler.backupCount == settings.logging.file_backup_count
            assert handler.max_total_bytes == settings.logging.file_max_total_bytes

    def test_rollover_prune_never_deletes_active_log_files(self, tmp_path) -> None:
        """目录预算清理必须保护四个活动文件（P1-9 回归）。"""

        from app.logging_config import _ACTIVE_LOG_FILES, _CappedRotatingFileHandler

        for name in _ACTIVE_LOG_FILES:
            (tmp_path / name).write_bytes(b"x" * 100)
        old_rotated = tmp_path / "sys-info.log.20260101"
        old_rotated.write_bytes(b"x" * 100)

        handler = _CappedRotatingFileHandler(
            filename=tmp_path / "sys-info.log",
            maxBytes=1,
            backupCount=10,
            max_total_bytes=100,
            encoding="utf-8",
        )
        try:
            handler.doRollover()
        finally:
            handler.close()

        for name in _ACTIVE_LOG_FILES:
            assert (tmp_path / name).exists()
        assert not old_rotated.exists()

    def test_handler_stops_after_three_write_failures(self, tmp_path, monkeypatch) -> None:
        """CPython 3.12 不检查 ``Handler.disabled``，必须靠自有标志停用（回归）。"""
        import logging.handlers

        from app.logging_config import _CappedRotatingFileHandler

        handler = _CappedRotatingFileHandler(
            filename=tmp_path / "failed.log",
            maxBytes=1024,
            backupCount=0,
            max_total_bytes=0,
            encoding="utf-8",
        )
        handler.stream.close()  # 模拟磁盘/权限故障：后续写入抛 ValueError
        record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)

        for _ in range(3):
            handler.emit(record)
        assert handler._stopped is True

        calls: list = []
        monkeypatch.setattr(
            logging.handlers.RotatingFileHandler,
            "emit",
            lambda self, item: calls.append(item),
        )
        handler.emit(record)
        assert calls == []
        # 模拟故障时 stream 已被关闭；先摘掉引用再 close，避免 close() 里的 flush 抛错。
        handler.stream = None
        handler.close()

    def test_prune_drops_oldest_files_until_within_budget(self, tmp_path) -> None:
        import os

        from app.logging_config import _prune_logs

        old = tmp_path / "old.log"
        newer = tmp_path / "newer.log"
        current = tmp_path / "sys-info.log"
        for path in (old, newer, current):
            path.write_bytes(b"x" * 100)
        os.utime(old, (1, 1))
        os.utime(newer, (2, 2))

        freed = _prune_logs(tmp_path, 100, protect={str(current)})

        assert freed == 200
        assert not old.exists()
        assert not newer.exists()
        assert current.exists()


class TestLogDirectory:
    """非 editable 安装不能把日志写进 site-packages（P2-7）."""

    def test_log_path_override_wins(self, tmp_path, monkeypatch) -> None:
        from app.logging_config import _log_dir

        target = tmp_path / "custom-logs"
        monkeypatch.setenv("LOG_PATH", str(target))

        assert _log_dir() == target
        assert target.is_dir()

    def test_source_tree_keeps_the_project_logs_directory(self, monkeypatch) -> None:
        from app.logging_config import PROJECT_ROOT, _log_dir

        monkeypatch.delenv("LOG_PATH", raising=False)
        assert (PROJECT_ROOT / "pyproject.toml").is_file()

        assert _log_dir() == PROJECT_ROOT / "logs"

    def test_wheel_install_uses_prefix_instead_of_site_packages(
        self, tmp_path, monkeypatch
    ) -> None:
        from app import logging_config

        source = tmp_path / "site-packages"
        source.mkdir()  # 没有 pyproject.toml -> 视为安装目录
        monkeypatch.delenv("LOG_PATH", raising=False)
        monkeypatch.setattr(logging_config, "PROJECT_ROOT", source)
        monkeypatch.setattr(logging_config.sys, "prefix", str(tmp_path / "prefix"))

        assert logging_config._log_dir() == (
            tmp_path / "prefix" / "var" / "log" / "car-monit"
        )
        # 不再往 site-packages 写入
        assert not (source / "logs").exists()

    def test_readonly_prefix_falls_back_to_the_user_directory(
        self, tmp_path, monkeypatch
    ) -> None:
        from app import logging_config

        source = tmp_path / "site-packages"
        source.mkdir()
        # 把 prefix 候选路径做成普通文件：mkdir 抛 FileExistsError（OSError 子类）
        blocked = tmp_path / "prefix" / "var" / "log" / "car-monit"
        blocked.parent.mkdir(parents=True)
        blocked.write_text("not a directory", encoding="utf-8")

        monkeypatch.delenv("LOG_PATH", raising=False)
        monkeypatch.setattr(logging_config, "PROJECT_ROOT", source)
        monkeypatch.setattr(logging_config.sys, "prefix", str(tmp_path / "prefix"))
        home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

        assert logging_config._log_dir() == home / ".car-monit" / "logs"


class TestTraceIdFilter:
    """Java: ``%X{traceId}`` MDC 占位符。"""

    def test_injects_trace_id_into_record(self) -> None:
        set_trace_id("abc123")
        try:
            record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)
            TraceIdFilter().filter(record)
            assert record.trace_id == "abc123"
        finally:
            remove_trace_id()

    def test_uses_dash_when_no_trace_id(self) -> None:
        remove_trace_id()
        record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)
        TraceIdFilter().filter(record)
        assert record.trace_id == "-"


class TestMilliSecondFormatter:
    """Logback ``%d{HH:mm:ss.SSS}`` —— Python 的 %(asctime)s 没有毫秒指令。"""

    def test_appends_three_digit_millis(self) -> None:
        formatter = MilliSecondFormatter(datefmt="%H:%M:%S")
        record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)
        record.msecs = 42.0
        rendered = formatter.formatTime(record)
        # 形如 "17:56:26.042"
        assert rendered.endswith(".042")
        assert len(rendered.split(".")[-1]) == 3


class TestStdioEncoding:
    """Java: ``PrintStream`` 用平台字符集 + 替换策略，从不抛编码异常。

    回归用例：stdout 被重定向时中文 Windows 用 GBK，打印启动横幅的 ``♥`` /
    ``ლ`` 曾抛 ``UnicodeEncodeError`` 导致进程启动失败。
    """

    def test_relax_stdio_encoding_keeps_platform_encoding(self) -> None:
        from app.main import _relax_stdio_encoding

        before = sys.stdout.encoding
        _relax_stdio_encoding()
        # 断言「没有把 encoding 改成 UTF-8」—— 否则 GBK 控制台会乱码
        assert sys.stdout.encoding == before

    def test_replace_strategy_allows_unmappable_chars(self) -> None:
        """用 GBK 流复现事故场景：``errors="replace"`` 后不可编码字符退化为 ``?``。"""
        import io

        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="gbk", errors="strict")
        # 修复前：直接抛 UnicodeEncodeError -> 进程启动失败
        with pytest.raises(UnicodeEncodeError):
            stream.write("♥")

        stream.reconfigure(errors="replace")
        stream.write("♥")
        stream.flush()
        assert buffer.getvalue() == b"?"
