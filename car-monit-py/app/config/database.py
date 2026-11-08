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
:func:`session_scope` does the same for a **single** statement: commit on success, rollback
on any exception. This is the closest possible match because Python has no checked
exceptions.

:func:`transactional` adds the **method-level** boundary that Java's annotation provides:
the first ``session_scope()`` executed inside the decorated method opens the session, every
nested ``session_scope()`` call (including calls made by mapper methods) joins it with
``REQUIRED`` semantics, and the outermost decorated method commits once — or rolls back
once if an exception escapes. A nested decorated participant that throws also marks the
outer transaction rollback-only, so catching the exception in the caller still fails the
outer commit with :class:`UnexpectedRollbackException` (Spring's behaviour). This is what
makes ``SysUserService.update_user`` (delete role/post links + update the user row) atomic.

The session is created **lazily** on the first ``session_scope()`` inside the method, so a
decorated method that never touches the database does not open a connection. This mirrors
Spring's lazy connection acquisition closely enough while keeping fake-mapper unit tests
offline.

Engine creation is lazy: importing this module never opens a socket, so the service can
boot (and ``/health`` can report ``DOWN``) while MySQL is unreachable.
"""

from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Iterator, Optional, TypeVar, cast

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.settings import AppSettings, get_settings

logger = logging.getLogger("app.config.database")

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None

#: Java: ``TransactionSynchronizationManager`` 的“当前线程是否已有事务”判断。
#: 用 ``ContextVar`` 而不是 ``threading.local``：端点在线程池里执行，anyio 会把
#: 当前请求的 context 复制进工作线程，嵌套调用与 ``asyncio`` 场景都能正确传播。
_TRANSACTION: ContextVar[Optional["_TransactionState"]] = ContextVar(
    "app_transaction_state", default=None
)

F = TypeVar("F", bound=Callable[..., Any])


class _TransactionState:
    """One ``@Transactional`` invocation's shared state.

    ``session`` is ``None`` until the first ``session_scope()`` inside the method, so a
    decorated method that only computes values never touches the pool. ``rollback_only``
    mirrors Spring's ``setRollbackOnly``: a nested ``REQUIRED`` participant that throws
    marks the outer transaction, and the outer commit then fails with
    :class:`UnexpectedRollbackException`.
    """

    __slots__ = ("session", "rollback_only")

    def __init__(self) -> None:
        self.session: Optional[Session] = None
        self.rollback_only = False


class UnexpectedRollbackException(RuntimeError):
    """Java: ``org.springframework.transaction.UnexpectedRollbackException``."""


_ROLLBACK_ONLY_MESSAGE = "Transaction rolled back because it has been marked as rollback-only"


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

    Two modes:

    * **no ``@transactional`` boundary** — the historical behaviour: each call opens,
      commits/rolls back and closes its own session (one transaction per statement).
    * **inside ``@transactional``** — joins the method-level transaction: the first call
      opens the session, subsequent calls reuse it, and the decorator is the only one that
      commits/rolls back/closes (``REQUIRED`` semantics, like Spring).
    """
    state = _TRANSACTION.get()
    if state is not None:
        if state.session is None:
            state.session = new_session()
        # Java: PROPAGATION_REQUIRED -> 加入外层事务，不提交、不回滚、不关闭。
        yield state.session
        return

    # 最外层（没有 @transactional）: 保持“一条语句一个事务”的既有语义。
    session = new_session()
    token = _TRANSACTION.set(_TransactionState())
    state = _TRANSACTION.get()
    assert state is not None
    state.session = session
    try:
        yield session
        if state.rollback_only:
            # rollback 由下面的 except 统一执行，避免同一事务 rollback 两次。
            raise UnexpectedRollbackException(_ROLLBACK_ONLY_MESSAGE)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        _TRANSACTION.reset(token)
        session.close()


def transactional(func: F) -> F:
    """``@Transactional(rollbackFor = Exception.class)`` 的方法级装饰器.

    Java 的注解由 Spring 的 ``MethodSecurityInterceptor``/事务代理在**方法调用前**开启
    事务、方法正常返回后提交、异常逃逸后回滚。这里用 ``ContextVar`` 复刻同一个边界：

    * 外层方法第一次 ``session_scope()`` 时创建 Session；
    * 内层方法（无论是否也被 ``@transactional`` 装饰）调用 ``session_scope()`` 都加入
      同一个 Session，不重复提交（``PROPAGATION_REQUIRED``）；
    * 内层**装饰**方法抛异常时把外层事务标记为 rollback-only；即使调用方 catch 住，
      外层也会以 :class:`UnexpectedRollbackException` 失败（Spring 的 REQUIRED 行为）；
    * 异常从**最外层**装饰方法逃逸时统一回滚，已提交的嵌套方法不会单独回滚；
    * 方法体没有访问数据库时不创建 Session，避免给纯计算/纯转发方法增加连接开销。

    与 Spring 的已知差异：Spring 在方法进入时就获取连接（DataSourceTransactionManager），
    这里延迟到第一条 SQL；对锁的持有时间只会更短，不会更长。
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        state = _TRANSACTION.get()
        if state is not None:
            # Java: PROPAGATION_REQUIRED -> 加入外层事务。嵌套参与者抛异常时把外层
            # 事务标记为 rollback-only；调用方即使 catch 住，外层 commit 也会失败。
            try:
                return func(*args, **kwargs)
            except Exception:
                state.rollback_only = True
                raise

        token = _TRANSACTION.set(_TransactionState())
        state = _TRANSACTION.get()
        assert state is not None
        try:
            result = func(*args, **kwargs)
        except Exception:
            if state.session is not None:
                state.session.rollback()
            raise
        else:
            if state.rollback_only:
                if state.session is not None:
                    state.session.rollback()
                raise UnexpectedRollbackException(_ROLLBACK_ONLY_MESSAGE)
            if state.session is not None:
                try:
                    state.session.commit()
                except Exception:
                    state.session.rollback()
                    raise
            return result
        finally:
            if state.session is not None:
                state.session.close()
            _TRANSACTION.reset(token)

    return cast(F, wrapper)


def is_transaction_active() -> bool:
    """Java: ``TransactionSynchronizationManager.isActualTransactionActive()``.

    仅供测试与诊断使用；业务代码不应依赖它来分支。
    """
    return _TRANSACTION.get() is not None


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
