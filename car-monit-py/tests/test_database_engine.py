"""Engine / sessionmaker 首建并发安全（线程池预热阶段）.

``get_engine`` / ``get_session_factory`` 是懒加载单例；首个请求和 ``/health`` 探针
可能同时触发。没有锁时会各建一个连接池（后者覆盖前者，前者的连接泄漏）。
"""

from __future__ import annotations

import threading
from typing import Any, List

from app.config import database


def _run_concurrently(action, workers: int = 8) -> List[Any]:
    barrier = threading.Barrier(workers)
    results: List[Any] = []

    def worker() -> None:
        barrier.wait()
        results.append(action())

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)
    return results


def test_get_engine_creates_exactly_one_engine(monkeypatch) -> None:
    calls: List[int] = []
    engine = object()

    def fake_create(_settings: Any) -> Any:
        calls.append(1)
        threading.Event().wait(0.02)  # 放大首建窗口
        return engine

    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "_create_engine", fake_create)

    results = _run_concurrently(database.get_engine)

    assert len(calls) == 1
    assert all(result is engine for result in results)


def test_get_session_factory_creates_exactly_one_factory(monkeypatch) -> None:
    calls: List[dict] = []
    engine = object()

    class _FakeMaker:
        def __init__(self, **kwargs: Any) -> None:
            calls.append(kwargs)

    def fake_maker(**kwargs: Any) -> Any:
        threading.Event().wait(0.02)
        return _FakeMaker(**kwargs)

    monkeypatch.setattr(database, "_engine", engine)
    monkeypatch.setattr(database, "_session_factory", None)
    monkeypatch.setattr(database, "sessionmaker", fake_maker)

    results = _run_concurrently(database.get_session_factory)

    assert len(calls) == 1
    assert calls[0]["bind"] is engine
    assert all(result is results[0] for result in results)


def test_dispose_engine_clears_both_singletons(monkeypatch) -> None:
    class _Disposable:
        def __init__(self) -> None:
            self.disposed = 0

        def dispose(self) -> None:
            self.disposed += 1

    engine = _Disposable()
    monkeypatch.setattr(database, "_engine", engine)
    monkeypatch.setattr(database, "_session_factory", object())

    database.dispose_engine()

    assert engine.disposed == 1
    assert database._engine is None
    assert database._session_factory is None
