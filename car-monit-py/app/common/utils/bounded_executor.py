"""带容量上限的线程池 / bounded thread pool.

Java 的 ``ThreadPoolTaskExecutor`` 是"核心 50 + 队列 1000 + 最大 200"，队列满了
由 ``CallerRunsPolicy`` 在**调用线程**执行任务；``ScheduledThreadPoolExecutor``
虽然用的是无界队列，但同样有明确的线程上限。

Python 的 ``ThreadPoolExecutor`` 队列**无界**，突发提交会把内存顶爆。这里用
:class:`threading.BoundedSemaphore` 给待执行任务计数：拿不到配额时按
``CallerRunsPolicy`` 降级为"调用线程直接跑"，既不会丢任务，也不会无限积压。
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Optional

logger = logging.getLogger("app.common.utils.bounded_executor")


class BoundedThreadPoolExecutor(ThreadPoolExecutor):
    """``ThreadPoolExecutor`` + 有界待执行队列 + ``CallerRunsPolicy``."""

    def __init__(
        self,
        *,
        max_workers: int,
        thread_name_prefix: str,
        queue_capacity: int = 1000,
    ) -> None:
        super().__init__(
            max_workers=max(1, max_workers),
            thread_name_prefix=thread_name_prefix,
        )
        self._permits = threading.BoundedSemaphore(max(1, queue_capacity))
        self.queue_capacity = max(1, queue_capacity)

    def submit(self, fn: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Future:  # type: ignore[override]
        if not self._permits.acquire(blocking=False):
            logger.warning(
                "[线程池] 队列已满(capacity=%s)，%s 改由调用线程执行",
                self.queue_capacity,
                getattr(fn, "__name__", fn),
            )
            return self._run_in_caller(fn, args, kwargs)
        try:
            return super().submit(self._release_when_done(fn), *args, **kwargs)
        except RuntimeError:
            # 池已 shutdown：把配额还回去，异常语义与 ThreadPoolExecutor 一致。
            self._permits.release()
            raise

    def _release_when_done(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            finally:
                self._permits.release()

        return _wrapped

    @staticmethod
    def _run_in_caller(fn: Callable[..., Any], args: tuple, kwargs: dict) -> Future:
        """``CallerRunsPolicy``：在调用线程执行，并返回一个已完成的 Future."""
        future: Future = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except Exception as exc:  # noqa: BLE001 - 与 Future 语义一致：异常记录在结果里
            future.set_exception(exc)
        return future


def default_queue_capacity() -> Optional[int]:
    """读取 ``app.executor_queue_capacity``（测试里允许配置缺失）。"""
    try:
        from app.settings import get_settings

        return max(1, int(get_settings().app.executor_queue_capacity))
    except Exception:  # pragma: no cover - 仅防御性回退
        return None


__all__ = ["BoundedThreadPoolExecutor", "default_queue_capacity"]
