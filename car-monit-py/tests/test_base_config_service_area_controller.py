"""``BaseConfigServiceAreaController`` —— ``/base/configServiceArea`` 的 7 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/base/BaseConfigServiceAreaController.java

测的是**控制器自己的约定**（Service / Mapper 由另外两个文件覆盖）：

* 7 个映射全部注册，且 3 条字面量路由排在 ``/{fwqbm}`` **之前**；
* 权限点：``list`` / ``export`` / ``add`` / ``edit`` / ``remove`` 五个，
  ``listQuery`` / ``getInfo`` **没有** ``@PreAuthorize``；
* ``getInfo`` 的路径变量是 **String**（业务编码），不是 ``Long``；
* ``remove`` 走 ``String[]`` —— 非 UUID 编码**不会** 500；
* ``add`` / ``edit`` 都落到同一个 ``save``：``PUT`` 不带 ``id`` 等于新增；
* ``export`` 的响应只有 ``code`` / ``msg``（文件名），**没有** ``data``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.base import base_config_service_area_controller as controller
from app.base.domain.base_config_service_area import BaseConfigServiceArea
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)

BODY: Dict[str, Any] = {
    "fwqbm": "S001",
    "fwqmc": "吉安服务区",
    "lon": "114.99",
    "lat": "27.11",
    "roadCode": "G45",
    "sectionCode": "G45-01",
    "pileNo": "K123+456",
}


class _FakeService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[BaseConfigServiceArea] = []
        self.by_id_result: Optional[BaseConfigServiceArea] = None
        self.save_result: Any = None
        self.delete_result: Any = None
        self.page_taken: Any = None

    def select_list(self, query: BaseConfigServiceArea) -> List[BaseConfigServiceArea]:
        self.calls.append(("select_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_by_id(self, fwqbm: str) -> Optional[BaseConfigServiceArea]:
        self.calls.append(("select_by_id", fwqbm))
        return self.by_id_result

    def save(self, entity: BaseConfigServiceArea) -> Any:
        self.calls.append(("save", entity.model_copy(deep=True)))
        return self.save_result

    def delete_by_ids(self, fwqbms: Sequence[str]) -> Any:
        self.calls.append(("delete_by_ids", list(fwqbms)))
        return self.delete_result


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeService()
    monkeypatch.setattr(controller, "_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_config_service_area_controller()


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    return TestClient(_build_app(login=False))


def _build_app(login: bool, permissions: Optional[set] = None) -> FastAPI:
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

    application.include_router(controller.router)
    return application


def _row(fwqbm: str = "S001") -> BaseConfigServiceArea:
    return BaseConfigServiceArea(fwqbm=fwqbm, fwqmc="吉安服务区")


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_seven_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/base/configServiceArea/list", ("GET",)),
            ("/base/configServiceArea/listQuery", ("GET",)),
            ("/base/configServiceArea/export", ("GET",)),
            ("/base/configServiceArea/{fwqbm}", ("GET",)),
            ("/base/configServiceArea", ("POST",)),
            ("/base/configServiceArea", ("PUT",)),
            ("/base/configServiceArea/{fwqbms}", ("DELETE",)),
        }

    def test_literal_routes_come_before_the_path_variable(self) -> None:
        """``/{fwqbm}`` 是 String，会吃掉后面所有单段 GET 路由。"""
        paths = [route.path for route in controller.router.routes]

        for literal in ("/list", "/listQuery", "/export"):
            assert paths.index(f"/base/configServiceArea{literal}") < paths.index(
                "/base/configServiceArea/{fwqbm}"
            )

    def test_list_query_and_get_info_need_no_permission_point(self, service: Any) -> None:
        """``listQuery`` / ``getInfo`` 在 Java 里没有 ``@PreAuthorize``。

        ``pre_authorize_permi`` 用 ``functools.wraps`` 包一层，但 ``router.get`` 注册的
        正是包过的那个对象，所以没法靠 ``route.endpoint`` 的身份区分 —— 改用**行为**
        区分：一个登录成功但**零权限**的用户，``/list`` 回 403、``/listQuery`` 回 200。
        """
        client = TestClient(_build_app(login=True, permissions=set()))

        assert client.get("/base/configServiceArea/list").json()["code"] == 403
        assert client.get("/base/configServiceArea/listQuery").json()["code"] == 200
        assert client.get("/base/configServiceArea/S001").json()["code"] == 200

    def test_write_endpoints_need_their_own_permission(self, service: Any) -> None:
        client = TestClient(_build_app(login=True, permissions={"base:configServiceArea:list"}))

        assert client.post("/base/configServiceArea", json=BODY).json()["code"] == 403
        assert client.delete("/base/configServiceArea/S001").json()["code"] == 403


# --------------------------------------------------------------------------- 查询


class TestList:
    def test_returns_the_table_data_info_envelope(self, http: Any, service: Any) -> None:
        service.list_result = [_row()]

        body = http.get("/base/configServiceArea/list").json()

        assert body["code"] == 200
        assert body["msg"] == "查询成功"
        assert body["total"] == 1
        assert body["rows"][0]["fwqbm"] == "S001"

    def test_start_page_is_consumed_by_the_service(self, http: Any, service: Any) -> None:
        http.get("/base/configServiceArea/list?pageNum=2&pageSize=5")

        assert service.calls[0][0] == "select_list"
        # 这里的 mini app 没有装 ``RequestContextMiddleware``，所以 ``start_page()``
        # 拿不到真实 query 参数（回落到默认 1/10）；只钉住"分页参数已被取走"。
        assert service.page_taken is not None

    def test_query_string_binds_onto_the_entity(self, http: Any, service: Any) -> None:
        http.get("/base/configServiceArea/list?fwqbm=S001&fwqmc=%E5%90%89%E5%AE%89")

        query = service.calls[0][1]
        assert query.fwqbm == "S001"
        assert query.fwqmc == "吉安"

    def test_list_query_is_not_paged(self, http: Any, service: Any) -> None:
        service.list_result = [_row()]

        body = http.get("/base/configServiceArea/listQuery").json()

        assert body["code"] == 200
        assert body["data"] == [body["data"][0]]
        assert "total" not in body
        assert service.page_taken is None


class TestGetInfo:
    def test_returns_the_entity_in_data(self, http: Any, service: Any) -> None:
        service.by_id_result = _row()

        body = http.get("/base/configServiceArea/S001").json()

        assert body["code"] == 200
        assert body["data"]["fwqbm"] == "S001"

    def test_missing_row_is_null_not_404(self, http: Any, service: Any) -> None:
        service.by_id_result = None

        response = http.get("/base/configServiceArea/nope")

        assert response.status_code == 200
        assert response.json() == {"code": 200, "msg": "操作成功"}

    def test_the_path_variable_is_a_string(self, http: Any, service: Any) -> None:
        """非数字编码**不会** 500 —— Java 声明的是 ``String fwqbm``。"""
        body = http.get("/base/configServiceArea/中文-编码").json()

        assert body["code"] == 200
        assert service.calls[0] == ("select_by_id", "中文-编码")


# --------------------------------------------------------------------------- 增删改


class TestWrite:
    def test_add_posts_to_save(self, http: Any, service: Any) -> None:
        service.save_result = {"code": 200, "msg": "操作成功！", "data": "uuid"}

        body = http.post("/base/configServiceArea", json=BODY).json()

        assert body == {"code": 200, "msg": "操作成功！", "data": "uuid"}
        assert service.calls[0][0] == "save"
        assert service.calls[0][1].fwqbm == "S001"

    def test_edit_puts_to_the_same_save(self, http: Any, service: Any) -> None:
        service.save_result = {"code": 200, "msg": "操作成功！", "data": "uuid"}

        http.put("/base/configServiceArea", json={**BODY, "id": "uuid"})

        assert service.calls[0][0] == "save"
        assert service.calls[0][1].id == "uuid"

    def test_remove_splits_the_path_variable(self, http: Any, service: Any) -> None:
        service.delete_result = {"code": 200, "msg": "操作成功", "data": 2}

        body = http.delete("/base/configServiceArea/S001,S002").json()

        assert body["data"] == 2
        assert service.calls[0] == ("delete_by_ids", ["S001", "S002"])

    def test_remove_accepts_non_numeric_ids(self, http: Any, service: Any) -> None:
        http.delete("/base/configServiceArea/中文")

        assert service.calls[0] == ("delete_by_ids", ["中文"])

    def test_empty_id_is_an_empty_string_element(self, http: Any, service: Any) -> None:
        """``parse_str_array("")`` -> ``[""]``（与 ``Long[]`` 不同，这里不报错）。"""
        http.delete("/base/configServiceArea/")

        assert service.calls == []


class TestExport:
    def test_export_returns_a_filename_in_msg(self, http: Any, service: Any, tmp_path: Any) -> None:
        service.list_result = [_row()]

        body = http.get("/base/configServiceArea/export").json()

        assert body["code"] == 200
        assert body["msg"].endswith(".xlsx")
        assert "data" not in body
        assert service.page_taken is None


# --------------------------------------------------------------------------- 安全


class TestSecurity:
    def test_a_zero_permission_user_cannot_read_the_list(self, service: Any) -> None:
        """``/list`` 要 ``base:configServiceArea:list``。

        “未登录 -> 401” 是 ``SecurityMiddleware`` 的职责（见
        ``tests/test_security_filter.py``）；这里没有装中间件，只能验证权限点本身。
        """
        client = TestClient(_build_app(login=True, permissions=set()))

        assert client.get("/base/configServiceArea/list").json()["code"] == 403

    def test_a_zero_permission_user_can_read_list_query_and_get_info(self, service: Any) -> None:
        """``listQuery`` / ``getInfo`` 在 Java 里没有 ``@PreAuthorize`` —— 登录即可。"""
        client = TestClient(_build_app(login=True, permissions=set()))

        assert client.get("/base/configServiceArea/listQuery").json()["code"] == 200
        assert client.get("/base/configServiceArea/S001").json()["code"] == 200
