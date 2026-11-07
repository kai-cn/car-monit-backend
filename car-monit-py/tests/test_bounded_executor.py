"""``BoundedThreadPoolExecutor`` 的 CallerRunsPolicy 行为（P2-15）."""

from __future__ import annotations

import threading

from app.common.utils.bounded_executor import BoundedThreadPoolExecutor


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
