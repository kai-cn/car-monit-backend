"""base 包一次性补齐的 8 个控制器 —— 路由表 / 权限点 / 装饰与导出行为.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/base/{Geometry,OdsSzdnGantry,OdsSzdnSection,
#   OdsSzdnToll,OdsLwzxsfsjFeeRecords01,OdsLwzxsfsjFeeStationExit01,
#   OdsLwzxsfsjFeeGantryFusion01,OdsRtSzdnSnapshotFlowAddcode}Controller.java

覆盖的重点（Service / Mapper / Forest 客户端由各自文件覆盖）：

* 8 张路由表都完整，且**字面量路由排在路径变量之前**（FastAPI 只看注册顺序）；
* 权限点只有 Java 写了 ``@PreAuthorize`` 的那几个；
* 门架导出的数据源是 **Redis**（不是数据库），空列表时回 200 + 空 body + 无响应头；
* 门架导出的两张 ``toMap`` 没有 merge 函数 —— 主键重复 / 值为 null 直接 500；
* 几何补齐的"泵"：10 个桩号里 ≥7 个有点才继续下一段，≥5 个才入库；
* ``feeStationExit`` 的三条失败分支（``null`` / 缺 ``code`` / ``code != 200``）。
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.base import geometry_controller
from app.api.base import ods_lwzxsfsj_fee_gantry_fusion01_controller as fee_gantry_controller
from app.api.base import ods_lwzxsfsj_fee_station_exit01_controller as fee_exit_controller
from app.api.base import ods_szdn_gantry_controller
from app.api.base import ods_szdn_section_controller
from app.api.base import ods_szdn_toll_controller
from app.base.domain.geometry import Geometry
from app.base.domain.ods_lwzxsfsj_fee_station_exit01 import OdsLwzxsfsjFeeStationExit01
from app.base.domain.ods_szdn_gantry import OdsSzdnGantry
from app.base.domain.ods_szdn_section import OdsSzdnSection
from app.base.domain.ods_szdn_toll import OdsSzdnToll
from app.base.domain.ods_yhgl_v_base_org import OdsYhglVBaseOrg
from app.common.constant.constants import SECTION_LIST, gantry_list, gantry_list_data
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)


# --------------------------------------------------------------------------- 脚手架


class _FakeRedis:
    """``RedisCache`` 的双通道替身：``GET`` 与 ``LRANGE`` 是两种用法."""

    def __init__(
        self,
        objects: Optional[Dict[str, Any]] = None,
        lists: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.objects = objects or {}
        self.lists = lists or {}
        self.reads: List[tuple] = []

    def get_cache_object(self, key: str) -> Any:
        self.reads.append(("object", key))
        return self.objects.get(key)

    def get_cache_list(self, key: str) -> Any:
        self.reads.append(("list", key))
        return self.lists.get(key)


def _build_app(
    router: Any,
    login: bool = True,
    permissions: Optional[set] = None,
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


@pytest.fixture(autouse=True)
def _clean_context() -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    yield
    SecurityContextHolder.clear_context()
    clear_page()
    geometry_controller.reset_geometry_controller()
    ods_szdn_gantry_controller.reset_gantry_controller()
    ods_szdn_section_controller.reset_section_controller()
    ods_szdn_toll_controller.reset_toll_controller()


def _paths(router: Any) -> List[str]:
    return [route.path for route in router.routes]


def _authenticate(permissions: Optional[set] = None) -> None:
    """直调控制器函数时用（不经过 HTTP，带不起中间件）。"""
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


# --------------------------------------------------------------------------- Geometry


class _InlineExecutor:
    """同步执行，让 fire-and-forget 的补齐流程可断言."""

    def __init__(self) -> None:
        self.submitted = 0

    def execute(self, task: Any) -> None:
        self.submitted += 1
        task()


class _FakeHenDa:
    def __init__(self, missing_prefixes: Sequence[str] = ()) -> None:
        self.missing = tuple(missing_prefixes)
        self.piles: List[str] = []

    def get_pile_to_lon_lat(self, road_code: Any, pile: Any, direction: Any) -> Any:
        self.piles.append(pile)
        if isinstance(pile, str) and pile.startswith(self.missing):
            return None
        return {"longitude": "116.5", "latitude": "39.5"}


class _FakeGeometryService:
    def __init__(self) -> None:
        self.saves: List[Geometry] = []
        self.sync_rows: List[Geometry] = []

    def save(self, entity: Geometry) -> AjaxResult:
        self.saves.append(entity)
        return AjaxResult.success()

    def sync_all_geometry(self) -> List[Geometry]:
        return self.sync_rows

    def select_list(self, query: Any) -> List[Geometry]:
        return []

    def select_by_id(self, entity_id: Any) -> Any:
        return None

    def delete_by_ids(self, ids: Sequence[int]) -> AjaxResult:
        return AjaxResult.success_data(len(ids))


class TestGeometryRoutes:
    def test_the_nine_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in geometry_controller.router.routes
        }

        assert registered == {
            ("/base/geometry/getHenDa", ("GET",)),
            ("/base/geometry/syncAllGeometry", ("GET",)),
            ("/base/geometry/syncAllGeometry1", ("GET",)),
            ("/base/geometry/list", ("GET",)),
            ("/base/geometry/export", ("GET",)),
            ("/base/geometry/{ID}", ("GET",)),
            ("/base/geometry", ("POST",)),
            ("/base/geometry", ("PUT",)),
            ("/base/geometry/{IDs}", ("DELETE",)),
        }

    def test_literal_routes_come_before_the_integer_path_variable(self) -> None:
        paths = _paths(geometry_controller.router)
        last_literal = paths.index("/base/geometry/export")

        assert last_literal < paths.index("/base/geometry/{ID}")

    def test_sync_endpoints_need_no_permission_point(self) -> None:
        geometry_controller.reset_geometry_controller(
            geometry_service=_FakeGeometryService(),
            hen_da_service=_FakeHenDa(),
            executor=_InlineExecutor(),
        )
        client = TestClient(_build_app(geometry_controller.router, permissions=set()))

        assert client.get("/base/geometry/syncAllGeometry").json()["code"] == 200
        assert client.get("/base/geometry/list").json()["code"] == 403

    def test_the_path_variable_is_an_integer(self) -> None:
        """``Integer ID`` —— 非数字路径由 FastAPI 422（包在 AjaxResult 里回 200）。"""
        client = TestClient(_build_app(geometry_controller.router))

        assert client.get("/base/geometry/abc").json()["code"] == 500


class TestGeometryPump:
    def test_one_row_per_complete_segment(self) -> None:
        service = _FakeGeometryService()
        hen_da = _FakeHenDa(missing_prefixes=("102",))
        geometry_controller.reset_geometry_controller(
            geometry_service=service, hen_da_service=hen_da, executor=_InlineExecutor()
        )

        geometry_controller.sync_geometry([Geometry(lxbh="G45", lxfx="1", qdzh=100)])

        # 第 1 段 100→101 共 11 个点；第 2 段 101→102 共 10 个点；
        # 第 3 段 102 整段查不到 -> 只有 1 个点，既不入库也停止。
        assert [(row.qdzh, row.zdzh) for row in service.saves] == [(100, 101), (101, 102)]
        assert service.saves[0].paths.count("116.5") == 11
        assert service.saves[1].paths.count("116.5") == 10
        assert len(hen_da.piles) == 3 * 11

    def test_the_segment_boundary_uses_the_next_whole_pile(self) -> None:
        """``i == 10`` 时查的是 ``qdzh + 1``，不是 ``qdzh.10``.

        补齐循环本身是**无界**的（只要每段都能凑到 7 个点就一直跑下去，Java 原样），
        所以这里让整桩号 ``101`` 查不到，第二段只有 1 个点后自然停下。
        """
        hen_da = _FakeHenDa(missing_prefixes=("101",))
        geometry_controller.reset_geometry_controller(
            geometry_service=_FakeGeometryService(),
            hen_da_service=hen_da,
            executor=_InlineExecutor(),
        )

        geometry_controller.sync_geometry([Geometry(lxbh="G45", lxfx="1", qdzh=100)])

        assert hen_da.piles[:11] == [f"100.{i}" for i in range(10)] + ["101"]

    def test_five_points_are_enough_to_save_but_not_to_continue(self) -> None:
        service = _FakeGeometryService()
        geometry_controller.reset_geometry_controller(
            geometry_service=service,
            hen_da_service=_FakeHenDa(missing_prefixes=("100.5", "100.6", "100.7", "100.8", "100.9")),
            executor=_InlineExecutor(),
        )

        geometry_controller.sync_geometry([Geometry(lxbh="G45", lxfx="1", qdzh=100)])

        # 100.0~100.4 + 整桩号 101 = 6 个点 -> 入库，但 count < 7 不再继续
        assert len(service.saves) == 1
        assert service.saves[0].paths.count("116.5") == 6

    def test_fewer_than_five_points_are_dropped(self) -> None:
        service = _FakeGeometryService()
        geometry_controller.reset_geometry_controller(
            geometry_service=service,
            # 100.3~100.9 全部查不到 -> 3 个点 + 整桩号 101 = 4 个，不入库
            hen_da_service=_FakeHenDa(
                missing_prefixes=("100.3", "100.4", "100.5", "100.6", "100.7", "100.8", "100.9")
            ),
            executor=_InlineExecutor(),
        )

        geometry_controller.sync_geometry([Geometry(lxbh="G45", lxfx="1", qdzh=100)])

        assert service.saves == []

    def test_paths_is_deep_to_string(self) -> None:
        assert geometry_controller._deep_to_string([[116.1, 39.1], [116.25, 39.0]]) == (
            "[[116.1, 39.1], [116.25, 39.0]]"
        )

    def test_double_rendering_matches_java(self) -> None:
        render = geometry_controller._java_double_to_string

        assert render(116.1) == "116.1"
        assert render(1.0) == "1.0"
        assert render(-0.0) == "-0.0"
        assert render(0.0) == "0.0"
        assert render(1e-5) == "1.0E-5"
        assert render(1e7) == "1.0E7"
        assert render(math.inf) == "Infinity"
        assert render(math.nan) == "NaN"

    def test_null_starting_pile_fails_at_the_boundary(self) -> None:
        """``qdzh`` 为 null：第一次拼成 ``"null.0"``，到 ``i == 10`` 才拆箱 NPE."""
        service = _FakeGeometryService()
        hen_da = _FakeHenDa()
        geometry_controller.reset_geometry_controller(
            geometry_service=service, hen_da_service=hen_da, executor=_InlineExecutor()
        )

        with pytest.raises(TypeError, match="NullPointerException"):
            geometry_controller.sync_geometry([Geometry(lxbh="G45", lxfx="1", qdzh=None)])

        assert hen_da.piles[0] == "null.0"
        assert service.saves == []


class TestGeometryEndpoints:
    def test_sync_all_returns_success_before_the_work_finishes(self) -> None:
        service = _FakeGeometryService()
        service.sync_rows = [Geometry(lxbh="G45", lxfx="1", qdzh=100)]
        hen_da = _FakeHenDa(missing_prefixes=("100",))
        executor = _InlineExecutor()
        geometry_controller.reset_geometry_controller(
            geometry_service=service, hen_da_service=hen_da, executor=executor
        )

        body = TestClient(_build_app(geometry_controller.router)).get(
            "/base/geometry/syncAllGeometry"
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        assert executor.submitted == 1

    def test_sync_all_geometry1_handles_exactly_one_row(self) -> None:
        service = _FakeGeometryService()
        executor = _InlineExecutor()
        geometry_controller.reset_geometry_controller(
            geometry_service=service,
            # 只补一段就得停，否则 while 循环永远满足 count >= 7
            hen_da_service=_FakeHenDa(missing_prefixes=("100",)),
            executor=executor,
        )

        client = TestClient(_build_app(geometry_controller.router))
        body = client.get("/base/geometry/syncAllGeometry1?lxbh=G45&lxfx=1&qdzh=100").json()

        assert body == {"code": 200, "msg": "操作成功"}
        assert executor.submitted == 1

    def test_get_hen_da_passes_the_payload_into_data(self) -> None:
        geometry_controller.reset_geometry_controller(hen_da_service=_FakeHenDa())

        client = TestClient(_build_app(geometry_controller.router))
        body = client.get("/base/geometry/getHenDa?lxbh=G45&zhStr=100.5&lxfx=1").json()

        assert body["data"] == {"longitude": "116.5", "latitude": "39.5"}

    def test_get_hen_da_omits_data_when_not_found(self) -> None:
        geometry_controller.reset_geometry_controller(hen_da_service=_FakeHenDa(("100",)))

        client = TestClient(_build_app(geometry_controller.router))
        body = client.get("/base/geometry/getHenDa?lxbh=G45&zhStr=100.5").json()

        assert body == {"code": 200, "msg": "操作成功"}


# --------------------------------------------------------------------------- 门架


class _FakeGantryService:
    def __init__(self) -> None:
        self.rows: List[OdsSzdnGantry] = []

    def select_list(self, query: Any) -> List[OdsSzdnGantry]:
        return self.rows

    def select_by_id(self, entity_id: Any) -> Any:
        return None

    def save(self, entity: Any) -> AjaxResult:
        return AjaxResult.success_data(1)

    def delete_by_ids(self, ids: Any) -> AjaxResult:
        return AjaxResult.success_data(1)


class _FakeListService:
    """``tollService.list()`` / ``baseOrgService.list()`` 的替身."""

    def __init__(self, rows: Optional[List[Any]] = None) -> None:
        self.rows = rows or []

    def select_list(self, query: Any) -> List[Any]:
        return self.rows


class TestGantry:
    def test_the_seven_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in ods_szdn_gantry_controller.router.routes
        }

        assert registered == {
            ("/base/gantry/list", ("GET",)),
            ("/base/gantry/listAll", ("GET",)),
            ("/base/gantry/export", ("GET",)),
            ("/base/gantry/{id}", ("GET",)),
            ("/base/gantry", ("POST",)),
            ("/base/gantry", ("PUT",)),
            ("/base/gantry/{ids}", ("DELETE",)),
        }

    def test_list_fills_road_and_section_names_from_redis(self) -> None:
        service = _FakeGantryService()
        service.rows = [OdsSzdnGantry(gantry_code="G001", road_code="G45", section_code="S1")]
        redis = _FakeRedis(
            lists={SECTION_LIST: [OdsSzdnSection(road_code="G45", road_name="大广高速", section_code="S1", section_name="吉安段")]}
        )
        ods_szdn_gantry_controller.reset_gantry_controller(service=service, redis_cache=redis)

        body = TestClient(_build_app(ods_szdn_gantry_controller.router)).get(
            "/base/gantry/list"
        ).json()

        row = body["rows"][0]
        assert row["roadName"] == "大广高速"
        assert row["sectionName"] == "吉安段"

    def test_list_defaults_to_empty_string_when_redis_is_empty(self) -> None:
        service = _FakeGantryService()
        service.rows = [OdsSzdnGantry(gantry_code="G001", road_code="G45", section_code="S1")]
        ods_szdn_gantry_controller.reset_gantry_controller(
            service=service, redis_cache=_FakeRedis()
        )

        body = TestClient(_build_app(ods_szdn_gantry_controller.router)).get(
            "/base/gantry/list"
        ).json()

        assert body["rows"][0]["roadName"] == ""
        assert body["rows"][0]["sectionName"] == ""

    def test_export_with_an_empty_redis_list_writes_nothing(self) -> None:
        ods_szdn_gantry_controller.reset_gantry_controller(
            redis_cache=_FakeRedis(objects={gantry_list: []})
        )

        response = TestClient(_build_app(ods_szdn_gantry_controller.router)).get(
            "/base/gantry/export"
        )

        assert response.status_code == 200
        assert response.content == b""
        assert "content-disposition" not in response.headers

    def _reset_for_export(self, gantries: List[OdsSzdnGantry], tolls: List[OdsSzdnToll]) -> None:
        service = _FakeGantryService()
        service.rows = gantries
        ods_szdn_gantry_controller.reset_gantry_controller(
            service=service,
            redis_cache=_FakeRedis(
                objects={gantry_list: gantries},
                lists={
                    SECTION_LIST: [
                        OdsSzdnSection(road_code="G45", road_name="大广高速", section_code="S1", section_name="吉安段")
                    ]
                },
            ),
            toll_service=_FakeListService(tolls),
            base_org_service=_FakeListService([OdsYhglVBaseOrg(org_code="O1", org_name="吉安中心")]),
        )

    def test_export_renders_the_template_and_sets_the_two_headers(self) -> None:
        gantry = OdsSzdnGantry(
            gantry_code="G001",
            road_code="G45",
            section_code="S1",
            toll_code="T1",
            org_code="O1",
            boundary_gantry_type="0",
            is_virtual="1",
        )
        self._reset_for_export([gantry], [OdsSzdnToll(toll_code="T1", toll_name="吉安收费站")])

        response = TestClient(_build_app(ods_szdn_gantry_controller.router)).get(
            "/base/gantry/export"
        )

        assert response.content[:2] == b"PK"  # xlsx = zip
        assert response.headers["content-type"] == "application/octet-stream;charset=UTF-8"
        assert response.headers["content-disposition"] == "attachment"

    def test_export_translates_the_three_flag_columns(self) -> None:
        entry = OdsSzdnGantry(
            gantry_code="G001",
            road_code="G45",
            section_code="S1",
            toll_code="T1",
            org_code="O1",
            boundary_gantry_type="0",
            is_virtual="1",
        )
        exit_gantry = OdsSzdnGantry(
            gantry_code="G002",
            road_code="G45",
            section_code="S1",
            toll_code="T1",
            org_code="O1",
            boundary_gantry_type="1",
            is_virtual="0",
        )
        self._reset_for_export([entry, exit_gantry], [OdsSzdnToll(toll_code="T1", toll_name="吉安收费站")])
        # Java: 缓存里有计数值 -> isData = "是"
        ods_szdn_gantry_controller._collaborators()["redis_cache"].objects[
            gantry_list_data + "G001"
        ] = "3"

        TestClient(_build_app(ods_szdn_gantry_controller.router)).get("/base/gantry/export")

        # "0".equals(...) 才是"否"，其余（包括 "1" 和 null）一律"是"
        assert entry.boundary_gantry_type == "边界入口门架"
        assert entry.is_virtual == "是"
        assert entry.is_data == "是"
        assert entry.toll_name == "吉安收费站"
        assert entry.org_name == "吉安中心"

        assert exit_gantry.boundary_gantry_type == "边界出口门架"
        assert exit_gantry.is_virtual == "否"
        assert exit_gantry.is_data == "否"

    def test_export_blows_up_on_a_duplicate_toll_code(self) -> None:
        """``Collectors.toMap`` 没有 merge 函数 —— 重复主键是 500，不是"后者覆盖".

        直调控制器函数：``AttributeError`` 不在 ``RuntimeError`` 的 MRO 里，
        装到 HTTP 上会被 ``ServerErrorMiddleware`` 重抛（见 ``COMPATIBILITY.md`` §25.3），
        而 Java 这里是 ``IllegalStateException`` -> 500。两边都是 500，只是信封形态不同。
        """
        gantry = OdsSzdnGantry(gantry_code="G001", road_code="G45", toll_code="T1", org_code="O1")
        self._reset_for_export(
            [gantry],
            [OdsSzdnToll(toll_code="T1", toll_name="甲"), OdsSzdnToll(toll_code="T1", toll_name="乙")],
        )
        _authenticate()

        with pytest.raises(AttributeError, match="Duplicate key"):
            ods_szdn_gantry_controller.export(OdsSzdnGantry())

    def test_export_blows_up_on_a_null_toll_name(self) -> None:
        gantry = OdsSzdnGantry(gantry_code="G001", road_code="G45", toll_code="T1", org_code="O1")
        self._reset_for_export([gantry], [OdsSzdnToll(toll_code="T1", toll_name=None)])
        _authenticate()

        with pytest.raises(TypeError, match="NullPointerException"):
            ods_szdn_gantry_controller.export(OdsSzdnGantry())


# --------------------------------------------------------------------------- 路段 / 收费站


class _FakeSectionService(_FakeGantryService):
    pass


class TestSectionAndToll:
    def test_section_route_table(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in ods_szdn_section_controller.router.routes
        }

        assert len(registered) == 7
        assert ("/base/section/listAll", ("GET",)) in registered

    def test_toll_route_table(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in ods_szdn_toll_controller.router.routes
        }

        assert len(registered) == 7
        assert ("/base/toll/listAll", ("GET",)) in registered

    def test_section_export_returns_a_filename_in_msg(self) -> None:
        service = _FakeSectionService()
        service.rows = [OdsSzdnSection(section_code="S1", section_name="吉安段")]
        ods_szdn_section_controller.reset_section_controller(service=service)

        body = TestClient(_build_app(ods_szdn_section_controller.router)).get(
            "/base/section/export"
        ).json()

        assert body["code"] == 200
        assert body["msg"].endswith(".xlsx")
        assert "data" not in body

    def test_toll_list_fills_the_section_name(self) -> None:
        service = _FakeGantryService()
        service.rows = [OdsSzdnToll(toll_code="T1", section_code="S1")]
        redis = _FakeRedis(
            lists={SECTION_LIST: [OdsSzdnSection(road_code="G45", road_name="大广高速", section_code="S1", section_name="吉安段")]}
        )
        ods_szdn_toll_controller.reset_toll_controller(service=service, redis_cache=redis)

        body = TestClient(_build_app(ods_szdn_toll_controller.router)).get(
            "/base/toll/list"
        ).json()

        assert body["rows"][0]["sectionName"] == "吉安段"

    def test_toll_list_still_builds_the_unused_road_map(self) -> None:
        """``roadMap`` 是死代码，但它的 ``toMap`` 仍会因 null 值 NPE."""
        service = _FakeGantryService()
        service.rows = []
        redis = _FakeRedis(lists={SECTION_LIST: [OdsSzdnSection(road_code="G45", road_name=None)]})
        ods_szdn_toll_controller.reset_toll_controller(service=service, redis_cache=redis)
        _authenticate()

        with pytest.raises(TypeError, match="NullPointerException"):
            ods_szdn_toll_controller.list_tolls(OdsSzdnToll())


# --------------------------------------------------------------------------- Forest 代理型


class _FakeFeeExitClient:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.queries: List[Any] = []

    def get_ods_lwzxsfsj_fee_station_exit01_page(self, query: Any) -> Any:
        self.queries.append(query)
        return self.payload

    def select_ods_lwzxsfsj_fee_station_exit01_by_id(self, big_id: Any) -> Any:
        return {"bigId": big_id}


class TestFeeStationExit:
    @pytest.fixture
    def client(self, monkeypatch: pytest.MonkeyPatch) -> Any:
        """``_client()`` 返回假 Forest 客户端；具体 payload 由用例自己定."""

        def _install(payload: Any) -> _FakeFeeExitClient:
            fake = _FakeFeeExitClient(payload)
            monkeypatch.setattr(fee_exit_controller, "_client", lambda: fake)
            return fake

        return _install

    def test_defaults_are_filled_before_the_remote_call(self, client: Any) -> None:
        fake = client({"code": 200, "msg": "查询成功", "total": 1, "rows": [{"bigId": "1"}]})

        body = TestClient(_build_app(fee_exit_controller.router)).get(
            "/base/feestationexit/list"
        ).json()

        assert body["code"] == 200
        assert body["total"] == 1
        assert fake.queries[0].page_num == 1
        assert fake.queries[0].page_size == 10

    def test_a_null_payload_becomes_a_service_exception(self, client: Any) -> None:
        client(None)

        body = TestClient(_build_app(fee_exit_controller.router)).get(
            "/base/feestationexit/list"
        ).json()

        assert body == {"code": 500, "msg": fee_exit_controller.FETCH_ERROR_MESSAGE}

    def test_a_non_200_code_becomes_a_service_exception(self, client: Any) -> None:
        client({"code": 500, "msg": "上游炸了"})

        body = TestClient(_build_app(fee_exit_controller.router)).get(
            "/base/feestationexit/list"
        ).json()

        assert body == {"code": 500, "msg": fee_exit_controller.FETCH_ERROR_MESSAGE}

    def test_a_missing_code_is_a_null_pointer_not_a_service_exception(self, client: Any) -> None:
        client({"msg": "没有 code"})
        _authenticate()

        with pytest.raises(TypeError, match="NullPointerException"):
            fee_exit_controller.list_fee_station_exits(OdsLwzxsfsjFeeStationExit01())

    def test_get_info_passes_through(self, client: Any) -> None:
        client(None)

        body = TestClient(_build_app(fee_exit_controller.router)).get(
            "/base/feestationexit/abc"
        ).json()

        assert body["data"] == {"bigId": "abc"}


class _FakeFeeGantryClient:
    def __init__(self) -> None:
        self.queries: List[Any] = []

    def get_ods_lwzxsfsj_fee_gantry_fusion01_page(self, query: Any) -> Any:
        self.queries.append(query)
        return _table_data_info()

    def select_ods_lwzxsfsj_fee_gantry_fusion01_by_id(self, big_id: Any) -> Any:
        return {"bigId": big_id}


def _table_data_info() -> Any:
    from app.common.core.page.table_data_info import TableDataInfo

    info = TableDataInfo()
    info.set_total(2)
    info.set_rows([{"bigId": "1"}, {"bigId": "2"}])
    info.set_code(200)
    info.set_msg("查询成功")
    return info


class TestFeeGantry:
    def test_the_two_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in fee_gantry_controller.router.routes
        }

        assert registered == {
            ("/base/feeGantry/list", ("GET",)),
            ("/base/feeGantry/{big_id}", ("GET",)),
        }

    def test_list_returns_the_remote_envelope_verbatim(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _FakeFeeGantryClient()
        monkeypatch.setattr(fee_gantry_controller, "_client", lambda: fake)

        body = TestClient(_build_app(fee_gantry_controller.router)).get(
            "/base/feeGantry/list"
        ).json()

        assert body == {"total": 2, "rows": [{"bigId": "1"}, {"bigId": "2"}], "code": 200, "msg": "查询成功"}
        assert fake.queries[0].page_num == 1
        assert fake.queries[0].page_size == 10

    def test_list_has_a_permission_point(self) -> None:
        client = TestClient(
            _build_app(fee_gantry_controller.router, permissions={"base:feeGantry:export"})
        )

        assert client.get("/base/feeGantry/list").json()["code"] == 403
