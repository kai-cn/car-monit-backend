"""Asynchronous task manager.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/manager/AsyncManager.java

Java original
-------------
A singleton holding the Spring bean ``scheduledExecutorService`` -- a
``ScheduledThreadPoolExecutor`` with ``corePoolSize = 50``, daemon threads named
``schedule-pool-N`` and a ``CallerRunsPolicy`` rejection handler. ``execute`` schedules the
task **10 ms in the future**, so the caller returns before the work starts.

Python equivalent
-----------------
``ThreadPoolExecutor(max_workers=50, thread_name_prefix="schedule-pool")``.

Deviations, all of them harmless:
* ``ThreadPoolExecutor`` has an unbounded queue, so ``CallerRunsPolicy`` has no counterpart --
  the pool never rejects. Java only hits that branch when 50 threads plus the queue (also
  unbounded) are saturated, which cannot happen either.
* The 10 ms delay is dropped. It exists in Java to let the HTTP response be flushed first;
  here the task is submitted to another thread, which achieves the same thing without
  adding a timer wheel. The delay is kept as a documented constant.

Why a background thread at all? The audit inserts must never fail the request that triggered
them, and a login must not pay for an extra round-trip to ``sys_logininfor``. ``AsyncManager``
is the only reason ``SysLogininforMapper`` gets a connection of its own.
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

logger = logging.getLogger("app.framework.manager.async_manager")


class AsyncManager:
    """Java: ``AsyncManager`` -- 异步任务管理器."""

    #: Java: ``private final int OPERATE_DELAY_TIME = 10;`` (ms). Not used; see module docstring.
    OPERATE_DELAY_TIME = 10

    #: Java: ``ThreadPoolConfig.scheduledExecutorService`` -> ``new ScheduledThreadPoolExecutor(50, ...)``
    CORE_POOL_SIZE = 50

    _instance: Optional["AsyncManager"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=self.CORE_POOL_SIZE,
            thread_name_prefix="schedule-pool",
        )

    # Java: public static AsyncManager me()
    @classmethod
    def me(cls) -> "AsyncManager":
        """Java: ``me()`` -- the process-wide singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # Java: public void execute(TimerTask task)
    def execute(self, task: Callable[[], None]) -> None:
        """Hand a zero-argument callable to the pool and return immediately.

        Java passes a ``TimerTask``; a plain callable is the Python equivalent. Exceptions are
        logged and swallowed -- in Java they escape into the executor's uncaught-exception
        handler, which logs them and keeps the pool alive. An audit insert failing must never
        take the application down.
        """
        self._executor.submit(self._run_safely, task)

    @staticmethod
    def _run_safely(task: Callable[[], None]) -> None:
        try:
            task()
        except Exception:  # noqa: BLE001 - async audit writes must not propagate
            logger.exception("[异步任务] 执行失败")

    # Java: public void shutdown()
    def shutdown(self) -> None:
        """Java: ``Threads.shutdownAndAwaitTermination(executor)``."""
        self._executor.shutdown(wait=True)


def reset_async_manager() -> None:
    """Test helper: shut the singleton down so a fresh pool is built on next use."""
    global _instance  # noqa: PLW0603 - mirrors the Java static field
    if AsyncManager._instance is not None:
        AsyncManager._instance.shutdown()
    AsyncManager._instance = None


__all__ = ["AsyncManager", "reset_async_manager"]
