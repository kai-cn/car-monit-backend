"""``SysIndexMenuController`` -- ``/system/indexmenu`` 的 7 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysIndexMenuController.java

这一层测什么
------------
Service 已被 ``test_sys_index_menu_service.py`` 覆盖，所以全部注入假 Service，只测
**控制器自己的约定**：

* 7 个映射全部注册（``export`` 在 Phase 3.18 补上，返回文件名）；
* 权限点只有 **两个**：``getInfo`` 与 ``edit``。``list`` / ``mylist`` / ``add`` /
  ``remove`` 的 ``@PreAuthorize`` 在 Java 源码里**是被注释掉的** —— 这不是遗漏，
  首页九宫格就靠这几个端点给普通用户取数据，补上权限会直接白屏；
* ``/list`` 与 ``/mylist`` **必须**排在 ``/{id}`` 之前，否则会被单段路径变量吃掉；
* ``/mylist`` 在控制器里**自己**又 ``setUserId`` 了一次（service 里还会再设一次）；
* ``add`` 只认 ``menuIds`` 一个字段，没有 ``@Validated``；
* ``edit`` 走的是 ``saveSysIndexMenu``：有 ``id`` 就改，没 ``id`` 就新增。

``export`` 与 ``/{id}`` 的冲突
-----------------------------
两者都是 ``GET`` 且都是单段。Java 下由 ``AntPathMatcher`` 优先匹配字面量，Python 下
靠**注册顺序**，所以 ``/export`` 必须写在 ``/{id}`` 之前 —— 否则 ``"export"``
会转 ``int`` 失败 -> ``HTTP 200 + code 500``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_index_menu_controller as controller
from app.api.system.sys_index_menu_controller import (
    add,
    edit,
    get_info,
    get_my_list,
    list_index_menus,
    remove,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.common.exception.exceptions import AccessDeniedException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.sys_index_menu import SysIndexMenu


# --------------------------------------------------------------------------- fakes


class _FakeIndexMenuService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysIndexMenu] = []
        self.my_list_result: List[SysIndexMenu] = []
        self.by_id_result: Optional[SysIndexMenu] = None
        self.insert_result: Dict[str, Any] = {"code": 200, "msg": "操作成功"}
        self.save_result: Dict[str, Any] = {
            "code": 200,
            "msg": "操作成功！",
            "data": "abc",
        }
        self.delete_result: Dict[str, Any] = {"code": 200, "msg": "操作成功", "data": 1}
        #: ``select_sys_index_menu_list`` 被调用时挂起中的分页参数。
        self.page_taken: Any = None

    def select_sys_index_menu_list(self, query: SysIndexMenu) -> List[SysIndexMenu]:
        self.calls.append(("select_sys_index_menu_list", query.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def get_list(self, query: SysIndexMenu) -> List[SysIndexMenu]:
        self.calls.append(("get_list", query.model_copy(deep=True)))
        return self.my_list_result

    def select_sys_index_menu_by_id(self, entity_id: Any) -> Optional[SysIndexMenu]:
        self.calls.append(("select_sys_index_menu_by_id", entity_id))
        return self.by_id_result

    def insert_sys_index_menu(self, menu_ids: Optional[str]) -> Dict[str, Any]:
        self.calls.append(("insert_sys_index_menu", menu_ids))
        return self.insert_result

    def save_sys_index_menu(self, entity: SysIndexMenu) -> Dict[str, Any]:
        self.calls.append(("save_sys_index_menu", entity.model_copy(deep=True)))
        return self.save_result

    def delete_sys_index_menu_by_ids(self, ids: Sequence[Any]) -> Dict[str, Any]:
        self.calls.append(("delete_sys_index_menu_by_ids", list(ids)))
        return self.delete_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeIndexMenuService()
    monkeypatch.setattr(controller, "_INDEX_MENU_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_index_menu_controller()


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    return TestClient(_build_app(login=False))


@pytest.fixture
def http_lenient() -> Any:
    """已登录、且**不把服务端异常当失败**的 mini app。

    ``@ExceptionHandler(Exception)`` 挂在 Starlette 的 ``ServerErrorMiddleware`` 上：
    响应发出后它还会再重抛一次。Uvicorn 下客户端拿到的就是 ``{"code":500,...}``；
    只有 ``TestClient`` 需要关掉 ``raise_server_exceptions`` 才看得到同一个响应体。
    """
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:

        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            SecurityContextHolder.get_context().set_authentication(
                UsernamePasswordAuthenticationToken(
                    LoginUser(user=SysUser(user_id=2, user_name="ry"), permissions={"*:*:*"}),
                    None,
                    [],
                )
            )
            return await call_next(request)

    application.include_router(controller.router)
    return application


def authenticate(
    user_id: int = 2, user_name: str = "ry", permissions: Optional[set] = None
) -> SysUser:
    user = SysUser(user_id=user_id, user_name=user_name)
    login_user = LoginUser(user=user, permissions=permissions or {"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _menu(menu_id: int = 100) -> SysIndexMenu:
    return SysIndexMenu(id="u-1", user_id=2, menu_id=menu_id, menu_name="用户管理")


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_seven_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/indexmenu/list", ("GET",)),
            ("/system/indexmenu/mylist", ("GET",)),
            ("/system/indexmenu/export", ("GET",)),
            ("/system/indexmenu/{id}", ("GET",)),
            ("/system/indexmenu", ("POST",)),
            ("/system/indexmenu", ("PUT",)),
            ("/system/indexmenu/{ids}", ("DELETE",)),
        }

    def test_export_comes_before_the_path_variable(self) -> None:
        """``/export`` 排在 ``/{id}`` 后面的话 ``"export"`` 会转 int 失败。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/indexmenu/export") < paths.index("/system/indexmenu/{id}")

    def test_the_literal_get_paths_come_first(self) -> None:
        """``/list`` 与 ``/mylist`` 都是单段，排在 ``/{id}`` 后面就会被吃掉。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/indexmenu/list") < paths.index("/system/indexmenu/{id}")
        assert paths.index("/system/indexmenu/mylist") < paths.index("/system/indexmenu/{id}")

    def test_the_list_beats_the_path_variable_over_http(self, http: TestClient) -> None:
        response = http.get("/system/indexmenu/list")

        assert response.json().keys() == {"total", "rows", "code", "msg"}
        assert response.json()["msg"] == "查询成功"

    def test_mylist_beats_the_path_variable_over_http(
        self, http: TestClient, service: Any
    ) -> None:
        service.my_list_result = [_menu()]

        response = http.get("/system/indexmenu/mylist")

        # 返回的是 AjaxResult（不是 TableDataInfo）：**没有** total / rows
        assert response.json()["code"] == 200
        assert "rows" not in response.json()
        assert service.of("select_sys_index_menu_by_id") == []

    def test_export_does_not_fall_into_the_path_variable(
        self, http: TestClient, service: Any
    ) -> None:
        """``/export`` 不再被 ``/{id}`` 兜住，返回**文件名**（落在 ``msg``）。"""
        response = http.get("/system/indexmenu/export")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["msg"].endswith("_用户常用菜单数据.xlsx")
        assert "data" not in body
        assert service.of("select_sys_index_menu_by_id") == []
        assert [call[0] for call in service.calls] == ["select_sys_index_menu_list"]


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    @pytest.mark.parametrize(
        "call",
        [
            lambda: get_info(1),
            lambda: edit(_menu()),
        ],
    )
    def test_the_two_guarded_endpoints(self, service: Any, call: Any) -> None:
        with pytest.raises(AccessDeniedException):
            call()

        assert service.calls == []

    @pytest.mark.parametrize(
        "call",
        [
            lambda: list_index_menus(SysIndexMenu()),
            lambda: get_my_list(SysIndexMenu()),
            lambda: add(SysIndexMenu(menu_ids="100")),
            lambda: remove("1"),
        ],
    )
    def test_the_four_unguarded_endpoints(self, service: Any, call: Any) -> None:
        """``@PreAuthorize`` 在 Java 里被注释掉了 —— 未登录也不能回 403。"""
        authenticate()

        response = call()

        # ``list`` 回的是 TableDataInfo，其余三个回 AjaxResult
        code = response.get_code() if hasattr(response, "get_code") else response["code"]
        assert code == 200
        assert service.calls != []

    def test_a_partial_permission_does_not_pass(self) -> None:
        authenticate(permissions={"system:indexmenu:*"})

        with pytest.raises(AccessDeniedException):
            edit(_menu())

    def test_query_permission_does_not_imply_edit(self) -> None:
        authenticate(permissions={"system:indexmenu:query"})

        with pytest.raises(AccessDeniedException):
            edit(_menu())

    def test_an_access_denied_becomes_http_200_code_403(
        self, http_anonymous: TestClient
    ) -> None:
        response = http_anonymous.get("/system/indexmenu/1")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}

    def test_an_anonymous_delete_is_not_403(self, http_anonymous: TestClient) -> None:
        """``remove`` 没有权限点 —— 未登录时由 Service 的 ``getUserId`` 决定后果。"""
        response = http_anonymous.delete("/system/indexmenu/1")

        assert response.json()["code"] != 403
        assert response.json() == {"code": 200, "msg": "操作成功", "data": 1}

    def test_an_anonymous_mylist_fails_inside_security_utils(
        self, http_anonymous: TestClient
    ) -> None:
        """``/mylist`` 要 ``getUserId()``，未登录时抛 ``CustomException`` -> code 500。"""
        response = http_anonymous.get("/system/indexmenu/mylist")

        assert response.status_code == 200
        assert response.json() == {"code": 500, "msg": "获取用户账户异常"}


# --------------------------------------------------------------------------- list


class TestList:
    def test_the_page_is_started_before_the_query(
        self, service: Any, http: TestClient
    ) -> None:
        http.get("/system/indexmenu/list")

        assert service.page_taken is not None
        assert service.page_taken.get_page_num() == 1

    def test_an_unknown_query_parameter_is_ignored(
        self, http: TestClient, service: Any
    ) -> None:
        """Java: ``WebDataBinder`` 的 ``ignoreUnknownFields=true``。"""
        response = http.get("/system/indexmenu/list", params={"nope": "1"})

        assert response.status_code == 200
        assert service.of("select_sys_index_menu_list") != []

    def test_the_camel_case_filters_are_bound(self, http: TestClient, service: Any) -> None:
        http.get(
            "/system/indexmenu/list",
            params={"menuName": "用户管理", "menuName2": "系统管理"},
        )

        query = service.of("select_sys_index_menu_list")[0][1]
        assert (query.menu_name, query.menu_name2) == ("用户管理", "系统管理")

    def test_the_controller_does_not_touch_the_user_id(self, http: TestClient, service: Any) -> None:
        """覆盖 ``userId`` 是 **Service** 的活；控制器原样透传（与 ``/mylist`` 不同）。"""
        http.get("/system/indexmenu/list", params={"userId": "999"})

        assert service.of("select_sys_index_menu_list")[0][1].user_id == 999

    def test_the_rows_and_total_come_from_the_mapper(self, service: Any) -> None:
        authenticate()
        service.list_result = [_menu(100), _menu(101)]

        response = list_index_menus(SysIndexMenu())

        assert response.get_total() == 2
        assert [row.menu_id for row in response.get_rows()] == [100, 101]

    def test_an_empty_list_is_still_a_zero_total(self, service: Any) -> None:
        authenticate()

        response = list_index_menus(SysIndexMenu())

        assert response.get_total() == 0
        assert response.get_rows() == []


# --------------------------------------------------------------------------- mylist


class TestMyList:
    def test_the_user_id_comes_from_the_login_context(self, service: Any) -> None:
        authenticate(user_id=2)

        get_my_list(SysIndexMenu(user_id=999))

        assert service.of("get_list")[0][1].user_id == 2

    def test_the_over_http_path_sets_the_same_value(self, http: TestClient, service: Any) -> None:
        http.get("/system/indexmenu/mylist", params={"userId": "999"})

        assert service.of("get_list")[0][1].user_id == 2

    def test_the_rows_are_wrapped_in_a_success_envelope(
        self, service: Any, http: TestClient
    ) -> None:
        service.my_list_result = [_menu(100)]

        body = http.get("/system/indexmenu/mylist").json()

        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert [row["menuId"] for row in body["data"]] == [100]

    def test_an_empty_result_keeps_an_empty_data_array(self, http: TestClient) -> None:
        """``success_data([])`` 保留 ``"data": []``（不是省略）。"""
        body = http.get("/system/indexmenu/mylist").json()

        assert body["data"] == []

    def test_the_menu_url_survives(self, service: Any, http: TestClient) -> None:
        """``menuUrl`` 是 SQL 里 ``concat(path,'/',path)`` 拼出来的，原样吐出。"""
        service.my_list_result = [
            SysIndexMenu(id="u-1", menu_name="用户管理", menu_url="system/user")
        ]

        body = http.get("/system/indexmenu/mylist").json()

        assert body["data"][0]["menuUrl"] == "system/user"


# --------------------------------------------------------------------------- getInfo


class TestGetInfo:
    def test_the_path_id_is_passed_through_as_an_int(self, service: Any) -> None:
        authenticate()

        get_info(123)

        assert service.of("select_sys_index_menu_by_id") == [("select_sys_index_menu_by_id", 123)]

    def test_a_missing_row_omits_data(self, http: TestClient) -> None:
        """查不到时 ``data`` 整个键消失（``success_data(None)``），不是 404。"""
        response = http.get("/system/indexmenu/123")

        assert response.status_code == 200
        assert response.json() == {"code": 200, "msg": "操作成功"}

    def test_a_hit_serializes_with_java_property_names(self, service: Any, http: TestClient) -> None:
        service.by_id_result = _menu(100)

        body = http.get("/system/indexmenu/123").json()

        assert body["data"]["menuId"] == 100
        assert body["data"]["menuName"] == "用户管理"
        assert "menu_id" not in body["data"]

    def test_params_is_serialized_as_null(self, service: Any, http: TestClient) -> None:
        """``BaseUuidEntity.params`` **没有** ``@JsonInclude(NON_EMPTY)`` -> 输出 ``null``。"""
        service.by_id_result = _menu(100)

        body = http.get("/system/indexmenu/123").json()

        assert body["data"]["params"] is None

    def test_search_value_is_serialized_because_this_base_class_lacks_json_ignore(
        self, service: Any, http: TestClient
    ) -> None:
        """``BaseUuidEntity.searchValue`` 没有 ``@JsonIgnore`` -> 照样输出 ``null``。

        与 :class:`~app.common.core.domain.base_entity.BaseEntity` 相反 —— 那边带
        ``@JsonIgnore``，**两边都不出现**。照抄 ``BaseEntity`` 的处理会让这个键凭空消失。
        """
        service.by_id_result = _menu(100)

        body = http.get("/system/indexmenu/123").json()

        assert body["data"]["searchValue"] is None

    def test_the_uuid_id_is_a_string(self, service: Any, http: TestClient) -> None:
        service.by_id_result = _menu(100)

        body = http.get("/system/indexmenu/123").json()

        assert body["data"]["id"] == "u-1"

    def test_a_non_numeric_path_id_is_a_code_500(self, http_lenient: TestClient) -> None:
        """Java: ``MethodArgumentTypeMismatchException`` -> HTTP 200 + code 500。"""
        response = http_lenient.get("/system/indexmenu/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- add


class TestAdd:
    def test_only_menu_ids_matters(self, service: Any) -> None:
        authenticate()

        add(SysIndexMenu(menu_ids="100,101", user_id=999, id="ignored"))

        assert service.of("insert_sys_index_menu") == [("insert_sys_index_menu", "100,101")]

    def test_a_missing_menu_ids_is_none(self, service: Any) -> None:
        authenticate()

        add(SysIndexMenu())

        assert service.of("insert_sys_index_menu") == [("insert_sys_index_menu", None)]

    def test_the_response_is_the_service_response_verbatim(
        self, service: Any, http: TestClient
    ) -> None:
        service.insert_result = {"code": 200, "msg": "操作成功"}

        body = http.post("/system/indexmenu", json={"menuIds": "100"}).json()

        assert body == {"code": 200, "msg": "操作成功"}

    def test_the_body_property_names_are_camel_case(self, service: Any, http: TestClient) -> None:
        http.post("/system/indexmenu", json={"menuIds": "100,101"})

        assert service.of("insert_sys_index_menu") == [("insert_sys_index_menu", "100,101")]

    def test_an_unknown_body_field_is_ignored(self, service: Any, http: TestClient) -> None:
        response = http.post("/system/indexmenu", json={"menuIds": "100", "nope": 1})

        assert response.status_code == 200
        assert response.json()["code"] == 200


# --------------------------------------------------------------------------- edit


class TestEdit:
    def test_no_validation_is_applied(self, service: Any, http: TestClient) -> None:
        """没有 ``@Validated``，空 body 也照收 —— 一个字段都进不到 Service 也没关系。"""
        response = http.put("/system/indexmenu", json={})

        assert response.status_code == 200
        assert response.json()["code"] == 200
        assert service.of("save_sys_index_menu") != []

    def test_the_entity_reaches_the_service_intact(self, service: Any) -> None:
        authenticate()

        edit(SysIndexMenu(id="u-1", menu_id=100, user_id=2))

        stored = service.of("save_sys_index_menu")[0][1]
        assert (stored.id, stored.menu_id) == ("u-1", 100)

    def test_the_success_message_keeps_the_full_width_bang(
        self, service: Any, http: TestClient
    ) -> None:
        body = http.put("/system/indexmenu", json={"id": "u-1"}).json()

        assert body["msg"] == "操作成功！"
        assert body["data"] == "abc"

    def test_query_permission_is_not_enough_for_edit(self, http: TestClient) -> None:
        response = http.put("/system/indexmenu", json={})

        assert response.json()["code"] == 200


# --------------------------------------------------------------------------- remove


class TestRemove:
    def test_the_comma_separated_ids_are_split(self, service: Any) -> None:
        authenticate()

        remove("1,2,3")

        assert service.of("delete_sys_index_menu_by_ids") == [
            ("delete_sys_index_menu_by_ids", [1, 2, 3])
        ]

    def test_the_response_is_the_service_response_verbatim(self, service: Any) -> None:
        authenticate()
        service.delete_result = {"code": 200, "msg": "操作成功", "data": 0}

        response = remove("1")

        # 软删除 + ``AjaxResult.success``：0 行也回 200
        assert response == {"code": 200, "msg": "操作成功", "data": 0}

    def test_a_zero_count_is_still_http_200(self, service: Any, http: TestClient) -> None:
        service.delete_result = {"code": 200, "msg": "操作成功", "data": 0}

        body = http.delete("/system/indexmenu/1").json()

        assert body["code"] == 200
        assert body["data"] == 0

    def test_a_non_numeric_id_is_a_code_500(self, http_lenient: TestClient) -> None:
        """Java: ``Long[]`` 转换失败 -> HTTP 200 + code 500。"""
        response = http_lenient.delete("/system/indexmenu/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- 其它


class TestMisc:
    def test_a_wrong_method_is_code_500(self, http: TestClient) -> None:
        """``DELETE /system/indexmenu`` 没有映射 -> Java 的 ``HttpRequestMethodNotSupportedException``。"""
        body = http.delete("/system/indexmenu").json()

        assert body["code"] == 500
        assert body["msg"] == "Request method 'DELETE' not supported"

    def test_the_router_prefix_is_the_java_one(self) -> None:
        assert controller.router.prefix == "/system/indexmenu"
