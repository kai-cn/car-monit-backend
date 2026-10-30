"""manager 分组（车辆监控业务）的 HTTP 契约测试.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/manager/{BussTest,CarAduitFree,CarConfimFree,
#   CarExceptRecord,CarFeeRecord,CarInfo,CarQueryLog,CarRouteDetail,CarRouteInfo,
#   CarSplitRecord,CarSuspicious,CarSuspiciousBack,CarSuspiciousCheck,CarTrackInfo,
#   CarWarningInfo,CarWarningRule,CarWhiteInfo,GantryCar,GantryTradeInfo}Controller.java

覆盖的重点（Mapper / Service 由各自文件覆盖）：

* 19 张路由表都完整，且每个路由里的 ``GET /{id}`` 都**排在所有静态 GET 之后**
  —— FastAPI 只看注册顺序，Java 是"精确路径优先"，这一条是本组最容易踩的坑
  （``CarQueryLogController`` 在 Java 里就是把 ``export`` 写在 ``getInfo`` 之后）；
* 权限点只有 Java 写了 ``@PreAuthorize`` 的那几个 —— ``getInfo`` 全部无权限点；
* ``listCarNo`` / ``listCount`` / ``incomeDetailList`` 在关键字段为空时把条件
  改成 ``"-1"``（查不到数据），而不是"不过滤"；
* 模板导出是 Java 的 ``return null`` 风格：渲染抛异常时回**空 body + 无响应头**；
* ``CarQueryLog`` 的导出中 ``menuPoint`` / ``modelType`` 走字典，``createTime`` 不转。
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import Response

from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.manager.domain.car_aduit_free import CarAduitFree
from app.manager.domain.car_confim_free import CarConfimFree
from app.manager.domain.car_query_log import CarQueryLog

MANAGER_PACKAGE = "app.api.manager"

#: ``模块名 -> {(path, (method, ...))}`` —— 逐条抄自 19 个 Java 控制器的映射表。
ROUTE_TABLES: Dict[str, Set[Tuple[str, Tuple[str, ...]]]] = {
    "buss_test_controller": {
        ("/manager/busstest/list", ("GET",)),
        ("/manager/busstest/export", ("GET",)),
        ("/manager/busstest/{id}", ("GET",)),
        ("/manager/busstest", ("POST",)),
        ("/manager/busstest", ("PUT",)),
        ("/manager/busstest/{ids}", ("DELETE",)),
        ("/manager/busstest/syncCurrentTrack", ("POST",)),
    },
    "car_aduit_free_controller": {
        ("/manager/aduitfree/list", ("GET",)),
        ("/manager/aduitfree/export", ("GET",)),
        ("/manager/aduitfree/incomeStatics", ("GET",)),
        ("/manager/aduitfree/exportIncomeStatics", ("GET",)),
        ("/manager/aduitfree/incomeDetailList", ("GET",)),
        ("/manager/aduitfree/exportIncomeDetailList", ("GET",)),
        ("/manager/aduitfree/{id}", ("GET",)),
        ("/manager/aduitfree", ("POST",)),
        ("/manager/aduitfree", ("PUT",)),
        ("/manager/aduitfree/{ids}", ("DELETE",)),
    },
    "car_confim_free_controller": {
        ("/manager/confimfree/list", ("GET",)),
        ("/manager/confimfree/listCarNo", ("GET",)),
        ("/manager/confimfree/listCount", ("GET",)),
        ("/manager/confimfree/export", ("GET",)),
        ("/manager/confimfree/exportConcernedList", ("GET",)),
        ("/manager/confimfree/concernedList", ("GET",)),
        ("/manager/confimfree/except/{except_ids}", ("GET",)),
        ("/manager/confimfree/carStatics", ("GET",)),
        ("/manager/confimfree/exportCarStatics", ("GET",)),
        ("/manager/confimfree/{id}", ("GET",)),
        ("/manager/confimfree", ("POST",)),
        ("/manager/confimfree", ("PUT",)),
        ("/manager/confimfree/{ids}", ("DELETE",)),
    },
    "car_except_record_controller": {
        ("/manager/exceptrecord/list", ("GET",)),
        ("/manager/exceptrecord/listCarNo", ("GET",)),
        ("/manager/exceptrecord/listCarOrgId", ("GET",)),
        ("/manager/exceptrecord/listExceptId", ("GET",)),
        ("/manager/exceptrecord/exceptRecordCount", ("GET",)),
        ("/manager/exceptrecord/exportOrgId", ("GET",)),
        ("/manager/exceptrecord/export", ("GET",)),
        ("/manager/exceptrecord/getConfirmId/{id}", ("GET",)),
        ("/manager/exceptrecord/{id}", ("GET",)),
        ("/manager/exceptrecord", ("POST",)),
        ("/manager/exceptrecord", ("PUT",)),
        ("/manager/exceptrecord/{ids}", ("DELETE",)),
        ("/manager/exceptrecord/import", ("POST",)),
    },
    "car_fee_record_controller": {
        ("/manager/feerecord/list", ("GET",)),
        ("/manager/feerecord/export", ("GET",)),
        ("/manager/feerecord/{id}", ("GET",)),
        ("/manager/feerecord", ("POST",)),
        ("/manager/feerecord", ("PUT",)),
        ("/manager/feerecord/{ids}", ("DELETE",)),
    },
    "car_info_controller": {
        ("/manager/carinfo/list", ("GET",)),
        ("/manager/carinfo/listAll", ("GET",)),
        ("/manager/carinfo/export", ("GET",)),
        ("/manager/carinfo/{id}", ("GET",)),
        ("/manager/carinfo", ("POST",)),
        ("/manager/carinfo", ("PUT",)),
        ("/manager/carinfo/{ids}", ("DELETE",)),
        ("/manager/carinfo/import", ("POST",)),
    },
    "car_query_log_controller": {
        ("/manager/querylog/list", ("GET",)),
        ("/manager/querylog/export", ("GET",)),
        ("/manager/querylog/{id}", ("GET",)),
        ("/manager/querylog", ("POST",)),
        ("/manager/querylog", ("PUT",)),
        ("/manager/querylog/{ids}", ("DELETE",)),
    },
    "car_route_detail_controller": {
        ("/manager/routedetail/list", ("GET",)),
        ("/manager/routedetail/export", ("GET",)),
        ("/manager/routedetail/{id}", ("GET",)),
        ("/manager/routedetail", ("POST",)),
        ("/manager/routedetail", ("PUT",)),
        ("/manager/routedetail/{ids}", ("DELETE",)),
    },
    "car_route_info_controller": {
        ("/manager/routeinfo/list", ("GET",)),
        ("/manager/routeinfo/export", ("GET",)),
        ("/manager/routeinfo/{id}", ("GET",)),
        ("/manager/routeinfo", ("POST",)),
        ("/manager/routeinfo", ("PUT",)),
        ("/manager/routeinfo/{ids}", ("DELETE",)),
    },
    "car_split_record_controller": {
        ("/manager/splitrecord/list", ("GET",)),
        ("/manager/splitrecord/export", ("GET",)),
        ("/manager/splitrecord/{id}", ("GET",)),
        ("/manager/splitrecord", ("POST",)),
        ("/manager/splitrecord", ("PUT",)),
        ("/manager/splitrecord/{ids}", ("DELETE",)),
    },
    "car_suspicious_back_controller": {
        ("/manager/carsuspiciousback/list", ("GET",)),
        ("/manager/carsuspiciousback/export", ("GET",)),
        ("/manager/carsuspiciousback/{id}", ("GET",)),
        ("/manager/carsuspiciousback", ("POST",)),
        ("/manager/carsuspiciousback", ("PUT",)),
        ("/manager/carsuspiciousback/{ids}", ("DELETE",)),
    },
    "car_suspicious_check_controller": {
        ("/manager/suspiciouscheck/list", ("GET",)),
        ("/manager/suspiciouscheck/export", ("GET",)),
        ("/manager/suspiciouscheck/{id}", ("GET",)),
        ("/manager/suspiciouscheck", ("POST",)),
        ("/manager/suspiciouscheck", ("PUT",)),
        ("/manager/suspiciouscheck/{ids}", ("DELETE",)),
    },
    "car_suspicious_controller": {
        ("/manager/suspicious/list", ("GET",)),
        ("/manager/suspicious/listCarNo", ("GET",)),
        ("/manager/suspicious/listFileCarNo", ("GET",)),
        ("/manager/suspicious/listAll", ("GET",)),
        ("/manager/suspicious/exportAbnormalPassage", ("GET",)),
        ("/manager/suspicious/export", ("GET",)),
        ("/manager/suspicious/exportHistory", ("GET",)),
        ("/manager/suspicious/listHistory", ("GET",)),
        ("/manager/suspicious/history/{id}", ("GET",)),
        ("/manager/suspicious/{id}", ("GET",)),
        ("/manager/suspicious", ("POST",)),
        ("/manager/suspicious", ("PUT",)),
        ("/manager/suspicious/check", ("PUT",)),
        ("/manager/suspicious/syncSuspiciousCarTask", ("POST",)),
        ("/manager/suspicious/{ids}", ("DELETE",)),
    },
    "car_track_info_controller": {
        ("/manager/cartrackinfo/list", ("GET",)),
        ("/manager/cartrackinfo/listByCarId", ("GET",)),
        ("/manager/cartrackinfo/listByCarByTime", ("GET",)),
        ("/manager/cartrackinfo/changeTrailInfo", ("PUT",)),
        ("/manager/cartrackinfo/carSnapShot", ("GET",)),
        ("/manager/cartrackinfo/export", ("GET",)),
        ("/manager/cartrackinfo/{id}", ("GET",)),
        ("/manager/cartrackinfo", ("POST",)),
        ("/manager/cartrackinfo", ("PUT",)),
        ("/manager/cartrackinfo/{ids}", ("DELETE",)),
    },
    "car_warning_info_controller": {
        ("/manager/carwarning/list", ("GET",)),
        ("/manager/carwarning/export", ("GET",)),
        ("/manager/carwarning/{id}", ("GET",)),
        ("/manager/carwarning", ("POST",)),
        ("/manager/carwarning", ("PUT",)),
        ("/manager/carwarning/{ids}", ("DELETE",)),
    },
    "car_warning_rule_controller": {
        ("/manager/warningrule/list", ("GET",)),
        ("/manager/warningrule/export", ("GET",)),
        ("/manager/warningrule/{id}", ("GET",)),
        ("/manager/warningrule", ("POST",)),
        ("/manager/warningrule", ("PUT",)),
        ("/manager/warningrule/{ids}", ("DELETE",)),
    },
    "car_white_info_controller": {
        ("/manager/whiteinfo/list", ("GET",)),
        ("/manager/whiteinfo/export", ("GET",)),
        ("/manager/whiteinfo/{id}", ("GET",)),
        ("/manager/whiteinfo", ("POST",)),
        ("/manager/whiteinfo", ("PUT",)),
        ("/manager/whiteinfo/{ids}", ("DELETE",)),
    },
    "gantry_car_controller": {
        ("/manager/gantrycar/list", ("GET",)),
        ("/manager/gantrycar/export", ("GET",)),
        ("/manager/gantrycar/{id}", ("GET",)),
        ("/manager/gantrycar", ("POST",)),
        ("/manager/gantrycar", ("PUT",)),
        ("/manager/gantrycar/{ids}", ("DELETE",)),
    },
    "gantry_trade_info_controller": {
        ("/manager/gantrytrade/list", ("GET",)),
        ("/manager/gantrytrade/export", ("GET",)),
        ("/manager/gantrytrade/{id}", ("GET",)),
        ("/manager/gantrytrade", ("POST",)),
        ("/manager/gantrytrade", ("PUT",)),
        ("/manager/gantrytrade/{ids}", ("DELETE",)),
    },
}


# --------------------------------------------------------------------------- 脚手架


def _module(name: str) -> Any:
    return importlib.import_module(f"{MANAGER_PACKAGE}.{name}")


def _build_app(router: Any, permissions: Optional[Set[str]] = None) -> FastAPI:
    """带假 JWT 的应用：中间件直接把登录用户塞进 ``SecurityContextHolder``."""
    application = FastAPI()
    register_exception_handlers(application)

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


class _FakeService:
    """记录调用参数的替身 —— 只实现测试真正会碰到的那几个方法."""

    def __init__(self, rows: Optional[List[Any]] = None) -> None:
        self.rows = rows if rows is not None else []
        self.calls: List[Tuple[str, Any]] = []

    def select_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_list", query))
        return self.rows

    def select_by_id(self, entity_id: Any) -> Any:
        self.calls.append(("select_by_id", entity_id))
        return None

    def save(self, entity: Any) -> AjaxResult:
        self.calls.append(("save", entity))
        return AjaxResult.success()

    def delete_by_ids(self, ids: Any) -> AjaxResult:
        self.calls.append(("delete_by_ids", ids))
        return AjaxResult.success()

    def select_concerned_list(self, query: Any) -> List[Any]:
        self.calls.append(("select_concerned_list", query))
        return self.rows

    def list_count(self, query: Any) -> Any:
        self.calls.append(("list_count", query))
        return {"confimFreeNum": 0}

    def select_by_except_ids(self, except_ids: Any) -> AjaxResult:
        self.calls.append(("select_by_except_ids", except_ids))
        return AjaxResult.success()

    def get_car_statistics(self, param: Any) -> List[Any]:
        self.calls.append(("get_car_statistics", param))
        return []

    def get_pc_car_statistics(self, query_ro: Any) -> List[Any]:
        self.calls.append(("get_pc_car_statistics", query_ro))
        return []

    def get_pc_income_statics(self, query_ro: Any) -> List[Any]:
        self.calls.append(("get_pc_income_statics", query_ro))
        return []

    def income_detail_list(self, query: Any) -> List[Any]:
        self.calls.append(("income_detail_list", query))
        return []


def _inject(monkeypatch: Any, module: Any, service: Any) -> None:
    """跳过 ``_service()`` 的单例，直接把替身挂在模块级 ``_SERVICE`` 上."""

    def _fake() -> Any:
        return service

    monkeypatch.setattr(module, "_SERVICE", service)
    monkeypatch.setattr(module, "_service", _fake)


def _dict_service(mapping: Dict[str, Dict[str, str]]) -> Any:
    class _FakeDictService:
        def select_dict_data_map(self, dict_type: str) -> Dict[str, str]:
            return mapping.get(dict_type, {})

    return _FakeDictService()


def _boom(*_args: Any, **_kwargs: Any) -> Any:
    raise RuntimeError("template exploded")


# --------------------------------------------------------------------------- 路由表


@pytest.mark.parametrize("module_name", sorted(ROUTE_TABLES))
def test_the_route_table_matches_the_java_mappings(module_name: str) -> None:
    router = _module(module_name).router

    registered = {(route.path, tuple(sorted(route.methods))) for route in router.routes}

    assert registered == ROUTE_TABLES[module_name]


@pytest.mark.parametrize("module_name", sorted(ROUTE_TABLES))
def test_the_single_segment_path_variable_is_declared_last(module_name: str) -> None:
    """``GET /{id}`` 必须排在所有静态 GET 之后，否则 ``/export`` 会被当成主键."""
    router = _module(module_name).router
    paths = [route.path for route in router.routes]
    catch_all = f"{router.prefix}/{{id}}"

    if catch_all not in paths:
        pytest.skip(f"{module_name} 没有单段路径变量")

    position = paths.index(catch_all)
    getters = [
        index
        for index, route in enumerate(router.routes)
        if "GET" in route.methods and route.path != catch_all
    ]

    assert all(index < position for index in getters), paths


# --------------------------------------------------------------------------- 权限点


def test_a_template_controller_keeps_its_permission_points(monkeypatch: Any) -> None:
    """``CarFeeRecordController``：``getInfo`` 是全组唯一没有权限点的那个."""
    module = _module("car_fee_record_controller")
    _inject(monkeypatch, module, _FakeService())
    client = TestClient(_build_app(module.router, permissions=set()))

    assert client.get("/manager/feerecord/list").json()["code"] == 403
    assert client.get("/manager/feerecord/export").json()["code"] == 403
    assert client.post("/manager/feerecord", json={}).json()["code"] == 403
    # getInfo 没有 @PreAuthorize -> 只要登录就放行
    assert client.get("/manager/feerecord/1").json()["code"] == 200


def test_confirm_and_aduit_free_need_login_only() -> None:
    """两个定制控制器引了 ``@PreAuthorize`` 但**一个都没用** —— 空权限集也应 200."""
    for module_name, path in (
        ("car_confim_free_controller", "/manager/confimfree/list"),
        ("car_aduit_free_controller", "/manager/aduitfree/list"),
    ):
        module = _module(module_name)
        monkeypatch = pytest.MonkeyPatch()
        try:
            _inject(monkeypatch, module, _FakeService())
            client = TestClient(_build_app(module.router, permissions=set()))

            assert client.get(path).json()["code"] == 200
        finally:
            monkeypatch.undo()


# --------------------------------------------------------------------------- 确认补缴


def test_list_car_no_replaces_a_blank_plate_with_minus_one(monkeypatch: Any) -> None:
    module = _module("car_confim_free_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.get("/manager/confimfree/listCarNo")

    assert service.calls[-1][1].car_no == "-1"


def test_list_count_replaces_a_blank_plate_with_minus_one(monkeypatch: Any) -> None:
    module = _module("car_confim_free_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.get("/manager/confimfree/listCount")

    assert service.calls[-1][1].car_no == "-1"


def test_list_car_no_keeps_a_supplied_plate(monkeypatch: Any) -> None:
    module = _module("car_confim_free_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.get("/manager/confimfree/listCarNo", params={"carNo": "京A12345"})

    assert service.calls[-1][1].car_no == "京A12345"


def test_except_ids_are_passed_through_verbatim(monkeypatch: Any) -> None:
    module = _module("car_confim_free_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    assert client.get("/manager/confimfree/except/1,2,3").json()["code"] == 200

    assert service.calls[-1] == ("select_by_except_ids", "1,2,3")


def test_export_translates_car_type_and_car_vehicle(monkeypatch: Any) -> None:
    module = _module("car_confim_free_controller")
    # escaped_type 在这个接口里**不**翻字典（只有 exportConcernedList 才翻）
    rows = [CarConfimFree(car_type="1", car_vehicle="2", escaped_type="a,b")]
    _inject(monkeypatch, module, _FakeService(rows=rows))
    monkeypatch.setattr(
        module,
        "get_dict_data_service",
        lambda: _dict_service(
            {
                "car_type": {"1": "小型车"},
                "car_vehicle": {"2": "客车"},
                "escaped_type": {"a": "甲", "b": "乙"},
            }
        ),
    )
    captured: Dict[str, Any] = {}

    def _capture(template: str, exported: Any) -> Response:
        captured["template"] = template
        captured["rows"] = exported
        return Response(content=b"ok")

    monkeypatch.setattr(module, "_export_excel", _capture)

    client = TestClient(_build_app(module.router))
    assert client.get("/manager/confimfree/export").content == b"ok"

    assert captured["template"] == "templates/export/carConfirm.xlsx"
    assert captured["rows"][0].car_type == "小型车"
    assert captured["rows"][0].car_vehicle == "客车"
    assert captured["rows"][0].escaped_type == "a,b"


def test_export_concerned_list_translates_escaped_types(monkeypatch: Any) -> None:
    """``exportConcernedList`` 额外把逗号分隔的 ``escapedType`` 逐个翻成标签,

    未命中字典的值**丢弃**，最后 ``deleteEnd`` 掉尾逗号。
    """
    module = _module("car_confim_free_controller")
    rows = [CarConfimFree(escaped_type="a,zzz,b,")]
    _inject(monkeypatch, module, _FakeService(rows=rows))
    monkeypatch.setattr(
        module,
        "get_dict_data_service",
        lambda: _dict_service({"escaped_type": {"a": "甲", "b": "乙"}}),
    )
    captured: Dict[str, Any] = {}

    def _capture(template: str, exported: Any) -> Response:
        captured["template"] = template
        captured["rows"] = exported
        return Response(content=b"ok")

    monkeypatch.setattr(module, "_export_excel", _capture)

    client = TestClient(_build_app(module.router))
    assert client.get("/manager/confimfree/exportConcernedList").content == b"ok"

    assert captured["template"] == "templates/export/concernedList.xlsx"
    # zzz 没有字典项 -> 丢弃；尾逗号被 deleteEnd 去掉
    assert captured["rows"][0].escaped_type == "甲,乙"


def test_a_failing_template_render_returns_an_empty_body(monkeypatch: Any) -> None:
    """Java: 先渲染、后设响应头 —— 渲染炸了就只有空 body，连响应头都没有."""
    module = _module("car_confim_free_controller")
    _inject(monkeypatch, module, _FakeService(rows=[]))
    monkeypatch.setattr(module, "get_dict_data_service", lambda: _dict_service({}))
    monkeypatch.setattr(module, "TemplateExportParams", _boom)

    client = TestClient(_build_app(module.router))
    response = client.get("/manager/confimfree/exportCarStatics")

    assert response.status_code == 200
    assert response.content == b""
    assert "content-disposition" not in response.headers


# --------------------------------------------------------------------------- 补缴处理


def test_income_detail_list_replaces_a_blank_org_with_minus_one(monkeypatch: Any) -> None:
    module = _module("car_aduit_free_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.get("/manager/aduitfree/incomeDetailList")

    assert [name for name, _ in service.calls] == ["income_detail_list"]
    assert service.calls[-1][1].org_id == "-1"


def test_income_detail_list_keeps_a_supplied_org(monkeypatch: Any) -> None:
    module = _module("car_aduit_free_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)

    client = TestClient(_build_app(module.router))
    client.get("/manager/aduitfree/incomeDetailList", params={"orgId": "100"})

    assert service.calls[-1][1].org_id == "100"


def test_aduit_export_goes_through_excel_util(monkeypatch: Any) -> None:
    """``export`` 走 ``ExcelUtil<CarAduitFree>``：返回体只有 ``msg``（文件名）."""
    module = _module("car_aduit_free_controller")
    _inject(monkeypatch, module, _FakeService(rows=[CarAduitFree(id="f-1")]))

    client = TestClient(_build_app(module.router))
    body = client.get("/manager/aduitfree/export").json()

    assert body["code"] == 200
    assert "data" not in body
    assert body["msg"].endswith("_补缴处理数据.xlsx")


def test_the_two_income_exports_pick_different_templates(monkeypatch: Any) -> None:
    module = _module("car_aduit_free_controller")
    _inject(monkeypatch, module, _FakeService(rows=[]))
    captured: List[str] = []

    def _capture(template: str, exported: Any) -> Response:
        captured.append(template)
        return Response(content=b"ok")

    monkeypatch.setattr(module, "_export_excel", _capture)

    client = TestClient(_build_app(module.router))
    client.get("/manager/aduitfree/exportIncomeStatics")
    client.get("/manager/aduitfree/exportIncomeDetailList")

    assert captured == [
        "templates/export/incomeStatics.xlsx",
        "templates/export/exportIncomeDetailList.xlsx",
    ]


# --------------------------------------------------------------------------- 查询日志


def test_the_export_path_is_not_swallowed_by_the_id_route(monkeypatch: Any) -> None:
    """Java 里 ``export`` 声明在 ``getInfo`` 之后，FastAPI 必须调换顺序."""
    module = _module("car_query_log_controller")
    service = _FakeService()
    _inject(monkeypatch, module, service)
    monkeypatch.setattr(module, "get_dict_data_service", lambda: _dict_service({}))
    # 渲染空列表也会落盘（表头行），这里只关心是哪个 service 方法被调到
    monkeypatch.setattr(module, "TemplateExportParams", _boom)

    client = TestClient(_build_app(module.router))
    response = client.get("/manager/querylog/export")

    assert response.content == b""
    called = [name for name, _ in service.calls]
    assert "select_list" in called
    assert "select_by_id" not in called


def test_query_log_export_translates_both_dictionaries(monkeypatch: Any) -> None:
    module = _module("car_query_log_controller")
    rows = [CarQueryLog(menu_point="p", model_type="m")]
    _inject(monkeypatch, module, _FakeService(rows=rows))
    monkeypatch.setattr(
        module,
        "get_dict_data_service",
        lambda: _dict_service({"model_type": {"m": "查询"}, "menu_point": {"p": "列表"}}),
    )
    monkeypatch.setattr(module, "TemplateExportParams", _boom)

    client = TestClient(_build_app(module.router))
    client.get("/manager/querylog/export")

    assert rows[0].menu_point == "列表"
    assert rows[0].model_type == "查询"
