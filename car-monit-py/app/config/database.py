"""Database engine and transactional session helper.

# Migrated from: ruoyi-admin/src/main/resources/application-druid.yml
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/DruidConfig.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/datasource/DynamicDataSource.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/common/core/monitor/SqlLogInterceptor.java

Java original
-------------
* Druid pool: ``initialSize=5``, ``minIdle=10``, ``maxActive=200``, ``maxWait=60000``,
  ``validationQuery=SELECT 1 FROM DUAL``, ``testWhileIdle=true``.
* ``DynamicDataSource`` switches between master/slave via ``@DataSource``; the slave is
  ``enabled: false``, so every statement resolves to master.
* ``p6spy`` wraps the JDBC driver purely to log SQL; ``Druid.stat.filter`` flags statements
  slower than ``slow-sql-millis: 1000``.

Python equivalent
-----------------
* ``create_engine`` + ``QueuePool`` with the same pool sizes.
* No ``DynamicDataSource``: the slave is disabled, so a single engine is behaviourally
  identical (documented in ``COMPATIBILITY.md``).
* ``event.listen(before/after_cursor_execute)`` replaces p6spy and the Druid stat filter;
  slow statements are logged at WARNING with the ``monitor.slow_sql_threshold`` value.

Transaction semantics
---------------------
Java's ``@Transactional(rollbackFor = Exception.class)`` rolls back for every exception.
:func:`session_scope` does the same: commit on success, rollback on any exception.
This is the closest possible match because Python has no checked exceptions.

Engine creation is lazy: importing this module never opens a socket, so the service can
boot (and ``/health`` can report ``DOWN``) while MySQL is unreachable.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.settings import AppSettings, get_settings

logger = logging.getLogger("app.config.database")

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def _create_engine(settings: AppSettings) -> Engine:
    """Build the SQLAlchemy engine from ``spring.datasource.druid``."""
    druid = settings.spring.datasource.druid
    engine = create_engine(
        settings.database_url,
        # Java: connectTimeout / socketTimeout from the JDBC URL and Druid block.
        connect_args=settings.database_connect_args,
        # Druid: minIdle=10 / maxActive=200 -> pool_size + max_overflow == 200
        pool_size=druid.min_idle,
        max_overflow=max(0, druid.max_active - druid.min_idle),
        # Druid: maxWait=60000 (ms) -> pool_timeout in seconds
        pool_timeout=max(1, druid.max_wait // 1000),
        # Druid: minEvictableIdleTimeMillis=300000 -> recycle after 300s
        pool_recycle=300,
        # Druid: testWhileIdle=true / validationQuery
        pool_pre_ping=True,
        future=True,
    )
    _register_slow_sql_listener(engine, settings.monitor.slow_sql_threshold)
    logger.debug("SQLAlchemy engine created (pool_size=%s, max_overflow=%s)", druid.min_idle, druid.max_active - druid.min_idle)
    return engine


def _register_slow_sql_listener(engine: Engine, threshold_ms: int) -> None:
    """Log every statement (p6spy) and warn on slow ones (Druid stat filter).

    Java 原语义
        ``spy.properties`` 使用 ``appender=StdoutLogger``，p6spy 把**每一条** statement
        打到 stdout，格式为 ``Consume Time: xx ms`` + ``Execute SQL: ...``；
        ``filter.stat.slow-sql-millis: 1000`` 另外把慢 SQL 交给 Druid 统计。

    Python 等价实现
        在 ``after_cursor_execute`` 中统一计时：每条语句打一条 DEBUG（因为
        ``logging.level.com.ruoyi: debug``，默认可见，等价于 p6spy 的 stdout），
        超过 ``monitor.slow-sql-threshold`` 再额外打一条 WARNING。
    """

    @event.listens_for(engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        conn.info.setdefault("_query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        stack = conn.info.get("_query_start_time") or []
        if not stack:
            return
        elapsed_ms = (time.perf_counter() - stack.pop()) * 1000.0
        # Java: p6spy StdoutLogger -- 每条语句都输出
        logger.debug(
            "[SQL] 耗时=%.0fms | %s | params=%s",
            elapsed_ms,
            " ".join(statement.split()),
            parameters,
        )
        if elapsed_ms >= threshold_ms:
            # Mirror the Java warning line so log parsers keep working.
            logger.warning(
                "[慢SQL告警] 耗时=%.0fms, 阈值=%sms, SQL=%s",
                elapsed_ms,
                threshold_ms,
                " ".join(statement.split()),
            )


def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = _create_engine(get_settings())
    return _engine


def get_session_factory() -> sessionmaker:
    """Return the process-wide ``sessionmaker``."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _session_factory


def new_session() -> Session:
    """Create a session that the caller must close (Java: an injected ``SqlSession``)."""
    return get_session_factory()()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope.

    Equivalent to Java::

        @Transactional(rollbackFor = Exception.class)
        public void doSomething() { ... }

    Usage::

        with session_scope() as session:
            session.execute(text("UPDATE sys_user SET ..."))

    Note: this is the Python equivalent of try-with-resources *and* declarative
    transaction demarcation combined -- the session is closed and the transaction is
    committed/rolled back on exit.
    """
    session = new_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection() -> bool:
    """Liveness probe used by ``GET /health``; never raises."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001 - probe must not raise
        logger.warning("[健康检查] 数据库连接失败: %s", exc)
        return False


def dispose_engine() -> None:
    """Release pooled connections (called from the FastAPI shutdown hook)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        logger.info("[数据源] 连接池已释放")
    _engine = None
    _session_factory = None
