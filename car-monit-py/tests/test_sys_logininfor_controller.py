"""``SysLogininforController`` —— ``/monitor/logininfor`` 的 4 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/monitor/SysLogininforController.java

与 ``/monitor/operlog`` 的三处差异
----------------------------------
1. ``SysLogininfor.status`` 是 **``String``**（``"0"`` / ``"1"``），不是 ``Integer``，
   所以查询条件走的是普通的 ``!= null and != ''``，没有 ``businessType`` 那个
   "0 被当空串吃掉"的 OGNL 陷阱。
2. 没有 ``businessTypes`` 数组，所以参数绑定可以直接用通用绑定器
   （:func:`bind_query_params`），不需要自定义 ``Depends``。
3. 权限点是 ``monitor:logininfor:*``，``clean`` 与 ``remove`` 同样共用 ``remove``。

``DELETE /clean`` 的声明顺序
----------------------------
必须排在 ``DELETE /{infoIds}`` 之前：FastAPI 按注册顺序匹配，否则 ``clean`` 会被
当成 ``infoIds="clean"`` -> ``int("clean")`` 失败 -> code 500。Spring 的
``AntPathMatcher`` 偏爱字面量，与顺序无关，所以两边最终行为一致。
"""

from __future__ import annotations

from typing import Any, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.monitor import sys_logininfor_controller as controller
from app.api.monitor.sys_logininfor_controller import (
    EXPORT_SHEET_NAME,
    clean,
    export,
    list_logininfor,
    remove,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.sys_logininfor import SysLogininfor


# --------------------------------------------------------------------------- fakes


class _FakeLogininforService:
    """Java: ``@Autowired ISysLogininforService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysLogininfor] = []
        self.delete_result = 1
        self.page_taken: Any = None

    def select_logininfor_list(self, logininfor: SysLogininfor) -> List[SysLogininfor]:
        self.calls.append(("select_logininfor_list", logininfor.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def delete_logininfor_by_ids(self, info_ids: List[int]) -> int:
        self.calls.append(("delete_logininfor_by_ids", list(info_ids)))
        return self.delete_result

    def clean_logininfor(self) -> None:
        self.calls.append(("clean_logininfor",))

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeLogininforService()
    monkeypatch.setattr(controller, "_LOGININFOR_SERVICE", fake)
    authenticate()
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_logininfor_controller()


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_lenient() -> Any:
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


def authenticate(permissions: Optional[set] = None) -> SysUser:
    """直调函数时用的登录态（默认超级管理员 ``*:*:*``）。"""
    user = SysUser(user_id=1, user_name="admin")
    login_user = LoginUser(token="t", user=user, permissions=permissions or {"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:

        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            authenticate()
            return await call_next(request)

    application.include_router(controller.router)
    return application


# --------------------------------------------------------------------------- 路由表


class TestRoutes:
    def test_the_four_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }
        assert registered == {
            ("/monitor/logininfor/list", ("GET",)),
            ("/monitor/logininfor/export", ("GET",)),
            ("/monitor/logininfor/clean", ("DELETE",)),
            ("/monitor/logininfor/{info_ids}", ("DELETE",)),
        }

    def test_clean_comes_before_the_path_variable(self) -> None:
        paths = [route.path for route in controller.router.routes]
        assert paths.index("/monitor/logininfor/clean") < paths.index(
            "/monitor/logininfor/{info_ids}"
        )

    def test_clean_is_not_swallowed_over_http(
        self, http: Any, service: _FakeLogininforService
    ) -> None:
        response = http.delete("/monitor/logininfor/clean")

        assert response.status_code == 200
        assert response.json()["code"] == 200
        assert service.of("clean_logininfor") == [("clean_logininfor",)]

    def test_the_sheet_name_is_the_java_literal(self) -> None:
        assert EXPORT_SHEET_NAME == "登录日志"


# --------------------------------------------------------------------------- list


class TestList:
    def test_returns_a_table_data_info(self, service: _FakeLogininforService) -> None:
        service.list_result = [SysLogininfor(info_id=1, user_name="admin", status="0")]
        body = list_logininfor(SysLogininfor()).to_dict()

        assert body["code"] == 200
        assert body["msg"] == "查询成功"
        assert body["total"] == 1
        assert body["rows"][0].model_dump(by_alias=True)["userName"] == "admin"

    def test_start_page_runs_before_the_query(self, service: _FakeLogininforService) -> None:
        list_logininfor(SysLogininfor())

        assert service.page_taken is not None
        assert service.page_taken.get_page_num() == 1
        assert service.page_taken.get_page_size() == 10

    def test_query_parameters_are_bound(self, http: Any, service: Any) -> None:
        http.get(
            "/monitor/logininfor/list",
            params={"ipaddr": "127.0", "status": "0", "userName": "admin"},
        )
        bound = service.of("select_logininfor_list")[0][1]
        assert bound.ipaddr == "127.0"
        assert bound.status == "0"
        assert bound.user_name == "admin"

    def test_status_zero_string_survives_binding(self, http: Any, service: Any) -> None:
        """``status="0"`` 是字符串，不会被当成"空"丢掉（对比 operlog 的 Integer 0）。"""
        http.get("/monitor/logininfor/list", params={"status": "0"})
        assert service.of("select_logininfor_list")[0][1].status == "0"

    def test_time_range_goes_into_params(self, http: Any, service: Any) -> None:
        http.get(
            "/monitor/logininfor/list",
            params={"params[beginTime]": "2024-01-01", "params[endTime]": "2024-12-31"},
        )
        bound = service.of("select_logininfor_list")[0][1]
        assert bound.params["beginTime"] == "2024-01-01"
        assert bound.params["endTime"] == "2024-12-31"


# --------------------------------------------------------------------------- export


class TestExport:
    def test_msg_is_the_filename_and_there_is_no_data_key(
        self, service: _FakeLogininforService
    ) -> None:
        service.list_result = [SysLogininfor(info_id=1)]
        body = export(SysLogininfor())

        assert body["code"] == 200
        assert body["msg"].endswith("_登录日志.xlsx")
        assert "data" not in body

    def test_export_does_not_start_a_page(self, service: _FakeLogininforService) -> None:
        export(SysLogininfor())
        assert service.page_taken is None


# --------------------------------------------------------------------------- 删除


class TestRemove:
    def test_comma_separated_ids_are_parsed(self, service: _FakeLogininforService) -> None:
        body = remove("4,5")

        assert service.of("delete_logininfor_by_ids")[0][1] == [4, 5]
        assert body["code"] == 200

    def test_zero_rows_is_an_error_envelope(self, service: _FakeLogininforService) -> None:
        """``toAjax(0)`` -> ``AjaxResult.error()`` -> code **500**（HTTP 仍是 200）。"""
        service.delete_result = 0
        assert remove("99")["code"] == 500

    def test_non_numeric_id_is_a_500(self, http_lenient: Any) -> None:
        response = http_lenient.delete("/monitor/logininfor/abc")
        assert response.status_code == 200
        assert response.json()["code"] == 500


class TestClean:
    def test_clean_delegates_and_returns_success(self, service: _FakeLogininforService) -> None:
        body = clean()

        assert service.of("clean_logininfor") == [("clean_logininfor",)]
        assert body["code"] == 200
        assert "data" not in body

    def test_clean_does_not_delete_by_ids(self, service: _FakeLogininforService) -> None:
        clean()
        assert service.of("delete_logininfor_by_ids") == []


class TestNotLoggedIn:
    def test_anonymous_is_rejected_by_the_permission_check(self) -> None:
        """没有登录态时 ``@PreAuthorize`` 直接拒绝（不碰 Service）。"""
        SecurityContextHolder.clear_context()
        with pytest.raises(Exception):
            list_logininfor(SysLogininfor())
