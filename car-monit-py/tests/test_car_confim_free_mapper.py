"""``CarConfimFreeMapper`` 的 ``find_in_set`` 语义（P2-1）.

Java 的 ``selectOrgId`` 写成 ``find_in_set(except_ids, #{id})`` —— 参数方向反了。
本工程单行路径与批量路径统一为``find_in_set(:id, except_ids)``，这里同时锁定
SQL 文本与批量路径的 Python 切分语义，防止两条路径再次漂移。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.manager.mapper.car_confim_free_mapper import CarConfimFreeMapper


class _Result:
    def __init__(self, rows: Optional[Sequence[Any]] = None) -> None:
        self._rows = list(rows or [])

    def all(self) -> List[Any]:
        return list(self._rows)

    def first(self) -> Any:
        return self._rows[0] if self._rows else None

    def keys(self) -> List[str]:
        return []


class _RecordingSession:
    def __init__(self, result: _Result) -> None:
        self._result = result
        self.statements: List[str] = []
        self.params: List[Dict[str, Any]] = []

    def execute(self, statement: Any, params: Optional[Dict[str, Any]] = None) -> _Result:
        self.statements.append(" ".join(str(statement).split()))
        self.params.append(dict(params or {}))
        return self._result


class _SessionScope:
    def __init__(self, session: _RecordingSession) -> None:
        self._session = session

    def __enter__(self) -> _RecordingSession:
        return self._session

    def __exit__(self, *_exc: Any) -> bool:
        return False


class _SessionFactory:
    def __init__(self, *results: _Result) -> None:
        self._results = list(results)
        self.sessions: List[_RecordingSession] = []

    def __call__(self) -> _SessionScope:
        session = _RecordingSession(self._results.pop(0))
        self.sessions.append(session)
        return _SessionScope(session)

    @property
    def statements(self) -> List[str]:
        return [statement for session in self.sessions for statement in session.statements]

    @property
    def params(self) -> List[Dict[str, Any]]:
        return [params for session in self.sessions for params in session.params]


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.manager.mapper import car_confim_free_mapper

    monkeypatch.setattr(car_confim_free_mapper, "session_scope", factory)


def test_select_org_id_puts_the_id_on_the_left_side(monkeypatch: pytest.MonkeyPatch) -> None:
    """单行路径必须``find_in_set(:id, except_ids)``，不能照抄 Java 的反向参数."""
    factory = _SessionFactory(_Result(rows=[("ORG-1",)]))
    _patch(monkeypatch, factory)

    assert CarConfimFreeMapper().select_org_id("C1", "E1") == "ORG-1"
    assert "find_in_set(:id, except_ids) > 0" in factory.statements[0]
    assert "find_in_set(except_ids, :id)" not in factory.statements[0]
    assert factory.params[0] == {"carId": "C1", "id": "E1"}


def test_select_org_id_returns_none_without_a_match(monkeypatch: pytest.MonkeyPatch) -> None:
    factory = _SessionFactory(_Result(rows=[]))
    _patch(monkeypatch, factory)

    assert CarConfimFreeMapper().select_org_id("C1", "E1") is None


def test_select_org_ids_treats_except_ids_as_a_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """批量路径与单行路径同一口径：拆逗号后逐项匹配，整串不作为 id."""
    factory = _SessionFactory(_Result(rows=[("C1", "E1,E2", "ORG-1")]))
    _patch(monkeypatch, factory)
    pairs = [("C1", "E1"), ("C1", "E1,E2"), ("C1", "E3"), ("C2", "E9")]

    result = CarConfimFreeMapper().select_org_ids(pairs)

    assert result == {
        ("C1", "E1"): "ORG-1",
        ("C1", "E1,E2"): None,
        ("C1", "E3"): None,
        ("C2", "E9"): None,
    }
    assert "from car_confim_free where car_id in " in factory.statements[0]
    assert factory.params[0] == {"carIds": ["C1", "C2"]}


def test_select_org_ids_skips_the_query_when_car_id_is_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = _SessionFactory()
    _patch(monkeypatch, factory)

    assert CarConfimFreeMapper().select_org_ids([("", "E1")]) == {("", "E1"): None}
    assert factory.statements == []


def test_select_by_except_ids_keeps_the_forward_direction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``<foreach>`` 拼出来的 OR 条件同样是"在列里找 id"."""
    factory = _SessionFactory(_Result(rows=[]))
    _patch(monkeypatch, factory)

    assert CarConfimFreeMapper().select_by_except_ids(["E1", "E2"]) == []
    assert factory.statements[0].count("find_in_set(:id0, t.except_ids) > 0") == 1
    assert factory.statements[0].count("find_in_set(:id1, t.except_ids) > 0") == 1
    assert factory.params[0] == {"id0": "E1", "id1": "E2"}
