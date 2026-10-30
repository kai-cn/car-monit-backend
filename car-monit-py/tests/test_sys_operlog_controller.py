"""``SysOperlogController`` —— ``/monitor/operlog`` 的 4 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/monitor/SysOperlogController.java
#   + ruoyi-admin/.../web/controller/monitor/SysUserOnlineController.java（注解风格参考）

这一层测什么
------------
Mapper 已被 ``test_sys_oper_log_mapper.py`` 覆盖、Service 只是一行转发，所以这里
全部注入假 Service，只测**控制器自己的约定**：

* 4 个映射全部注册，且 ``DELETE /clean`` 必须排在 ``DELETE /{operIds}`` **之前**
  （Spring 的 ``AntPathMatcher`` 会优先匹配字面量，FastAPI 只看注册顺序）；
* ``list`` 在 Service 之前调 ``startPage()``；
* ``export`` **不**分页，``msg`` 是文件名（``AjaxResult.success(String)`` 重载 ——
  没有 ``data`` 键）；
* ``clean`` 与 ``remove`` 共用 ``monitor:operlog:remove`` 权限（Java 原文如此）；
* ``businessTypes`` 数组绑定：RuoYi 前端发的是**重复键**
  （``businessTypes=0&businessTypes=1``），Spring 逐元素转 ``Integer``。

``businessTypes`` 为什么不能用通用绑定器
----------------------------------------
:func:`app.common.core.controller.base_controller.bind_query_params` 只处理
``str`` / ``bool`` / ``int`` / ``datetime`` 这几种标量；把 ``List[str]`` 塞给 pydantic
会直接 422，而 Java 侧是 ``String[]`` -> ``Integer[]`` 的转换失败 -> **code 500**。
所以控制器自己写了 :func:`_parse_business_types`，失败时抛 ``ValueError``。
"""

from __future__ import annotations

from typing import Any, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.monitor import sys_operlog_controller as controller
from app.api.monitor.sys_operlog_controller import (
    EXPORT_SHEET_NAME,
    _parse_business_types,
    clean,
    export,
    list_oper_logs,
    remove,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page, start_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.sys_oper_log import SysOperLog


# --------------------------------------------------------------------------- fakes


class _FakeOperLogService:
    """Java: ``@Autowired ISysOperLogService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysOperLog] = []
        self.delete_result = 1
        self.clean_calls = 0
        #: Service 被调用时挂起中的分页参数（真实 mapper 会在这里 ``take_page()``）。
        self.page_taken: Any = None

    def select_oper_log_list(self, oper_log: SysOperLog) -> List[SysOperLog]:
        self.calls.append(("select_oper_log_list", oper_log.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def delete_oper_log_by_ids(self, oper_ids: List[int]) -> int:
        self.calls.append(("delete_oper_log_by_ids", list(oper_ids)))
        return self.delete_result

    def clean_oper_log(self) -> None:
        self.calls.append(("clean_oper_log",))
        self.clean_calls += 1

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者与安全上下文。"""
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeOperLogService()
    monkeypatch.setattr(controller, "_OPER_LOG_SERVICE", fake)
    # 直调函数时没有 ``JwtAuthenticationTokenFilter``，得自己放一个 *:*:* 的登录态
    authenticate()
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_oper_log_controller()


@pytest.fixture
def http() -> Any:
    """已登录的 mini app（``*:*:*``，等同超级管理员）。"""
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_lenient() -> Any:
    """把服务端异常当响应的 mini app（``@ExceptionHandler(Exception)`` 会再重抛）。"""
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


def _login_user() -> LoginUser:
    user = SysUser(user_id=1, user_name="admin", dept_id=103)
    return LoginUser(token="t", user=user, permissions={"*:*:*"})


def authenticate(permissions: Optional[set] = None) -> SysUser:
    """直调函数时用的登录态（默认超级管理员 ``*:*:*``）。"""
    user = SysUser(user_id=1, user_name="admin", dept_id=103)
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
            SecurityContextHolder.get_context().set_authentication(
                UsernamePasswordAuthenticationToken(_login_user(), None, [])
            )
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
            ("/monitor/operlog/list", ("GET",)),
            ("/monitor/operlog/export", ("GET",)),
            ("/monitor/operlog/clean", ("DELETE",)),
            ("/monitor/operlog/{oper_ids}", ("DELETE",)),
        }

    def test_clean_comes_before_the_path_variable(self) -> None:
        """``DELETE /clean`` 若排在 ``/{oper_ids}`` 之后，会被当成 ``operIds="clean"``。"""
        paths = [route.path for route in controller.router.routes]
        assert paths.index("/monitor/operlog/clean") < paths.index(
            "/monitor/operlog/{oper_ids}"
        )

    def test_clean_is_not_swallowed_by_the_path_variable_over_http(
        self, http: Any, service: _FakeOperLogService
    ) -> None:
        response = http.delete("/monitor/operlog/clean")

        assert response.status_code == 200
        assert response.json()["code"] == 200
        assert service.clean_calls == 1

    def test_the_sheet_name_is_the_java_literal(self) -> None:
        assert EXPORT_SHEET_NAME == "操作日志"


# --------------------------------------------------------------------------- list


class TestList:
    def test_returns_a_table_data_info(self, service: _FakeOperLogService) -> None:
        service.list_result = [SysOperLog(oper_id=1, title="用户管理")]
        body = list_oper_logs(SysOperLog()).to_dict()

        assert body["code"] == 200
        assert body["msg"] == "查询成功"
        # 行里是实体对象；JSON 键名由 pydantic 的 alias 决定（``operId``）
        assert body["rows"][0].model_dump(by_alias=True)["operId"] == 1
        # 没有分页参数时 ``PageInfo`` 的 total 就是列表长度
        assert body["total"] == 1

    def test_string_concatenation_of_a_single_row(self, service: _FakeOperLogService) -> None:
        """``get_data_table`` 在只有一行时也必须还是 ``List``（不是单个对象）。"""
        service.list_result = [SysOperLog(oper_id=9)]
        body = list_oper_logs(SysOperLog()).to_dict()
        assert isinstance(body["rows"], list)
        assert len(body["rows"]) == 1

    def test_start_page_runs_before_the_query(self, service: _FakeOperLogService) -> None:
        """``startPage()`` 是方法体第一行；分页参数由 mapper 的 ``take_page`` 取走。"""
        list_oper_logs(SysOperLog())

        assert service.page_taken is not None
        assert service.page_taken.get_page_num() == 1
        assert service.page_taken.get_page_size() == 10

    def test_query_parameters_are_bound_to_the_entity(self, http: Any, service: Any) -> None:
        response = http.get(
            "/monitor/operlog/list",
            params={"title": "用户", "status": 1, "operName": "admin"},
        )

        assert response.status_code == 200
        bound = service.of("select_oper_log_list")[0][1]
        assert bound.title == "用户"
        assert bound.status == 1
        assert bound.oper_name == "admin"

    def test_business_type_zero_is_still_bound(self, http: Any, service: Any) -> None:
        """0（其它）不丢 —— 丢掉条件是 **mapper** 的事，不是绑定层的。"""
        http.get("/monitor/operlog/list", params={"businessType": 0})

        bound = service.of("select_oper_log_list")[0][1]
        assert bound.business_type == 0

    def test_camel_case_alias_is_accepted(self, http: Any, service: Any) -> None:
        """前端发的是 Java 属性名 ``businessType``，不是 ``business_type``。"""
        http.get("/monitor/operlog/list", params={"businessType": 2})
        assert service.of("select_oper_log_list")[0][1].business_type == 2

    def test_time_range_goes_into_params(self, http: Any, service: Any) -> None:
        http.get(
            "/monitor/operlog/list",
            params={"params[beginTime]": "2024-01-01", "params[endTime]": "2024-12-31"},
        )
        bound = service.of("select_oper_log_list")[0][1]
        assert bound.params["beginTime"] == "2024-01-01"
        assert bound.params["endTime"] == "2024-12-31"


# --------------------------------------------------------------------------- businessTypes


class TestBusinessTypesBinding:
    """``Integer[] businessTypes`` —— RuoYi 前端用 ``tansParams`` 发**重复键**."""

    def test_repeated_keys_become_a_list(self, http: Any, service: Any) -> None:
        http.get(
            "/monitor/operlog/list",
            params=[("businessTypes", 0), ("businessTypes", 1)],
        )
        assert service.of("select_oper_log_list")[0][1].business_types == [0, 1]

    def test_comma_separated_value_also_works(self, http: Any, service: Any) -> None:
        """宽容：``businessTypes=1,2`` 与 ``businessTypes=1&businessTypes=2`` 等价。"""
        http.get("/monitor/operlog/list", params={"businessTypes": "1,2"})
        assert service.of("select_oper_log_list")[0][1].business_types == [1, 2]

    def test_absent_becomes_none(self, http: Any, service: Any) -> None:
        http.get("/monitor/operlog/list")
        # ``None``（不是 ``[]``）：XML 的判据两者等价，但保持与 ``getParameterValues`` 一致
        assert service.of("select_oper_log_list")[0][1].business_types is None

    def test_parse_keeps_zero(self) -> None:
        assert _parse_business_types(["0", "1"]) == [0, 1]

    def test_parse_empty_list_is_none(self) -> None:
        assert _parse_business_types([]) is None

    def test_non_numeric_is_a_500_not_a_422(self, http_lenient: Any) -> None:
        """Java: ``NumberFormatException`` -> ``BindException`` -> HTTP 200 + code 500."""
        response = http_lenient.get("/monitor/operlog/list", params={"businessTypes": "abc"})

        assert response.status_code == 200
        assert response.json()["code"] == 500

    def test_empty_element_is_a_500(self) -> None:
        """``"1,,2"`` -> 空串 -> ``Integer.valueOf("")`` 抛错（Java 同样失败）。"""
        with pytest.raises(ValueError):
            _parse_business_types(["1,,2"])


# --------------------------------------------------------------------------- export


class TestExport:
    def test_msg_is_the_filename_and_there_is_no_data_key(
        self, service: _FakeOperLogService
    ) -> None:
        """``AjaxResult.success(String)`` 重载：文件名落在 ``msg`` 里。"""
        service.list_result = [SysOperLog(oper_id=1, title="用户管理")]
        body = export(SysOperLog())

        assert body["code"] == 200
        assert body["msg"].endswith("_操作日志.xlsx")
        assert "data" not in body

    def test_export_does_not_start_a_page(self, service: _FakeOperLogService) -> None:
        """导出全量，没有 ``startPage()`` —— ``page_taken`` 必须仍是 ``None``。"""
        export(SysOperLog())
        assert service.page_taken is None

    def test_export_binds_the_same_query_parameters(self, http: Any, service: Any) -> None:
        http.get("/monitor/operlog/export", params={"title": "登录"})
        assert service.of("select_oper_log_list")[0][1].title == "登录"


# --------------------------------------------------------------------------- 删除


class TestRemove:
    def test_comma_separated_ids_are_parsed(self, service: _FakeOperLogService) -> None:
        body = remove("1,2,3")

        assert service.of("delete_oper_log_by_ids")[0][1] == [1, 2, 3]
        assert body["code"] == 200

    def test_zero_rows_is_an_error_envelope(self, service: _FakeOperLogService) -> None:
        """``BaseController.toAjax(rows)`` = ``rows > 0 ? success() : error()``.

        注意 ``error()`` 的 code 是 **500**（不是 400）—— HTTP 状态码仍是 200。
        """
        service.delete_result = 0
        body = remove("99")
        assert body["code"] == 500
        assert body["msg"] == "操作失败"

    def test_non_numeric_id_is_a_500(self, http_lenient: Any) -> None:
        response = http_lenient.delete("/monitor/operlog/abc")
        assert response.status_code == 200
        assert response.json()["code"] == 500


class TestClean:
    def test_clean_delegates_and_returns_success(self, service: _FakeOperLogService) -> None:
        body = clean()

        assert service.of("clean_oper_log") == [("clean_oper_log",)]
        assert body["code"] == 200
        # Java: ``return AjaxResult.success();`` —— 不看影响行数，也没有 ``data`` 键
        assert "data" not in body

    def test_clean_does_not_delete_by_ids(self, service: _FakeOperLogService) -> None:
        clean()
        assert service.of("delete_oper_log_by_ids") == []
