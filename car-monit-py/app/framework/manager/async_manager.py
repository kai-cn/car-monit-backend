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

Deviations:
* 队列现在**有界**（``app.executor_queue_capacity``，默认 1000）。Java 的
  ``ScheduledThreadPoolExecutor`` 用无界 ``DelayedWorkQueue``，突发审计写入会把内存顶爆；
  这里改用 :class:`~app.common.utils.bounded_executor.BoundedThreadPoolExecutor`，
  队列满时按 ``CallerRunsPolicy`` 在调用线程执行（不丢任务、不无限积压）。
* The 10 ms delay is dropped. It exists in Java to let the HTTP response be flushed first;
  here the task is submitted to another thread, which achieves the same thing without
  adding a timer wheel. The delay is kept as a documented constant.
* ``shutdown`` 不再像 Java ``Threads.shutdownAndAwaitTermination`` 那样等 120 秒：
  ``shutdown(wait=False)`` 后只做有界等待（默认 5 秒），超时记 WARNING 返回，
  避免审计写入把进程退出/uvicorn 停止拖住。

Why a background thread at all? The audit inserts must never fail the request that triggered
them, and a login must not pay for an extra round-trip to ``sys_logininfor``. ``AsyncManager``
is the only reason ``SysLogininforMapper`` gets a connection of its own.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from app.common.utils.bounded_executor import BoundedThreadPoolExecutor, default_queue_capacity

logger = logging.getLogger("app.framework.manager.async_manager")


class AsyncManager:
    """Java: ``AsyncManager`` -- 异步任务管理器."""

    #: Java: ``private final int OPERATE_DELAY_TIME = 10;`` (ms). Not used; see module docstring.
    OPERATE_DELAY_TIME = 10

    #: Java: ``ThreadPoolConfig.scheduledExecutorService`` -> ``new ScheduledThreadPoolExecutor(50, ...)``
    CORE_POOL_SIZE = 50

    #: Java ``Threads.shutdownAndAwaitTermination`` 等 120s 再 ``shutdownNow``；
    #: 进程退出不能被审计写入无限拖住，这里改成有界等待（差异见模块 docstring）。
    SHUTDOWN_TIMEOUT_SECONDS = 5.0

    _instance: Optional["AsyncManager"] = None
    _lock = threading.Lock()

    def __init__(self, queue_capacity: Optional[int] = None) -> None:
        capacity = queue_capacity or default_queue_capacity() or 1000
        self._executor = BoundedThreadPoolExecutor(
            max_workers=self.CORE_POOL_SIZE,
            thread_name_prefix="schedule-pool",
            queue_capacity=capacity,
            # 审计/登录日志属于"脱离请求"的后台写入：队列满时也不能继承调用方的
            # traceId / SecurityContext / 事务 ContextVar，否则会误加入别人的事务。
            caller_runs_isolated=True,
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
    def shutdown(self, timeout: Optional[float] = None) -> None:
        """Java: ``Threads.shutdownAndAwaitTermination(executor)``.

        ``shutdown(wait=False)`` 立即停止接收新任务并返回，然后**有界**等待
        ``schedule-pool`` 线程结束（默认 5s）。Java 等 120s 再 ``shutdownNow``；
        Python 无法中断阻塞中的线程，无限等待会让 uvicorn 停止/解释器退出挂住，
        所以这里到点只记 WARNING 并返回。
        """
        limit = self.SHUTDOWN_TIMEOUT_SECONDS if timeout is None else max(0.0, timeout)
        self._executor.shutdown(wait=False)
        deadline = time.monotonic() + limit
        for thread in list(threading.enumerate()):
            if not thread.name.startswith("schedule-pool") or not thread.is_alive():
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            thread.join(remaining)
        alive = [
            thread.name
            for thread in threading.enumerate()
            if thread.name.startswith("schedule-pool") and thread.is_alive()
        ]
        if alive:
            logger.warning(
                "[异步任务] 关闭等待 %.1fs 后仍有 %d 个线程在执行: %s",
                limit,
                len(alive),
                ", ".join(alive),
            )


def reset_async_manager() -> None:
    """Test helper: shut the singleton down so a fresh pool is built on next use."""
    global _instance  # noqa: PLW0603 - mirrors the Java static field
    if AsyncManager._instance is not None:
        AsyncManager._instance.shutdown()
    AsyncManager._instance = None


__all__ = ["AsyncManager", "reset_async_manager"]
