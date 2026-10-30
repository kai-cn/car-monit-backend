"""省界/收费站设备 ip —— ``/base/gantryIp`` 与 ``/base/tollStationIp``.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/base/OdsSzdnGantryIpController.java
#   ruoyi-admin/.../web/controller/base/OdsSzdnTollStationIpController.java
#   ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryIpMapper.xml
#   ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollStationIpMapper.xml

这是 ``base`` 包里最薄的一类模块（"Family-A"）：只有 ``/list`` 和 ``/{id}``，
两个端点都**没有** ``@PreAuthorize``，也**没有** ``del_flag`` / 审计列。

改错不会报错、只会悄悄改结果的地方
----------------------------------
1. 列表用的是 ``WHERE 1 = 1`` + 片段自带 ``and``，**不是** ``<where>``；
2. 两条列表都**已有** ``order by``，所以 PageHelper 不会追加客户端排序；
3. 收费站的排序键是 ``t.big_id``（不在投影、不在实体里）—— 照抄；
4. 门架列表有 ``id`` 过滤、收费站列表**没有**；
5. ``gantryName`` / ``tollName`` 是模糊匹配，其余字段是等值；
6. ``/{id}`` 是 ``Long``：``/abc`` 回 ``code 500``（HTTP 200），不是 404；
7. 门架的 ``type`` 字段名与 pydantic 无冲突，但**必须**出现在 JSON 里。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.base import ods_szdn_gantry_ip_controller as gantry_controller
from app.api.base import ods_szdn_toll_station_ip_controller as toll_controller
from app.base.domain.ods_szdn_gantry_ip import OdsSzdnGantryIp
from app.base.domain.ods_szdn_toll_station_ip import OdsSzdnTollStationIp
from app.base.mapper import ods_szdn_gantry_ip_mapper as gantry_mapper_module
from app.base.mapper import ods_szdn_toll_station_ip_mapper as toll_mapper_module
from app.base.mapper.ods_szdn_gantry_ip_mapper import (
    OdsSzdnGantryIpMapper,
    build_list_sql as build_gantry_list_sql,
)
from app.base.mapper.ods_szdn_toll_station_ip_mapper import (
    OdsSzdnTollStationIpMapper,
    build_list_sql as build_toll_list_sql,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, start_page, take_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)

# --------------------------------------------------------------------------- fakes


class _Row:
    """One result row: ``_mapping`` 就够 ``_map_row`` 用了。"""

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


def _patch(monkeypatch: pytest.MonkeyPatch, module: Any, *results: _Result) -> _SessionFactory:
    factory = _SessionFactory(*results)
    monkeypatch.setattr(module, "session_scope", factory)
    return factory


class _FakeGantryService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[OdsSzdnGantryIp] = []
        self.by_id_result: Optional[OdsSzdnGantryIp] = None
        self.page_taken: Any = None

    def select_list(self, query: OdsSzdnGantryIp) -> List[OdsSzdnGantryIp]:
        self.calls.append(("select_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_by_id(self, entity_id: int) -> Optional[OdsSzdnGantryIp]:
        self.calls.append(("select_by_id", entity_id))
        return self.by_id_result


class _FakeTollService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[OdsSzdnTollStationIp] = []
        self.by_id_result: Optional[OdsSzdnTollStationIp] = None

    def select_list(self, query: OdsSzdnTollStationIp) -> List[OdsSzdnTollStationIp]:
        self.calls.append(("select_list", query.model_copy(deep=True)))
        take_page()
        return self.list_result

    def select_by_id(self, entity_id: int) -> Optional[OdsSzdnTollStationIp]:
        self.calls.append(("select_by_id", entity_id))
        return self.by_id_result


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    gantry = _FakeGantryService()
    toll = _FakeTollService()
    monkeypatch.setattr(gantry_controller, "_SERVICE", gantry)
    monkeypatch.setattr(toll_controller, "_SERVICE", toll)
    yield gantry, toll
    SecurityContextHolder.clear_context()
    clear_page()
    gantry_controller.reset_gantry_ip_controller()
    toll_controller.reset_toll_station_ip_controller()


def _build_app(router: Any, login: bool = True, permissions: Optional[set] = None) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:

        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            SecurityContextHolder.get_context().set_authentication(
                UsernamePasswordAuthenticationToken(
                    LoginUser(
                        user=SysUser(user_id=2, user_name="ry"),
                        permissions={"*:*:*"} if permissions is None else permissions,
                    ),
                    None,
                    [],
                )
            )
            return await call_next(request)

    application.include_router(router)
    return application


@pytest.fixture
def gantry_http() -> Any:
    return TestClient(_build_app(gantry_controller.router))


@pytest.fixture
def toll_http() -> Any:
    return TestClient(_build_app(toll_controller.router))


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_gantry_registers_two_paths(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in gantry_controller.router.routes
        }

        assert registered == {
            ("/base/gantryIp/list", ("GET",)),
            ("/base/gantryIp/{id}", ("GET",)),
        }

    def test_toll_station_registers_two_paths(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in toll_controller.router.routes
        }

        assert registered == {
            ("/base/tollStationIp/list", ("GET",)),
            ("/base/tollStationIp/{id}", ("GET",)),
        }

    def test_the_literal_list_comes_before_the_path_variable(self) -> None:
        for router, prefix in (
            (gantry_controller.router, "/base/gantryIp"),
            (toll_controller.router, "/base/tollStationIp"),
        ):
            paths = [route.path for route in router.routes]
            assert paths.index(f"{prefix}/list") < paths.index(f"{prefix}/{{id}}")


# --------------------------------------------------------------------------- 查询


class TestGantryList:
    def test_returns_the_table_data_info_envelope(self, gantry_http: Any) -> None:
        gantry, _ = _current()
        gantry.list_result = [OdsSzdnGantryIp(id=1, gantry_code="G001")]

        body = gantry_http.get("/base/gantryIp/list").json()

        assert body["code"] == 200
        assert body["msg"] == "查询成功"
        assert body["total"] == 1
        assert body["rows"][0]["gantryCode"] == "G001"

    def test_start_page_is_consumed(self, gantry_http: Any) -> None:
        gantry, _ = _current()

        gantry_http.get("/base/gantryIp/list?pageNum=2&pageSize=5")

        assert gantry.calls[0][0] == "select_list"
        assert gantry.page_taken is not None

    def test_query_string_binds_camel_case_names(self, gantry_http: Any) -> None:
        gantry, _ = _current()

        gantry_http.get("/base/gantryIp/list?gantryCode=G001&gantryName=%E6%9D%AD%E5%B7%9E")

        query = gantry.calls[0][1]
        assert query.gantry_code == "G001"
        assert query.gantry_name == "杭州"

    def test_list_needs_no_permission_point(self) -> None:
        """``OdsSzdnGantryIpController`` 没有 ``@PreAuthorize`` —— 登录即可，零权限也 200。"""
        client = TestClient(_build_app(gantry_controller.router, permissions=set()))

        assert client.get("/base/gantryIp/list").json()["code"] == 200


class TestGantryGetInfo:
    def test_returns_the_entity_in_data(self, gantry_http: Any) -> None:
        gantry, _ = _current()
        gantry.by_id_result = OdsSzdnGantryIp(id=7, gantry_code="G001", type="1")

        body = gantry_http.get("/base/gantryIp/7").json()

        assert body["code"] == 200
        assert body["data"]["id"] == 7
        assert body["data"]["type"] == "1"

    def test_missing_row_is_null_not_404(self, gantry_http: Any) -> None:
        gantry, _ = _current()
        gantry.by_id_result = None

        response = gantry_http.get("/base/gantryIp/999")

        assert response.status_code == 200
        assert response.json() == {"code": 200, "msg": "操作成功"}

    def test_a_non_numeric_id_is_a_code_500(self, gantry_http: Any) -> None:
        """Java ``@PathVariable Long`` 的类型不匹配 -> 全局处理器 -> ``code 500``（HTTP 200）。"""
        gantry, _ = _current()

        response = gantry_http.get("/base/gantryIp/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500
        assert gantry.calls == []

    def test_the_entity_carries_the_unmapped_nested_object(self, gantry_http: Any) -> None:
        """``@TableField(exist = false)`` —— JSON 里有这个键，值恒为 ``null``。"""
        gantry, _ = _current()
        gantry.by_id_result = OdsSzdnGantryIp(id=7)

        data = gantry_http.get("/base/gantryIp/7").json()["data"]

        assert "odsSzdnGantry" in data
        assert data["odsSzdnGantry"] is None


class TestTollStationEndpoints:
    def test_list_envelope(self, toll_http: Any) -> None:
        _, toll = _current()
        toll.list_result = [OdsSzdnTollStationIp(id=3, toll_code="T001")]

        body = toll_http.get("/base/tollStationIp/list").json()

        assert body["total"] == 1
        assert body["rows"][0]["tollCode"] == "T001"

    def test_get_info(self, toll_http: Any) -> None:
        _, toll = _current()
        toll.by_id_result = OdsSzdnTollStationIp(id=3, toll_name="杭州西")

        assert toll_http.get("/base/tollStationIp/3").json()["data"]["tollName"] == "杭州西"

    def test_list_needs_no_permission_point(self) -> None:
        client = TestClient(_build_app(toll_controller.router, permissions=set()))

        assert client.get("/base/tollStationIp/list").json()["code"] == 200

    def test_a_non_numeric_id_is_a_code_500(self, toll_http: Any) -> None:
        response = toll_http.get("/base/tollStationIp/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- 门架 SQL


class TestGantryListSql:
    def test_no_condition_keeps_where_1_eq_1_and_the_fixed_order(self) -> None:
        sql, params = build_gantry_list_sql(OdsSzdnGantryIp())

        assert "where 1 = 1" in sql
        assert sql.endswith("order by t.id")
        assert params == {}
        assert "del_flag" not in sql

    def test_every_declared_column_is_a_condition(self) -> None:
        sql, params = build_gantry_list_sql(
            OdsSzdnGantryIp(
                id=5,
                gantry_code="G001",
                gantry_name="杭州",
                org_code="3301",
                ip="10.0.0.1",
                brand="hikvision",
                type="1",
            )
        )

        assert sql.count(" = :") == 6  # id/gantry_code/org_code/ip/brand/type
        assert "and t.gantry_name like concat('%', :gantry_name, '%')" in sql
        assert params["gantry_name"] == "杭州"
        assert params["id"] == 5

    def test_the_like_column_is_not_an_equality(self) -> None:
        sql, _ = build_gantry_list_sql(OdsSzdnGantryIp(gantry_name="杭州"))

        assert "t.gantry_name = :gantry_name" not in sql

    def test_empty_strings_are_skipped(self) -> None:
        _, params = build_gantry_list_sql(OdsSzdnGantryIp(gantry_code="", org_code=""))

        assert params == {}

    def test_a_zero_id_is_skipped_like_the_ognl_comparison(self) -> None:
        """``id != null and id != ''`` 对 ``Long`` 等价于 ``id != 0``。"""
        sql, params = build_gantry_list_sql(OdsSzdnGantryIp(id=0))

        assert "and t.id = :id" not in sql
        assert params == {}

    def test_fragments_keep_their_leading_and(self) -> None:
        sql, _ = build_gantry_list_sql(OdsSzdnGantryIp(gantry_code="A", org_code="B"))

        assert "where 1 = 1 and t.gantry_code = :gantry_code and t.org_code = :org_code" in sql


class TestGantryMapper:
    def test_list_takes_the_page_and_returns_metadata(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        row = _Row(
            {
                "id": 1,
                "gantry_code": "G001",
                "gantry_name": None,
                "org_code": None,
                "ip": None,
                "brand": None,
                "type": None,
            }
        )
        _patch(
            monkeypatch,
            gantry_mapper_module,
            _Result(scalar_value=9),
            _Result(rows=[row]),
        )
        start_page()

        rows = OdsSzdnGantryIpMapper().select_list(OdsSzdnGantryIp())

        assert len(rows) == 1
        assert rows.total == 9
        assert isinstance(rows[0], OdsSzdnGantryIp)

    def test_the_count_statement_wraps_the_data_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _patch(
            monkeypatch,
            gantry_mapper_module,
            _Result(scalar_value=0),
            _Result(rows=[]),
        )
        start_page()

        OdsSzdnGantryIpMapper().select_list(OdsSzdnGantryIp())

        assert factory.statements[0].startswith("select count(0) from (SELECT")

    def test_select_by_id_is_a_plain_equality(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _patch(monkeypatch, gantry_mapper_module, _Result(rows=[]))

        assert OdsSzdnGantryIpMapper().select_by_id(7) is None
        assert factory.statements[0] == (
            "select t.id, t.gantry_code, t.gantry_name, t.org_code, t.ip, t.brand, t.type "
            "from ods_szdn_gantry_ip t where t.id = :id"
        )
        assert factory.params[0] == {"id": 7}

    def test_rows_keep_only_the_seven_projected_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch(
            monkeypatch,
            gantry_mapper_module,
            _Result(rows=[_Row({"id": 1, "gantry_code": "G001", "unexpected": "x"})]),
        )

        entity = OdsSzdnGantryIpMapper().select_by_id(1)

        assert entity is not None
        assert entity.gantry_code == "G001"
        assert entity.ods_szdn_gantry is None


# --------------------------------------------------------------------------- 收费站 SQL


class TestTollStationListSql:
    def test_no_condition_keeps_the_big_id_order(self) -> None:
        """``order by t.big_id`` —— 逐字照抄，别改成 ``t.id``。"""
        sql, params = build_toll_list_sql(OdsSzdnTollStationIp())

        assert "where 1 = 1" in sql
        assert sql.endswith("order by t.big_id")
        assert params == {}

    def test_every_declared_column_is_a_condition(self) -> None:
        sql, params = build_toll_list_sql(
            OdsSzdnTollStationIp(
                toll_code="T001",
                toll_name="杭州西",
                org_code="3301",
                ip="10.0.0.1",
                brand="hikvision",
            )
        )

        assert sql.count(" = :") == 4  # toll_code/org_code/ip/brand
        assert "and t.toll_name like concat('%', :toll_name, '%')" in sql
        assert params["toll_name"] == "杭州西"

    def test_there_is_no_id_condition(self) -> None:
        """对比门架：XML 里**没有** ``<if test="id ...">``，传了也不过滤。"""
        sql, params = build_toll_list_sql(OdsSzdnTollStationIp(id=5))

        assert "and t.id = :id" not in sql
        assert "id" not in params

    def test_empty_strings_are_skipped(self) -> None:
        _, params = build_toll_list_sql(OdsSzdnTollStationIp(toll_code="", brand=""))

        assert params == {}


class TestTollStationMapper:
    def test_select_by_id_sql(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _patch(monkeypatch, toll_mapper_module, _Result(rows=[]))

        OdsSzdnTollStationIpMapper().select_by_id(3)

        assert factory.statements[0] == (
            "select t.id, t.toll_code, t.toll_name, t.org_code, t.ip, t.brand "
            "from ods_szdn_toll_station_ip t where t.id = :id"
        )

    def test_rows_keep_only_the_six_projected_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch(
            monkeypatch,
            toll_mapper_module,
            _Result(rows=[_Row({"id": 3, "toll_name": "杭州西", "big_id": 99})]),
        )

        entity = OdsSzdnTollStationIpMapper().select_by_id(3)

        assert entity is not None
        assert entity.toll_name == "杭州西"
        assert entity.id == 3


# --------------------------------------------------------------------------- 小工具


def _current() -> Any:
    """读取当前测试注入的两个假 Service（供 ``TestXxx`` 内联使用）。"""
    from app.api.base import ods_szdn_gantry_ip_controller as g
    from app.api.base import ods_szdn_toll_station_ip_controller as t

    return g._SERVICE, t._SERVICE
