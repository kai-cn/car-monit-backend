"""``BaseConfigServiceAreaMapper`` / ``BaseConfigServiceAreaService`` —— SQL 与 MP 语义.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/base/BaseConfigServiceAreaMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/base/service/impl/BaseConfigServiceAreaServiceImpl.java

这一层抓的是**改错不会报错、只会悄悄改数据**的地方：

1. 列表 SQL **不带** ``del_flag = '0'``，也**不带** ``order by``；
2. ``createBy`` 的条件是 ``!= null``（传 ``0`` 也生效），其余 7 个是 ``!= null and != ''``；
3. ``insert`` 走 ``ASSIGN_UUID``：主键是 **32 位无连字符小写 hex**，且会回写实体；
4. ``insert`` 的字段策略是 ``NOT_NULL``：值为 ``None`` 的列**不进 SQL**；
5. ``MetaObjectHandler`` 的 ``tenantId`` 被 ``epsId == null`` 守卫（Java 笔误，照抄）；
6. ``updateById`` 的 ``WHERE`` 带 ``del_flag = '0'``（``@TableLogic``）；
7. 两条 ``delete`` 是**物理** ``delete from``（XML 里写的是 ``<update>`` 标签）；
8. ``save`` 的判据是 ``isNotBlank(id)``，且**两种分支的返回体完全一样**。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.base.domain.base_config_service_area import BaseConfigServiceArea
from app.base.mapper import base_config_service_area_mapper as mapper_module
from app.base.mapper import plus_mapper as plus_mapper_module
from app.base.mapper.base_config_service_area_mapper import (
    BaseConfigServiceAreaMapper,
    build_list_sql,
)
from app.base.service.base_config_service_area_service import BaseConfigServiceAreaService
from app.common.core.page.page_helper import clear_page, start_page
from app.common.utils import security_utils as SecurityUtils


# --------------------------------------------------------------------------- fakes


class _Row:
    """One result row: ``_mapping`` + ``first()`` 就够 ``_map_row`` 用了。"""

    def __init__(self, values: Dict[str, Any]) -> None:
        self._mapping = values


class _Result:
    def __init__(
        self,
        rows: Optional[Sequence[Any]] = None,
        scalar_value: Any = None,
        rowcount: int = 0,
    ) -> None:
        self._rows = list(rows or [])
        self._scalar = scalar_value
        self.rowcount = rowcount

    def keys(self) -> List[str]:
        return list(self._rows[0]._mapping.keys()) if self._rows else []

    def all(self) -> List[Any]:
        return list(self._rows)

    def first(self) -> Any:
        return self._rows[0] if self._rows else None

    def scalar(self) -> Any:
        return self._scalar


class _RecordingSession:
    def __init__(self, results: List[_Result]) -> None:
        self._results = list(results)
        self.statements: List[str] = []
        self.params: List[Dict[str, Any]] = []

    def execute(self, statement: Any, params: Optional[Dict[str, Any]] = None) -> _Result:
        self.statements.append(" ".join(str(statement).split()))
        self.params.append(dict(params or {}))
        if not self._results:
            raise AssertionError(f"unexpected extra statement: {statement}")
        return self._results.pop(0)


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
        session = _RecordingSession(self._results)
        self.sessions.append(session)
        return _SessionScope(session)

    @property
    def statements(self) -> List[str]:
        return [statement for session in self.sessions for statement in session.statements]

    @property
    def params(self) -> List[Dict[str, Any]]:
        return [params for session in self.sessions for params in session.params]


@pytest.fixture(autouse=True)
def _page_state() -> Any:
    clear_page()
    yield
    clear_page()


@pytest.fixture(autouse=True)
def _security(monkeypatch: pytest.MonkeyPatch) -> Any:
    """固定 ``SecurityUtils`` 的四个取值，避免依赖登录上下文。"""
    monkeypatch.setattr(SecurityUtils, "get_user_id", lambda: 7)
    monkeypatch.setattr(SecurityUtils, "get_eps_id", lambda: 11)
    monkeypatch.setattr(SecurityUtils, "get_tenant_id", lambda: 22)


def _patch_session(monkeypatch: pytest.MonkeyPatch, *results: _Result) -> _SessionFactory:
    """把两个模块里的 ``session_scope`` 都换掉。

    ``insert`` / ``update_by_id`` / ``delete_by_id`` / ``select_by_id`` 定义在
    :mod:`app.base.mapper.plus_mapper`，列表与自定义语句在本模块，两处都得钉。
    """
    factory = _SessionFactory(*results)
    monkeypatch.setattr(mapper_module, "session_scope", factory)
    monkeypatch.setattr(plus_mapper_module, "session_scope", factory)
    return factory


# --------------------------------------------------------------------------- 列表 SQL


class TestBuildListSql:
    def test_no_condition_means_no_where(self) -> None:
        sql, params = build_list_sql(BaseConfigServiceArea())

        assert "where" not in sql.lower()
        assert params == {}
        assert "del_flag" not in sql
        assert "order by" not in sql.lower()

    def test_every_declared_column_is_a_condition(self) -> None:
        sql, params = build_list_sql(
            BaseConfigServiceArea(
                id="u1",
                fwqbm="S001",
                fwqmc="吉安服务区",
                lon="114.9",
                lat="27.1",
                road_code="G45",
                section_code="G45-01",
                pile_no="K1+000",
                create_by=0,
            )
        )

        assert sql.count(" = :") == 9
        assert "t.id = :id" in sql
        assert "t.create_by = :create_by" in sql
        assert params["create_by"] == 0

    def test_empty_string_is_skipped_but_zero_is_not(self) -> None:
        sql, params = build_list_sql(BaseConfigServiceArea(fwqbm="", create_by=0))

        assert "fwqbm" not in params
        assert "create_by" in params
        assert params == {"create_by": 0}

    def test_fragments_are_joined_with_a_bare_and(self) -> None:
        sql, _ = build_list_sql(BaseConfigServiceArea(fwqbm="S001", fwqmc="A"))

        assert "where t.fwqbm = :fwqbm and t.fwqmc = :fwqmc" in sql


# --------------------------------------------------------------------------- insert


class TestInsert:
    def test_assign_uuid_and_fill_insert_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _patch_session(monkeypatch, _Result(rowcount=1))
        mapper = BaseConfigServiceAreaMapper()
        entity = BaseConfigServiceArea(fwqbm="S001")

        mapper.insert(entity)

        assert entity.id is not None and len(entity.id) == 32
        assert "-" not in entity.id
        assert entity.id == entity.id.lower()
        assert isinstance(entity.create_time, datetime)
        assert entity.create_by == 7
        assert entity.eps_id == 11
        assert entity.tenant_id == 22

        sql = factory.statements[0]
        assert sql.startswith("insert into base_config_service_area (id, ")
        assert "create_time" in sql
        assert sql.count(":") == len(factory.params[0])

    def test_none_columns_are_not_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _patch_session(monkeypatch, _Result(rowcount=1))

        BaseConfigServiceAreaMapper().insert(BaseConfigServiceArea(fwqbm="S001"))

        sql = factory.statements[0]
        for column in ("fwqmc", "lon", "lat", "road_code", "section_code", "pile_no"):
            assert column not in sql
        assert "del_flag" not in sql

    def test_a_given_eps_id_still_fills_the_tenant(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """P2-7：``tenant_id`` 以自己的值为判据，不再被调用方传入的 ``eps_id`` 阻断。"""
        _patch_session(monkeypatch, _Result(rowcount=1))
        entity = BaseConfigServiceArea(fwqbm="S001", eps_id=99)

        BaseConfigServiceAreaMapper().insert(entity)

        assert entity.eps_id == 99
        assert entity.tenant_id == 22

    def test_the_generated_id_is_written_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _patch_session(monkeypatch, _Result(rowcount=1))
        entity = BaseConfigServiceArea()

        BaseConfigServiceAreaMapper().insert(entity)

        assert factory.params[0]["id"] == entity.id


# --------------------------------------------------------------------------- update


class TestUpdateById:
    def test_sets_only_non_null_columns_and_filters_on_del_flag(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _patch_session(monkeypatch, _Result(rowcount=1))
        entity = BaseConfigServiceArea(id="u1", fwqbm="S001")

        BaseConfigServiceAreaMapper().update_by_id(entity)

        sql = factory.statements[0]
        assert sql.startswith("update base_config_service_area set ")
        assert "fwqbm = :fwqbm" in sql
        assert "where id = :id and del_flag = '0'" in sql
        assert "fwqmc" not in sql
        assert "update_time" in sql and "update_by = :update_by" in sql
        assert entity.update_by == 7

    def test_the_id_is_never_in_the_set_clause(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _patch_session(monkeypatch, _Result(rowcount=1))

        BaseConfigServiceAreaMapper().update_by_id(BaseConfigServiceArea(id="u1", fwqbm="S001"))

        assert "id = :id," not in factory.statements[0]


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_by_id_is_a_logic_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _patch_session(monkeypatch, _Result(rowcount=1))

        BaseConfigServiceAreaMapper().delete_by_id("u1")

        assert factory.statements[0] == (
            "update base_config_service_area set del_flag = '1' where id = :id and del_flag = '0'"
        )

    def test_delete_by_fwqbm_is_a_physical_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _patch_session(monkeypatch, _Result(rowcount=1))

        BaseConfigServiceAreaMapper().delete_by_fwqbm("S001")

        assert factory.statements[0] == "delete from base_config_service_area where fwqbm = :fwqbm"

    def test_delete_by_fwqbms_uses_an_in_clause(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _patch_session(monkeypatch, _Result(rowcount=2))

        count = BaseConfigServiceAreaMapper().delete_by_fwqbms(["S001", "S002"])

        assert count == 2
        assert factory.statements[0].startswith("delete from base_config_service_area where fwqbm in")
        assert sorted(factory.params[0].values()) == ["S001", "S002"]


# --------------------------------------------------------------------------- select


class TestSelect:
    def test_a_missing_row_maps_to_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_session(monkeypatch, _Result(rows=[]))

        assert BaseConfigServiceAreaMapper().select_by_fwqbm("nope") is None

    def test_rows_keep_only_the_seven_projected_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        row = _Row(
            {
                "fwqbm": "S001",
                "fwqmc": "吉安服务区",
                "lon": "1",
                "lat": "2",
                "road_code": "G45",
                "section_code": "G45-01",
                "pile_no": "K1",
            }
        )
        _patch_session(monkeypatch, _Result(rows=[row]))

        entity = BaseConfigServiceAreaMapper().select_by_fwqbm("S001")

        assert entity is not None
        assert entity.fwqmc == "吉安服务区"
        assert entity.id is None
        assert entity.create_time is None

    def test_list_takes_the_page_and_returns_metadata(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        row = _Row(
            {
                "fwqbm": "S001",
                "fwqmc": None,
                "lon": None,
                "lat": None,
                "road_code": None,
                "section_code": None,
                "pile_no": None,
            }
        )
        _patch_session(
            monkeypatch,
            _Result(scalar_value=3),
            _Result(rows=[row]),
        )
        start_page()

        rows = BaseConfigServiceAreaMapper().select_list(BaseConfigServiceArea())

        assert len(rows) == 1
        assert rows.total == 3


# --------------------------------------------------------------------------- service


class _FakeMapper:
    def __init__(self) -> None:
        self.calls: List[str] = []

    def insert(self, entity: BaseConfigServiceArea) -> int:
        self.calls.append("insert")
        entity.id = "generated"
        return 1

    def update_by_id(self, entity: BaseConfigServiceArea) -> int:
        self.calls.append("update_by_id")
        return 1

    def select_by_fwqbm(self, fwqbm: str) -> Optional[BaseConfigServiceArea]:
        self.calls.append("select_by_fwqbm")
        return None

    def select_list(self, query: BaseConfigServiceArea) -> List[BaseConfigServiceArea]:
        self.calls.append("select_list")
        return []

    def delete_by_fwqbms(self, fwqbms: Sequence[str]) -> int:
        self.calls.append("delete_by_fwqbms")
        return len(fwqbms)


class TestService:
    def test_a_blank_id_inserts(self) -> None:
        mapper = _FakeMapper()
        service = BaseConfigServiceAreaService(mapper)  # type: ignore[arg-type]

        result = service.save(BaseConfigServiceArea(fwqbm="S001"))

        assert mapper.calls == ["insert"]
        assert result == {"code": 200, "msg": "操作成功！", "data": "generated"}

    def test_a_non_blank_id_updates(self) -> None:
        mapper = _FakeMapper()
        service = BaseConfigServiceAreaService(mapper)  # type: ignore[arg-type]

        service.save(BaseConfigServiceArea(id="u1", fwqbm="S001"))

        assert mapper.calls == ["update_by_id"]

    def test_an_empty_string_id_inserts(self) -> None:
        mapper = _FakeMapper()
        service = BaseConfigServiceAreaService(mapper)  # type: ignore[arg-type]

        service.save(BaseConfigServiceArea(id="", fwqbm="S001"))

        assert mapper.calls == ["insert"]

    def test_delete_returns_the_row_count(self) -> None:
        mapper = _FakeMapper()
        service = BaseConfigServiceAreaService(mapper)  # type: ignore[arg-type]

        assert service.delete_by_ids(["A", "B"])["data"] == 2
