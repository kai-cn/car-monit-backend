"""Logging bootstrap.

# Migrated from: ruoyi-admin/src/main/resources/logback.xml
# Migrated from: ruoyi-admin/src/main/resources/application.yml (``logging.level``)

Java original
-------------
* Console appender with ``%d{HH:mm:ss.SSS} [%thread] %-5level [%X{traceId}] %logger{20} - %msg%n``
* Rolling file appenders: ``sys-info.log`` (INFO only), ``sys-error.log`` (ERROR only),
  ``sys-slow.log`` (slow request / slow SQL), ``sys-user.log`` (user access),
  time+size based, 100 MB per file, 60 days history, written under ``/home/ruoyi/logs``.
* ``logging.level.com.ruoyi: debug`` overrides the ``info`` level declared in logback.xml
  (Spring Boot applies ``logging.level.*`` after the Logback configuration is loaded).

Python equivalent
-----------------
* One console handler using the same pattern (``traceId`` comes from
  :mod:`app.common.core.context.trace_context` via a :class:`logging.Filter`).
* ``RotatingFileHandler`` for the info / error / slow / user files. Python's rotating
  handler is size-based only, so the 100 MB cap is kept and the 60-day retention becomes
  ``backupCount`` -- documented in ``COMPATIBILITY.md``.
* Java logger names are translated, not invented:

    =============================  ==================
    Java logger                    Python logger
    =============================  ==================
    ``com.ruoyi``                  ``app``
    ``org.springframework``        ``uvicorn``
    ``org.mybatis``                ``sqlalchemy``
    ``com.alibaba.druid``          ``sqlalchemy.pool``
    =============================  ==================
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, List

from app.common.core.context.trace_context import get_trace_id
from app.settings import AppSettings, PROJECT_ROOT

#: Java logger prefix -> Python logger prefix.
JAVA_TO_PY_LOGGER: Dict[str, List[str]] = {
    "com.ruoyi": ["app"],
    "org.springframework": ["uvicorn", "fastapi"],
    "org.mybatis": ["sqlalchemy"],
    "com.alibaba.druid": ["sqlalchemy.pool"],
}

_CONSOLE_PATTERN = "%(asctime)s [%(threadName)s] %(levelname)-5s [%(trace_id)s] %(name)s - %(message)s"
_FILE_PATTERN = "%(asctime)s [%(threadName)s] %(levelname)-5s [%(trace_id)s] %(name)s:%(lineno)d - %(message)s"

_CONFIGURED = False


class TraceIdFilter(logging.Filter):
    """Injects the current trace id into every record (Java: ``%X{traceId}``)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or "-"
        return True


class MilliSecondFormatter(logging.Formatter):
    """``logging`` has no ``%f`` directive; append milliseconds like Logback does."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        import time

        created = time.localtime(record.created)
        base = time.strftime(datefmt or "%Y-%m-%d %H:%M:%S", created)
        return f"{base}.{int(record.msecs):03d}"


class _LevelFilter(logging.Filter):
    """Java ``LevelFilter`` equivalent: accept exactly one level, deny everything else.

    logback 的 ``LevelFilter`` 是**精确匹配**单一级别（``onMatch=ACCEPT`` /
    ``onMismatch=DENY``），不是"该级别及以上"的阈值过滤。``sys-info.log`` 因此只收
    INFO：DEBUG（p6spy 风格的逐条 SQL）不会落盘，WARNING/ERROR 也不会。
    """

    def __init__(self, level: int) -> None:
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self.level


def _log_dir() -> Path:
    """``log.path`` from logback.xml; overridable through ``LOG_PATH``."""
    configured = os.environ.get("LOG_PATH")
    path = Path(configured) if configured else PROJECT_ROOT / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rotating_handler(path: Path, level: int, formatter: logging.Formatter) -> logging.Handler:
    handler = logging.handlers.RotatingFileHandler(
        filename=path,
        maxBytes=100 * 1024 * 1024,  # logback: <maxFileSize>100MB</maxFileSize>
        backupCount=30,  # logback: <maxHistory>60</maxHistory> (days -> rotations)
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(TraceIdFilter())
    return handler


def configure_logging(settings: AppSettings) -> None:
    """Configure the root logger once per process."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_path = _log_dir()
    console_formatter = MilliSecondFormatter(_CONSOLE_PATTERN, datefmt="%H:%M:%S")
    file_formatter = MilliSecondFormatter(_FILE_PATTERN)

    console = logging.StreamHandler()
    console.setFormatter(console_formatter)
    console.addFilter(TraceIdFilter())

    info_file = _rotating_handler(log_path / "sys-info.log", logging.INFO, file_formatter)
    info_file.addFilter(_LevelFilter(logging.INFO))
    error_file = _rotating_handler(log_path / "sys-error.log", logging.ERROR, file_formatter)
    error_file.addFilter(_LevelFilter(logging.ERROR))
    slow_file = _rotating_handler(log_path / "sys-slow.log", logging.INFO, file_formatter)
    user_file = _rotating_handler(log_path / "sys-user.log", logging.INFO, file_formatter)

    root = logging.getLogger()
    root.handlers.clear()
    # logback: <root level="info"> with console + file_info + file_error
    root.setLevel(logging.INFO)
    root.addHandler(console)
    root.addHandler(info_file)
    root.addHandler(error_file)

    # logback: <logger name="com.ruoyi.common.core.monitor.TraceIdFilter" level="info"
    #          additivity="false"><appender-ref ref="file_slow"/></logger>
    # trace 日志**只**进 sys-slow.log：否则每个请求的 [请求完成] 会同时写 info 文件，
    # 日志量翻倍且掩盖真正的 INFO 业务日志。
    trace_logger = logging.getLogger("app.middleware.trace_id")
    trace_logger.addHandler(slow_file)
    trace_logger.propagate = False
    trace_logger.setLevel(logging.INFO)

    # logback: SqlLogInterceptor 同样 additivity="false" 只挂 file_slow。本工程的
    # ``app.config.database`` 还兼任 p6spy 的逐条 SQL 输出（Java 写 stdout），
    # 因此保留向 root 传播，交给 console；DEBUG 已被 info/error 的精确级别过滤挡住。
    logging.getLogger("app.config.database").addHandler(slow_file)

    # logback: <logger name="sys-user" ...> -> user access log
    logging.getLogger("app.user_access").addHandler(user_file)

    # logback.xml hard-codes com.ruoyi=info / org.springframework=warn; application.yml
    # overrides them via logging.level.* -- exactly the precedence implemented here.
    defaults = {"com.ruoyi": "INFO", "org.springframework": "WARN", "org.mybatis": "INFO", "com.alibaba.druid": "WARN"}
    effective: Dict[str, str] = {**defaults, **settings.log_levels()}
    for java_logger, level in effective.items():
        for py_logger in JAVA_TO_PY_LOGGER.get(java_logger, [java_logger]):
            logging.getLogger(py_logger).setLevel(level.upper())

    # SQLAlchemy 的 engine echo 会额外打印方言探测语句（SELECT DATABASE() /
    # SELECT @@sql_mode ...），Java 侧 JDBC 驱动不做这些输出，p6spy 也不打印它们。
    # 真正的「每条语句」输出由 app.config.database 的快照监听器负责（p6spy 等价）。
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # uvicorn installs its own handlers; let them propagate to our root handler instead.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True

    _CONFIGURED = True
    logging.getLogger("app.logging").debug("日志系统初始化完成, 日志目录=%s", log_path)


def reset_logging() -> None:
    """Test helper: allow ``configure_logging`` to run again."""
    global _CONFIGURED
    _CONFIGURED = False
