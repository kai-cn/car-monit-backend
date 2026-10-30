"""base 包第二批只读 ODS 表（6 个模块）.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/base/{OdsCxztFwqclls,OdsLwzxsfsjFeeStationEnter01,
#       OdsRtSzdnSnapshotFlowProvcaptureAddcode,OdsRtSzdnSnapshotFlowStationcaptureAddcode,
#       OdsSzdnProvinceBorderVehicleWeightNewstructure,ZdataTrailTracks}Controller.java
#   ruoyi-system/src/main/resources/mapper/base/<同名>Mapper.xml

覆盖 6 个"生成器模板 + 只读"模块：

===========================  =========================  ======================
模块                          URL 前缀                    详情键
===========================  =========================  ======================
``OdsCxztFwqclls``           ``/manager/fwqclls``        ``big_id``（Long）
``OdsLwzxsfsjFeeStationEnter01`` ``/base/feeStationEnter``  ``big_id``（Long）
``OdsRtSzdnSnapshotFlowProvcaptureAddcode`` ``/base/provcapture`` ``big_id``（Long）
``OdsRtSzdnSnapshotFlowStationcaptureAddcode`` ``/base/stationcapture`` ``big_id``（Long）
``OdsSzdnProvinceBorderVehicleWeightNewstructure`` ``/base/vehicleweight`` ``dataSource``（String）
``ZdataTrailTracks``         ``/base/trailtracks``      ``uuid``（String）
===========================  =========================  ======================

重点守住的 8 个"改错也不报错"的地方
-----------------------------------
1. ``fwqclls`` 前缀是 ``/manager/...``，且 ``list`` **有**权限点；其余 5 个没有。
2. ``fwqclls`` / ``vehicleweight`` **没有** ``order by``（客户端排序生效）；
   另外 3 个有 ``order by t.big_id``；``trailtracks`` 是 ``order by t.enter_time desc``。
3. ``feeStationEnter`` 投影里多出的 ``t.id`` 不在 ``RESULT_COLUMNS`` 里。
4. ``trailtracks`` 投影里的 ``t.create_time`` 同样被丢弃。
5. ``trailtracks`` 的瞬态字段 ``carNo`` 映射到 ``plate_key`` 列。
6. ``vehicleweight`` 的两列是 snake_case（``load_time`` / ``grade_level``）。
7. ``vehicleweight`` 的详情键是 ``dataSource``，不是主键 ``datauuid``。
8. ``carTrackQuery`` 在"常用路线查不到"时**不会**退化成普通查询。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.base import ods_cxzt_fwqclls_controller as fwqclls_controller
from app.api.base import (
    ods_lwzxsfsj_fee_station_enter01_controller as fee_station_controller,
)
from app.api.base import (
    ods_rt_szdn_snapshot_flow_provcapture_addcode_controller as prov_controller,
)
from app.api.base import (
    ods_rt_szdn_snapshot_flow_stationcapture_addcode_controller as station_controller,
)
from app.api.base import (
    ods_szdn_province_border_vehicle_weight_newstructure_controller as weight_controller,
)
from app.api.base import zdata_trail_tracks_controller as trail_controller
from app.base.domain.ods_cxzt_fwqclls import OdsCxztFwqclls
from app.base.domain.ods_rt_szdn_snapshot_flow_provcapture_addcode import (
    OdsRtSzdnSnapshotFlowProvcaptureAddcode,
)
from app.base.domain.ods_rt_szdn_snapshot_flow_stationcapture_addcode import (
    OdsRtSzdnSnapshotFlowStationcaptureAddcode,
)
from app.base.domain.ods_szdn_province_border_vehicle_weight_newstructure import (
    OdsSzdnProvinceBorderVehicleWeightNewstructure,
)
from app.base.domain.zdata_trail_tracks import ZdataTrailTracks
from app.base.mapper import (
    ods_szdn_province_border_vehicle_weight_newstructure_mapper as weight_mapper_module,
)
from app.base.mapper import zdata_trail_tracks_mapper as trail_mapper_module
from app.base.mapper.ods_cxzt_fwqclls_mapper import (
    CONDITIONS as FWQCLLS_CONDITIONS,
    OdsCxztFwqcllsMapper,
)
from app.base.mapper.ods_sql import map_row
from app.base.mapper.ods_szdn_province_border_vehicle_weight_newstructure_mapper import (
    OdsSzdnProvinceBorderVehicleWeightNewstructureMapper,
)
from app.base.mapper.zdata_trail_tracks_mapper import (
    CYLY_RESULT_COLUMNS,
    HISTORY_CONDITIONS,
    LIST_CONDITIONS,
    RESULT_COLUMNS as TRAIL_RESULT_COLUMNS,
    ZdataTrailTracksMapper,
    build_cyly_sql,
    build_history_trail_sql,
)
from app.base.service.zdata_trail_tracks_service import ZdataTrailTracksService
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
    """One result row: ``_mapping`` 就够 ``map_row`` 用了。"""

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

    def execute(
        self, statement: Any, params: Optional[Dict[str, Any]] = None
    ) -> _Result:
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


def _sql(query: Any, mapper: Any) -> str:
    """列表 SQL 压成单行，便于断言片段。"""
    sql, _params = mapper.build_list_sql(query)
    return " ".join(sql.split())


class _FakeService:
    """6 个 Service 都只有 ``select_list`` / ``select_by_id``，共用一个假实现。"""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[Any] = []
        self.by_id_result: Any = None
        self.page_taken: Any = None

    def select_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_by_id", entity_id))
        return self.by_id_result


_MODULES = (
    (fwqclls_controller, "fwqclls"),
    (fee_station_controller, "feeStationEnter"),
    (prov_controller, "provcapture"),
    (station_controller, "stationcapture"),
    (weight_controller, "vehicleweight"),
    (trail_controller, "trailtracks"),
)


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    fakes = {}
    for module, name in _MODULES:
        fake = _FakeService()
        fakes[name] = fake
        monkeypatch.setattr(module, "_SERVICE", fake)
    yield fakes
    SecurityContextHolder.clear_context()
    clear_page()
    for module, _name in _MODULES:
        module._SERVICE = None


def _current(name: str) -> Any:
    return next(module._SERVICE for module, key in _MODULES if key == name)


def _build_app(
    router: Any, login: bool = True, permissions: Optional[set] = None
) -> FastAPI:
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
def fwqclls_http() -> Any:
    return TestClient(_build_app(fwqclls_controller.router))


@pytest.fixture
def fee_station_http() -> Any:
    return TestClient(_build_app(fee_station_controller.router))


@pytest.fixture
def prov_http() -> Any:
    return TestClient(_build_app(prov_controller.router))


@pytest.fixture
def station_http() -> Any:
    return TestClient(_build_app(station_controller.router))


@pytest.fixture
def weight_http() -> Any:
    return TestClient(_build_app(weight_controller.router))


@pytest.fixture
def trail_http() -> Any:
    return TestClient(_build_app(trail_controller.router))


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_fwqclls_lives_under_manager_not_base(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in fwqclls_controller.router.routes
        }

        assert registered == {
            ("/manager/fwqclls/list", ("GET",)),
            ("/manager/fwqclls/{bigId}", ("GET",)),
        }

    def test_five_base_prefixes(self) -> None:
        expected = (
            (fee_station_controller.router, "/base/feeStationEnter"),
            (prov_controller.router, "/base/provcapture"),
            (station_controller.router, "/base/stationcapture"),
            (weight_controller.router, "/base/vehicleweight"),
            (trail_controller.router, "/base/trailtracks"),
        )

        for router, prefix in expected:
            paths = [route.path for route in router.routes]
            assert paths[0] == f"{prefix}/list"
            assert len(paths) == 2

    def test_detail_key_names_match_java(self) -> None:
        assert [r.path for r in fwqclls_controller.router.routes][1].endswith("{bigId}")
        assert [r.path for r in fee_station_controller.router.routes][1].endswith("{bigId}")
        assert [r.path for r in prov_controller.router.routes][1].endswith("{bigId}")
        assert [r.path for r in station_controller.router.routes][1].endswith("{bigId}")
        assert [r.path for r in weight_controller.router.routes][1].endswith(
            "{dataSource}"
        )
        assert [r.path for r in trail_controller.router.routes][1].endswith("{uuid}")


# --------------------------------------------------------------------------- 权限


class TestPermission:
    def test_fwqclls_list_needs_the_manager_permission(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = TestClient(
            _build_app(fwqclls_controller.router, permissions={"base:configServiceArea:list"})
        )

        body = client.get("/manager/fwqclls/list").json()

        # Java: AccessDeniedException -> 全局处理器改写成 HTTP 200 + code 403。
        assert body["code"] == 403
        assert _current("fwqclls").calls == []

    def test_fwqclls_list_passes_with_its_own_permission(self, fwqclls_http: Any) -> None:
        body = fwqclls_http.get("/manager/fwqclls/list").json()

        assert body["code"] == 200

    @pytest.mark.parametrize(
        "name,path",
        [
            ("feeStationEnter", "/base/feeStationEnter/list"),
            ("provcapture", "/base/provcapture/list"),
            ("stationcapture", "/base/stationcapture/list"),
            ("vehicleweight", "/base/vehicleweight/list"),
            ("trailtracks", "/base/trailtracks/list"),
        ],
    )
    def test_other_lists_are_login_only(self, name: str, path: str) -> None:
        module = next(module for module, key in _MODULES if key == name)
        client = TestClient(_build_app(module.router, permissions=set()))

        body = client.get(path).json()

        assert body["code"] == 200


# --------------------------------------------------------------------------- 列表


class TestListEnvelope:
    def test_returns_query_success_and_rows(self, fee_station_http: Any) -> None:
        fake = _current("feeStationEnter")
        fake.list_result = []

        body = fee_station_http.get("/base/feeStationEnter/list").json()

        assert body == {"code": 200, "msg": "查询成功", "total": 0, "rows": []}

    def test_start_page_is_consumed_by_the_service(
        self, prov_http: Any
    ) -> None:
        fake = _current("provcapture")

        prov_http.get("/base/provcapture/list?pageNum=2&pageSize=5")

        # 这里的 mini app 没装 ``RequestContextMiddleware``，所以 ``start_page()``
        # 读不到 query string，只能拿到缺省的第 1 页 / 每页 10 条（完整应用里有）。
        # 要验证的是"有没有挂起分页"，不是"挂起了几"。
        assert fake.calls[0][0] == "select_list"
        assert fake.page_taken is not None

    def test_query_string_binds_to_entity_aliases(self, trail_http: Any) -> None:
        fake = _current("trailtracks")

        trail_http.get(
            "/base/trailtracks/list?carNo=%E4%BA%ACA12345&applyTime1=2025-01-01"
            "&applyTime2=2025-01-31"
        )

        query = fake.calls[0][1]
        assert query.car_no == "京A12345"
        assert query.apply_time1 == "2025-01-01"
        assert query.apply_time2 == "2025-01-31"

    def test_numeric_filter_zero_is_kept_for_vehicleweight(self, weight_http: Any) -> None:
        fake = _current("vehicleweight")

        weight_http.get("/base/vehicleweight/list?isOverweight=0")

        assert fake.calls[0][1].is_overweight == 0


# --------------------------------------------------------------------------- 详情


@pytest.mark.parametrize(
    "name,path",
    [
        ("fwqclls", "/manager/fwqclls/12"),
        ("feeStationEnter", "/base/feeStationEnter/12"),
        ("provcapture", "/base/provcapture/12"),
        ("stationcapture", "/base/stationcapture/12"),
    ],
)
def test_long_path_variable_is_converted(
    name: str, path: str
) -> None:
    module = next(module for module, key in _MODULES if key == name)
    client = TestClient(_build_app(module.router))

    body = client.get(path).json()

    # Java: AjaxResult.success(data) 在 data == null 时**不写** data 键。
    assert body["code"] == 200
    assert body == {"code": 200, "msg": "操作成功"}


@pytest.mark.parametrize(
    "name,path",
    [
        ("fwqclls", "/manager/fwqclls/abc"),
        ("feeStationEnter", "/base/feeStationEnter/abc"),
        ("provcapture", "/base/provcapture/abc"),
        ("stationcapture", "/base/stationcapture/abc"),
    ],
)
def test_non_numeric_long_path_variable_returns_code_500(name: str, path: str) -> None:
    module = next(module for module, key in _MODULES if key == name)
    client = TestClient(_build_app(module.router))

    response = client.get(path)

    # Java: MethodArgumentTypeMismatchException -> 全局处理器 -> HTTP 200 + code 500。
    assert response.status_code == 200
    assert response.json()["code"] == 500


def test_string_path_variables_accept_anything(weight_http: Any, trail_http: Any) -> None:
    assert weight_http.get("/base/vehicleweight/1001").json()["code"] == 200
    assert trail_http.get("/base/trailtracks/clobber").json()["code"] == 200

    assert _current("vehicleweight").calls[-1] == ("select_by_id", "1001")
    assert _current("trailtracks").calls[-1] == ("select_by_id", "clobber")


# --------------------------------------------------------------------------- SQL


class TestFwqcllsSql:
    def test_has_no_order_by(self) -> None:
        sql = _sql(OdsCxztFwqclls(), OdsCxztFwqcllsMapper())

        assert "order by" not in sql.lower()
        assert "from ods_cxzt_fwqclls t where 1 = 1" in sql.lower()

    def test_three_like_filters(self) -> None:
        query = OdsCxztFwqclls(
            directionname="京", devicename="枪机", servicename="阳澄湖"
        )

        sql = _sql(query, OdsCxztFwqcllsMapper())

        assert "and t.directionname like concat('%', :directionname, '%')" in sql
        assert "and t.devicename like concat('%', :devicename, '%')" in sql
        assert "and t.servicename like concat('%', :servicename, '%')" in sql

    def test_big_id_null_only_keeps_zero(self) -> None:
        # XML: <if test="bigId != null "> —— 0 会生效（与 gantryIp 的 != '' 相反）。
        sql = _sql(OdsCxztFwqclls(big_id=0), OdsCxztFwqcllsMapper())

        assert "and t.big_id = :big_id" in sql

    def test_condition_count_matches_the_xml(self) -> None:
        assert len(FWQCLLS_CONDITIONS) == 18


class TestFeeStationEnterSql:
    def test_order_by_big_id_disables_client_sorting(self) -> None:
        from app.base.mapper.ods_lwzxsfsj_fee_station_enter01_mapper import (
            OdsLwzxsfsjFeeStationEnter01Mapper,
        )

        sql = _sql(object(), OdsLwzxsfsjFeeStationEnter01Mapper())

        assert sql.endswith("order by t.big_id")

    def test_stray_projection_column_is_not_mapped(self) -> None:
        from app.base.mapper.ods_lwzxsfsj_fee_station_enter01_mapper import (
            RESULT_COLUMNS,
            SELECT_ODS_LWZXSFSJ_FEE_STATION_ENTER01_VO,
        )

        # 投影里有 t.id，resultMap 没有 -> 读出来丢弃。
        assert "t.id" in SELECT_ODS_LWZXSFSJ_FEE_STATION_ENTER01_VO
        assert "id" not in RESULT_COLUMNS


class TestCaptureSql:
    def test_prov_capture_condition_count(self) -> None:
        from app.base.mapper.ods_rt_szdn_snapshot_flow_provcapture_addcode_mapper import (
            CONDITIONS,
        )

        assert len(CONDITIONS) == 82

    def test_station_capture_condition_count_and_like(self) -> None:
        from app.base.mapper.ods_rt_szdn_snapshot_flow_stationcapture_addcode_mapper import (
            CONDITIONS,
            OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper,
        )

        # XML: <if> 出现在第 86~119 行，共 34 条（bigId 是 null-only）。
        assert len(CONDITIONS) == 34
        sql = _sql(
            OdsRtSzdnSnapshotFlowStationcaptureAddcode(
                tollname="阳澄湖", maindirectionname="上行"
            ),
            OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper(),
        )
        assert "and t.tollname like concat('%', :tollname, '%')" in sql
        assert "and t.maindirectionname like concat('%', :maindirectionname, '%')" in sql

    def test_speed_is_a_string_filter(self) -> None:
        from app.base.mapper.ods_rt_szdn_snapshot_flow_provcapture_addcode_mapper import (
            OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper,
        )

        query = OdsRtSzdnSnapshotFlowProvcaptureAddcode(speed="80")
        sql = _sql(query, OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper())

        assert "and t.speed = :speed" in sql


class TestVehicleWeightSql:
    def test_has_no_order_by(self) -> None:
        sql = _sql(OdsSzdnProvinceBorderVehicleWeightNewstructure(), OdsSzdnProvinceBorderVehicleWeightNewstructureMapper())

        assert "order by" not in sql.lower()
        assert (
            "from ods_szdn_province_border_vehicle_weight_newstructure t where 1 = 1"
            in sql.lower()
        )

    def test_camel_case_columns_keep_their_names(self) -> None:
        query = OdsSzdnProvinceBorderVehicleWeightNewstructure(
            data_source="SZDN", plate_no="京A12345"
        )

        sql = _sql(query, OdsSzdnProvinceBorderVehicleWeightNewstructureMapper())

        assert "and t.dataSource = :data_source" in sql
        assert "and t.plateNo = :plate_no" in sql

    def test_two_snake_case_columns(self) -> None:
        query = OdsSzdnProvinceBorderVehicleWeightNewstructure(
            load_time=datetime(2025, 9, 18), grade_level=1
        )

        sql = _sql(query, OdsSzdnProvinceBorderVehicleWeightNewstructureMapper())

        assert "and t.load_time = :load_time" in sql
        assert "and t.grade_level = :grade_level" in sql

    def test_detail_key_is_data_source(self) -> None:
        assert (
            OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.detail_column
            == "dataSource"
        )


class TestTrailTracksSql:
    def test_order_by_enter_time_desc(self) -> None:
        sql = _sql(ZdataTrailTracks(), ZdataTrailTracksMapper())

        assert sql.endswith("order by t.enter_time desc")

    def test_car_no_targets_the_plate_key_column(self) -> None:
        sql = _sql(ZdataTrailTracks(car_no="京A12345"), ZdataTrailTracksMapper())

        assert "and t.plate_key = :car_no" in sql

    def test_apply_time_templates(self) -> None:
        query = ZdataTrailTracks(apply_time1="2025-01-01", apply_time2="2025-01-31")

        sql = _sql(query, ZdataTrailTracksMapper())

        assert "and t.enter_time >= STR_TO_DATE(:apply_time1,'%Y-%m-%d')" in sql
        assert (
            "and t.enter_time < date_add(STR_TO_DATE(:apply_time2,'%Y-%m-%d'), "
            "interval 1 day)" in sql
        )

    def test_history_trail_expands_uuid_list(self) -> None:
        query = ZdataTrailTracks(uuid_list=["u1", "u2"])

        sql, params = build_history_trail_sql(query)
        flat = " ".join(sql.split())

        assert "and uuid in (:uuid0, :uuid1)" in flat
        assert params == {"uuid0": "u1", "uuid1": "u2"}
        assert flat.endswith("order by t.enter_time desc")

    def test_history_trail_plate_key_is_a_like(self) -> None:
        sql, _ = build_history_trail_sql(ZdataTrailTracks(plate_key="京A"))

        assert "like concat('%', :plate_key, '%')" in " ".join(sql.split())

    def test_cyly_keeps_the_inner_where_and_limit(self) -> None:
        sql, _ = build_cyly_sql(ZdataTrailTracks(car_no="京A12345"))
        flat = " ".join(sql.split())

        assert "WHERE 1=1 and t.plate_key = :car_no" in flat
        assert "LIMIT 3" in flat
        assert "WHERE rn = 1" in flat
        assert flat.endswith("order by passCount desc")

    def test_create_time_is_projected_but_never_mapped(self) -> None:
        from app.base.mapper.zdata_trail_tracks_mapper import (
            SELECT_ZDATA_TRAIL_TRACKS_VO,
        )

        assert "t.create_time" in SELECT_ZDATA_TRAIL_TRACKS_VO
        assert "create_time" not in TRAIL_RESULT_COLUMNS

    def test_condition_counts(self) -> None:
        assert len(LIST_CONDITIONS) == 10
        assert len(HISTORY_CONDITIONS) == 5
        assert CYLY_RESULT_COLUMNS == ("uuid", "passCount")

    def test_remove_real_data_without_cars_deletes_everything(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=7))
        monkeypatch.setattr(trail_mapper_module, "session_scope", factory)

        affected = ZdataTrailTracksMapper().remove_real_data([])

        assert affected == 7
        assert factory.statements == ["delete from zdata_trail_tracks t"]

    def test_remove_real_data_with_cars_uses_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=2))
        monkeypatch.setattr(trail_mapper_module, "session_scope", factory)

        ZdataTrailTracksMapper().remove_real_data(["京A", "京B"])

        assert factory.statements == [
            "delete from zdata_trail_tracks t WHERE plate_key in (:p0, :p1)"
        ]


# --------------------------------------------------------------------------- 行映射


class TestMapRow:
    def test_unmapped_column_is_dropped(self) -> None:
        row = _Row({"uuid": "u1", "point_count": 3, "create_time": "2025-09-18"})

        entity = map_row(ZdataTrailTracks, TRAIL_RESULT_COLUMNS, row)

        assert entity.uuid == "u1"
        assert entity.point_count == 3
        assert not hasattr(entity, "create_time")

    def test_camel_case_column_fills_the_snake_case_field(self) -> None:
        row = _Row({"dataSource": "SZDN", "weighingImagesArry": "[1,2]"})

        entity = map_row(
            OdsSzdnProvinceBorderVehicleWeightNewstructure,
            ("dataSource", "weighingImagesArry"),
            row,
        )

        assert entity.data_source == "SZDN"
        assert entity.weighing_images_arry == "[1,2]"


# --------------------------------------------------------------------------- JSON


class TestJsonShape:
    def test_vehicle_weight_uses_camel_case_keys(self) -> None:
        payload = OdsSzdnProvinceBorderVehicleWeightNewstructure(
            data_source="SZDN",
            plate_no="京A12345",
            weighing_images_arry="[]",
            is_overweight=1,
            check_time=datetime(2025, 9, 18, 13, 45),
        ).to_json_dict()

        assert payload["dataSource"] == "SZDN"
        assert payload["plateNo"] == "京A12345"
        assert payload["weighingImagesArry"] == "[]"
        assert payload["isOverweight"] == 1
        # @JsonFormat("yyyy-MM-dd") -> 字符串，时间被截断
        assert payload["checkTime"] == "2025-09-18"
        # 没有 @JsonFormat 的 Long 字段仍是数字
        assert payload["vehicleWeight"] is None

    def test_trail_tracks_uses_date_time_format(self) -> None:
        payload = ZdataTrailTracks(
            uuid="u1", enter_time=datetime(2025, 9, 18, 13, 45, 6)
        ).to_json_dict()

        assert payload["enterTime"] == "2025-09-18 13:45:06"
        assert payload["exitTime"] is None

    def test_trail_tracks_transients_are_present_as_null(self) -> None:
        payload = ZdataTrailTracks().to_json_dict()

        # @TableField(exist = false) 的字段不出现在 SQL 里，但**出现在 JSON 里**。
        for key in (
            "carNo",
            "applyTime1",
            "applyTime2",
            "uuidList",
            "passCount",
            "startLonDec",
            "stratLatDec",
            "endLonDec",
            "endLatDec",
            "firtStationCode",
            "escapedTfcj",
            "isCylx",
        ):
            assert key in payload
            assert payload[key] is None

    def test_cxzt_crosstime_is_iso_text(self) -> None:
        payload = OdsCxztFwqclls(crosstime=datetime(2025, 9, 18, 0, 0)).to_json_dict()

        # 没有 @JsonFormat 的 Date -> Jackson 的 StdDateFormat：ISO-8601、三位小数、
        # 冒号分隔的偏移量。实测 Java 的 ``loginDate`` 就是
        # ``"2024-05-17T14:15:52.000+08:00"`` 这个形状（见 test_domain_serialization）。
        assert payload["crosstime"] == "2025-09-18T00:00:00.000+08:00"


# --------------------------------------------------------------------------- carTrackQuery


class _FakeTrailMapper:
    def __init__(self) -> None:
        self.cyly_result: List[ZdataTrailTracks] = []
        self.history_result: List[ZdataTrailTracks] = []
        self.calls: List[str] = []

    def get_cyly(self, query: ZdataTrailTracks) -> List[ZdataTrailTracks]:
        self.calls.append("get_cyly")
        return self.cyly_result

    def get_history_trail(self, query: ZdataTrailTracks) -> List[ZdataTrailTracks]:
        self.calls.append("get_history_trail")
        return self.history_result

    def select_list(self, query: Any) -> List[Any]:  # pragma: no cover - unused
        raise AssertionError("carTrackQuery must not call select_list")


class TestCarTrackQuery:
    def test_null_is_cylx_falls_into_the_else_branch(self) -> None:
        mapper = _FakeTrailMapper()
        service = ZdataTrailTracksService(mapper=mapper)

        service.car_track_query(ZdataTrailTracks())

        assert mapper.calls == ["get_history_trail"]

    def test_empty_cyly_does_not_fall_back_to_history(self) -> None:
        mapper = _FakeTrailMapper()
        service = ZdataTrailTracksService(mapper=mapper)

        result = service.car_track_query(ZdataTrailTracks(is_cylx="1"))

        # Java: cylist 为空时 list 保持初始的空 ArrayList，getHistoryTrail 不被调用。
        assert mapper.calls == ["get_cyly"]
        assert result == []

    def test_cyly_hits_rewrite_plate_key_and_set_coordinates(self) -> None:
        mapper = _FakeTrailMapper()
        mapper.cyly_result = [ZdataTrailTracks(uuid="u1", pass_count=3)]
        mapper.history_result = [
            ZdataTrailTracks(
                uuid="u1",
                plate_key="京A12345",
                start_lon="120.123456",
                strat_lat="31.123456",
                end_lon="121.000001",
                end_lat="32.000001",
            )
        ]
        service = ZdataTrailTracksService(mapper=mapper)
        query = ZdataTrailTracks(is_cylx="1")

        result = service.car_track_query(query)

        assert mapper.calls == ["get_cyly", "get_history_trail"]
        assert query.uuid_list == ["u1"]
        assert result[0].plate_key == "京A12345(通行3次)"
        assert result[0].start_lon_dec == pytest.approx(120.123456)
        assert result[0].strat_lat_dec == pytest.approx(31.123456)
        assert result[0].end_lon_dec == pytest.approx(121.000001)
        assert result[0].end_lat_dec == pytest.approx(32.000001)

    def test_unmatched_uuid_keeps_plate_key(self) -> None:
        mapper = _FakeTrailMapper()
        mapper.cyly_result = [ZdataTrailTracks(uuid="u1", pass_count=3)]
        mapper.history_result = [ZdataTrailTracks(uuid="u2", plate_key="京B")]
        service = ZdataTrailTracksService(mapper=mapper)

        result = service.car_track_query(ZdataTrailTracks(is_cylx="1"))

        assert result[0].plate_key == "京B"

    def test_blank_coordinates_are_left_as_null(self) -> None:
        mapper = _FakeTrailMapper()
        mapper.history_result = [ZdataTrailTracks(start_lon="  ", strat_lat="")]
        service = ZdataTrailTracksService(mapper=mapper)

        result = service.car_track_query(ZdataTrailTracks())

        assert result[0].start_lon_dec is None
        assert result[0].strat_lat_dec is None

    def test_start_page_is_consumed_by_get_cyly_when_requested(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """分页只作用于第一条 select —— 与 PageHelper 的 ThreadLocal 一致。"""
        mapper = _FakeTrailMapper()
        mapper.cyly_result = [ZdataTrailTracks(uuid="u1", pass_count=1)]
        seen: List[Optional[Any]] = []
        original = mapper.get_cyly

        def _get_cyly(query: ZdataTrailTracks) -> List[ZdataTrailTracks]:
            seen.append(take_page())
            return original(query)

        monkeypatch.setattr(mapper, "get_cyly", _get_cyly)
        service = ZdataTrailTracksService(mapper=mapper)

        start_page()
        service.car_track_query(ZdataTrailTracks(is_cylx="1"))

        assert seen[0] is not None
        assert take_page() is None
