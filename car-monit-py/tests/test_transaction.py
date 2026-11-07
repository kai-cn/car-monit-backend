"""`@transactional` / `session_scope()` 的事务语义回归用例.

# Migrated from: org.springframework.transaction.annotation.Transactional

覆盖 Java ``@Transactional(rollbackFor = Exception.class)`` 的四条可观察语义：

1. 一次装饰方法内的多条 SQL 共用一个 Session，**只提交一次**；
2. 异常从最外层装饰方法逃逸时**只回滚一次**；
3. 嵌套装饰方法按 ``PROPAGATION_REQUIRED`` 加入外层事务，不单独提交；
4. 方法内部被 catch 的异常**不**触发回滚（与 Spring 一致）；
5. 没有访问数据库的装饰方法不创建 Session / 连接。

用 FakeSession 替代真实 MySQL，保证离线可跑。
"""

from __future__ import annotations

from typing import Any, List

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.base.service.abstract_crud_service import AbstractCrudService
from app.base.service.zdata_trail_tracks_service import ZdataTrailTracksService
from app.config import database
from app.manager.service.manager_service import ManagerCrudService


class _FailingBatchMapper:
    """前 N 条写入成功，第 ``fail_at`` 条抛异常（用来验证批量整体回滚）。"""

    def __init__(self, fail_at: int = 2) -> None:
        self.calls = 0
        self.fail_at = fail_at

    def _touch(self) -> None:
        self.calls += 1
        with database.session_scope():
            if self.calls == self.fail_at:
                raise ValueError("batch boom")

    def insert(self, _entity: Any) -> None:
        self._touch()

    def update_by_id(self, _entity: Any) -> None:
        self._touch()


class FakeSession:
    """只记录 commit/rollback/close 的 Session 替身。"""

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closes += 1


@pytest.fixture()
def sessions(monkeypatch: pytest.MonkeyPatch) -> List[FakeSession]:
    """把 ``new_session`` 换成 FakeSession，并返回创建过的实例列表。"""
    created: List[FakeSession] = []

    def fake_new_session() -> FakeSession:
        session = FakeSession()
        created.append(session)
        return session

    monkeypatch.setattr(database, "new_session", fake_new_session)
    return created


def test_decorated_method_commits_once_and_reuses_the_session(
    sessions: List[FakeSession],
) -> None:
    @database.transactional
    def work() -> Any:
        with database.session_scope() as first:
            pass
        with database.session_scope() as second:
            pass
        return first, second

    first, second = work()

    assert len(sessions) == 1
    assert first is second is sessions[0]
    assert sessions[0].commits == 1
    assert sessions[0].rollbacks == 0
    assert sessions[0].closes == 1


def test_plain_session_scope_still_commits_each_call(
    sessions: List[FakeSession],
) -> None:
    with database.session_scope():
        pass
    with database.session_scope():
        pass

    assert len(sessions) == 2
    assert [item.commits for item in sessions] == [1, 1]
    assert [item.closes for item in sessions] == [1, 1]


def test_exception_escaping_the_decorated_method_rolls_back_once(
    sessions: List[FakeSession],
) -> None:
    @database.transactional
    def work() -> None:
        with database.session_scope():
            raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        work()

    assert len(sessions) == 1
    assert sessions[0].commits == 0
    assert sessions[0].rollbacks == 1
    assert sessions[0].closes == 1


def test_nested_decorated_method_joins_the_outer_transaction(
    sessions: List[FakeSession],
) -> None:
    @database.transactional
    def inner() -> None:
        with database.session_scope():
            pass

    @database.transactional
    def outer() -> None:
        with database.session_scope():
            pass
        inner()
        with database.session_scope():
            pass

    outer()

    assert len(sessions) == 1
    assert sessions[0].commits == 1
    assert sessions[0].rollbacks == 0
    assert sessions[0].closes == 1


def test_caught_exception_does_not_mark_the_transaction_for_rollback(
    sessions: List[FakeSession],
) -> None:
    """Spring 只在异常**逃逸**时回滚；方法内部 catch 后仍正常提交。"""

    @database.transactional
    def work() -> None:
        with database.session_scope():
            pass
        try:
            raise ValueError("caught inside")
        except ValueError:
            pass
        with database.session_scope():
            pass

    work()

    assert len(sessions) == 1
    assert sessions[0].commits == 1
    assert sessions[0].rollbacks == 0


def test_nested_failure_marks_the_outer_transaction_rollback_only(
    sessions: List[FakeSession],
) -> None:
    """REQUIRED 语义：内层抛出、外层 catch，外层 commit 仍须失败（Spring 行为）。"""

    @database.transactional
    def inner() -> None:
        with database.session_scope():
            pass
        raise ValueError("inner failed")

    @database.transactional
    def outer() -> None:
        with database.session_scope():
            pass
        try:
            inner()
        except ValueError:
            pass

    with pytest.raises(database.UnexpectedRollbackException, match="rollback-only"):
        outer()

    assert len(sessions) == 1
    assert sessions[0].commits == 0
    assert sessions[0].rollbacks >= 1
    assert sessions[0].closes == 1


def test_decorated_method_without_sql_does_not_open_a_session(
    sessions: List[FakeSession],
) -> None:
    @database.transactional
    def work() -> str:
        return "no database access"

    assert work() == "no database access"
    assert sessions == []
    assert database.is_transaction_active() is False


def test_real_rollback_discards_both_statements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """用内存 SQLite 验证真正的 commit/rollback，而不是只看 FakeSession 计数。"""
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("create table tx_probe (value integer)"))

    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    monkeypatch.setattr(database, "_session_factory", factory)

    @database.transactional
    def work(fail: bool) -> None:
        with database.session_scope() as session:
            session.execute(text("insert into tx_probe values (1)"))
        with database.session_scope() as session:
            session.execute(text("insert into tx_probe values (2)"))
        if fail:
            raise RuntimeError("boom")

    work(False)
    with engine.connect() as connection:
        assert connection.execute(text("select count(*) from tx_probe")).scalar() == 2

    with pytest.raises(RuntimeError, match="boom"):
        work(True)

    # 第二条 work 的两条 INSERT 都随异常回滚，表里仍只有第一次提交的两行。
    with engine.connect() as connection:
        assert connection.execute(text("select count(*) from tx_probe")).scalar() == 2


@pytest.mark.parametrize(
    "factory",
    [
        lambda mapper: ManagerCrudService(mapper=mapper),
        lambda mapper: AbstractCrudService(mapper=mapper),
        lambda mapper: ZdataTrailTracksService(mapper=mapper),
    ],
)
def test_save_batch_rolls_back_the_whole_batch(
    sessions: List[FakeSession], factory: Any
) -> None:
    """saveBatch 中途失败时不能留下半截数据（manager/base/zdata 三条路径）."""
    with pytest.raises(ValueError, match="batch boom"):
        factory(_FailingBatchMapper(fail_at=2)).save_batch([object(), object()])

    assert len(sessions) == 1
    assert sessions[0].commits == 0
    assert sessions[0].rollbacks == 1


def test_update_batch_by_id_rolls_back_the_whole_batch(
    sessions: List[FakeSession],
) -> None:
    with pytest.raises(ValueError, match="batch boom"):
        ManagerCrudService(mapper=_FailingBatchMapper(fail_at=2)).update_batch_by_id(
            [object(), object()]
        )

    assert len(sessions) == 1
    assert sessions[0].commits == 0
    assert sessions[0].rollbacks == 1
