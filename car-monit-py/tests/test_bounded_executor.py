"""``BoundedThreadPoolExecutor`` 的 CallerRunsPolicy 行为（P2-15）."""

from __future__ import annotations

import threading
from contextvars import ContextVar

from app.common.utils.bounded_executor import BoundedThreadPoolExecutor
from app.framework.manager.async_manager import AsyncManager


def test_caller_runs_when_the_queue_is_full() -> None:
    executor = BoundedThreadPoolExecutor(
        max_workers=1, thread_name_prefix="bounded-test", queue_capacity=1
    )
    started = threading.Event()
    release = threading.Event()

    def blocking() -> None:
        started.set()
        release.wait(2)

    executor.submit(blocking)
    assert started.wait(2)

    # 第二个任务占住唯一的队列配额（worker 被 blocking 占着）
    executor.submit(lambda: None)

    caller_thread = threading.get_ident()
    seen: dict = {}

    def caller() -> str:
        seen["thread"] = threading.get_ident()
        return "caller"

    third = executor.submit(caller)

    assert third.result() == "caller"
    assert seen["thread"] == caller_thread

    release.set()
    executor.shutdown(wait=True)


def _fill_queue(executor: BoundedThreadPoolExecutor) -> tuple[threading.Event, threading.Event]:
    """占满 worker + 唯一队列配额，使下一次 ``submit`` 落到 CallerRuns."""
    started = threading.Event()
    release = threading.Event()

    def blocking() -> None:
        started.set()
        release.wait(2)

    executor.submit(blocking)
    assert started.wait(2)
    executor.submit(lambda: None)
    return started, release


def test_caller_runs_isolated_uses_empty_context() -> None:
    """``caller_runs_isolated=True``：任务看不到调用方的 ContextVar."""
    probe: ContextVar[str] = ContextVar("probe", default="unset")
    executor = BoundedThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="bounded-isolated",
        queue_capacity=1,
        caller_runs_isolated=True,
    )
    release = _fill_queue(executor)[1]

    token = probe.set("caller-value")
    try:
        third = executor.submit(probe.get)
        assert third.result() == "unset"
    finally:
        probe.reset(token)
        release.set()
        executor.shutdown(wait=True)


def test_caller_runs_without_isolation_inherits_context() -> None:
    """默认 ``caller_runs_isolated=False``：与 Java 一致，沿用调用线程上下文."""
    probe: ContextVar[str] = ContextVar("probe", default="unset")
    executor = BoundedThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="bounded-inherit",
        queue_capacity=1,
    )
    release = _fill_queue(executor)[1]

    token = probe.set("caller-value")
    try:
        third = executor.submit(probe.get)
        assert third.result() == "caller-value"
    finally:
        probe.reset(token)
        release.set()
        executor.shutdown(wait=True)


def test_async_manager_uses_isolated_caller_runs() -> None:
    """审计/登录日志的回退执行不能继承调用方事务/安全上下文."""
    manager = AsyncManager(queue_capacity=1)
    try:
        assert manager._executor._caller_runs_isolated is True
    finally:
        manager.shutdown()
