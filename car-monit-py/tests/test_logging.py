"""Logging parity tests.

# Migrated from: ruoyi-admin/src/main/resources/logback.xml
# Migrated from: ruoyi-admin/src/main/resources/application.yml (``logging.level``)

只验证「配置是否被正确应用」，不去断言日志正文 —— 正文由各模块自己的用例覆盖。
"""

from __future__ import annotations

import logging
import sys

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
