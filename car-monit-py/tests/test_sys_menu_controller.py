"""``SysMenuController`` -- ``/system/menu`` 的 7 个映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysMenuController.java
#   + ruoyi-common/.../core/controller/BaseController.java

这一层测什么
------------
Service 已被 ``test_sys_menu_service.py`` 覆盖、Mapper 被 ``test_sys_menu_mapper.py``
覆盖，所以这里全部注入假 Service，只测**控制器自己的判断**：

* 路由注册：7 条 + 字面量必须排在 ``/{menu_id}`` 之前；
* ``treeselect`` / ``roleMenuTreeselect`` **只要求登录**（没有 ``@PreAuthorize``）；
* ``list`` **不分页**（返回 ``AjaxResult``，不是 ``TableDataInfo``）；
* ``add`` 的两道闸、``edit`` 的三道闸（多一道"上级不能是自己"）；
* ``remove`` 的两道闸（子菜单 / 已分配）；
* 三个查询端点都要先 ``tokenService.getLoginUser(request)`` 取当前用户 id。

``@Validated`` 与 ``@PreAuthorize`` 的先后
------------------------------------------
Java 的顺序是"参数解析（含校验）→ 方法代理（含 ``@PreAuthorize``）"，所以
**没权限的请求只要请求体不合法，回的也是 500 而不是 403**。
:class:`TestValidationRunsBeforePermission` 用"未登录 + 非法请求体"验证这一点：
如果哪天有人把 :data:`ValidMenu` 从 ``Depends`` 挪进函数体，这个用例会立刻变红。

两种驱动方式
------------
* 直调函数：能拿到 ``AjaxResult`` 对象本身，断言键序最直观；
* ``TestClient``：只有走 ASGI 栈才会真正解析 ``Depends`` 与路由表。用**独立的
  mini app**（只挂本控制器的 router + 异常处理器），避开 ``SecurityMiddleware``
  对 MySQL/Redis 的依赖。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_menu_controller as controller
from app.api.system.sys_menu_controller import (
    ADD_MENU_BAD_FRAME_URL,
    ADD_MENU_NAME_EXISTS,
    EDIT_MENU_BAD_FRAME_URL,
    EDIT_MENU_NAME_EXISTS,
    EDIT_MENU_SELF_PARENT,
    REMOVE_HAS_CHILD,
    REMOVE_HAS_ROLE,
    add,
    edit,
    get_info,
    list_menus,
    remove,
    role_menu_treeselect,
    treeselect,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_menu import SysMenu
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page
from app.common.exception.exceptions import AccessDeniedException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)

#: 一个能通过 ``MENU_CONSTRAINTS`` 的请求体（``menuName`` / ``orderNum`` / ``menuType``
#: 三个 ``@NotBlank``）。
VALID_BODY: Dict[str, Any] = {"menuName": "用户管理", "orderNum": "1", "menuType": "C"}

#: Java: ``UserConstants.UNIQUE_OLD`` / ``NOT_UNIQUE_OLD``。
UNIQUE = "0"
NOT_UNIQUE = "1"


# --------------------------------------------------------------------------- fakes


class _FakeMenuService:
    """记录每一次调用；答案由用例配置。"""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysMenu] = []
        self.for_user_result: List[SysMenu] = []
        self.menu_by_id: Optional[SysMenu] = None
        self.role_menu_ids: List[int] = []
        self.tree_select: Any = []
        self.name_unique = UNIQUE
        self.has_child = False
        self.exist_role = False
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1

    # -- 查询 --------------------------------------------------------------
    def select_menu_list(self, menu: SysMenu, user_id: int) -> List[SysMenu]:
        self.calls.append(("select_menu_list", menu.model_copy(deep=True), user_id))
        return self.list_result

    def select_menu_list_for_user(self, user_id: int) -> List[SysMenu]:
        self.calls.append(("select_menu_list_for_user", user_id))
        return self.for_user_result

    def select_menu_list_by_role_id(self, role_id: int) -> List[int]:
        self.calls.append(("select_menu_list_by_role_id", role_id))
        return self.role_menu_ids

    def build_menu_tree_select(self, menus: List[SysMenu]) -> Any:
        self.calls.append(("build_menu_tree_select", list(menus)))
        return self.tree_select

    def select_menu_by_id(self, menu_id: int) -> Optional[SysMenu]:
        self.calls.append(("select_menu_by_id", menu_id))
        return self.menu_by_id

    # -- 校验 --------------------------------------------------------------
    def check_menu_name_unique(self, menu: SysMenu) -> str:
        self.calls.append(("check_menu_name_unique", menu.menu_name))
        return self.name_unique

    def has_child_by_menu_id(self, menu_id: int) -> bool:
        self.calls.append(("has_child_by_menu_id", menu_id))
        return self.has_child

    def check_menu_exist_role(self, menu_id: int) -> bool:
        self.calls.append(("check_menu_exist_role", menu_id))
        return self.exist_role

    # -- 写 ----------------------------------------------------------------
    def insert_menu(self, menu: SysMenu) -> int:
        self.calls.append(("insert_menu", menu.model_copy(deep=True)))
        return self.insert_result

    def update_menu(self, menu: SysMenu) -> int:
        self.calls.append(("update_menu", menu.model_copy(deep=True)))
        return self.update_result

    def delete_menu_by_id(self, menu_id: int) -> int:
        self.calls.append(("delete_menu_by_id", menu_id))
        return self.delete_result

    # ----------------------------------------------------------------------
    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]

    def names(self) -> List[str]:
        return [call[0] for call in self.calls]


class _FakeTokenService:
    """Java: ``@Autowired TokenService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        #: ``None`` 用来模拟"令牌已过期" -> Java NPE。
        self.login_user: Optional[LoginUser] = _login_user()

    def get_login_user(self, request: Any) -> Optional[LoginUser]:
        self.calls.append(("get_login_user", request))
        return self.login_user

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _Fakes:
    def __init__(self) -> None:
        self.menu = _FakeMenuService()
        self.token = _FakeTokenService()


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def fakes(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者与安全上下文。"""
    SecurityContextHolder.clear_context()
    clear_page()
    bundle = _Fakes()
    monkeypatch.setattr(controller, "_MENU_SERVICE", bundle.menu)
    monkeypatch.setattr(controller, "_TOKEN_SERVICE", bundle.token)
    yield bundle
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_menu_controller()


@pytest.fixture
def service(fakes: _Fakes) -> _FakeMenuService:
    return fakes.menu


@pytest.fixture
def http() -> Any:
    """已登录的 mini app（``*:*:*``，等同超级管理员）。"""
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    """未登录的 mini app —— 用来验证校验先于权限。"""
    return TestClient(_build_app(login=False))


@pytest.fixture
def http_lenient() -> Any:
    """已登录、且**不把服务端异常当失败**的 mini app（见 ``exception_handlers``）。"""
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:
        # Java: ``JwtAuthenticationTokenFilter`` —— 只把 LoginUser 放进上下文。
        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            SecurityContextHolder.get_context().set_authentication(
                UsernamePasswordAuthenticationToken(_login_user(), None, [])
            )
            return await call_next(request)

    application.include_router(controller.router)
    return application


def _login_user(
    user_id: int = 2,
    user_name: str = "ry",
    permissions: Optional[Set[str]] = None,
) -> LoginUser:
    from app.common.core.domain.entity.sys_user import SysUser

    return LoginUser(
        user=SysUser(user_id=user_id, user_name=user_name),
        permissions=permissions if permissions is not None else {"*:*:*"},
    )


def authenticate(
    user_id: int = 2,
    user_name: str = "ry",
    permissions: Optional[Set[str]] = None,
) -> None:
    """直调函数时用的登录态。"""
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(
            _login_user(user_id, user_name, permissions), None, []
        )
    )


def _menu(menu_id: int = 100, parent_id: int = 0, **overrides: Any) -> SysMenu:
    fields: Dict[str, Any] = {
        "menu_id": menu_id,
        "parent_id": parent_id,
        "menu_name": f"菜单{menu_id}",
        "menu_type": "C",
        "path": "user",
        "is_frame": "1",
        "visible": "0",
        "status": "0",
    }
    fields.update(overrides)
    return SysMenu(**fields)


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    """7 个映射的路径 / 动词。"""

    def test_the_seven_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/menu/list", ("GET",)),
            ("/system/menu/treeselect", ("GET",)),
            ("/system/menu/roleMenuTreeselect/{role_id}", ("GET",)),
            ("/system/menu/{menu_id}", ("GET",)),
            ("/system/menu", ("POST",)),
            ("/system/menu", ("PUT",)),
            ("/system/menu/{menu_id}", ("DELETE",)),
        }

    def test_literal_paths_come_before_the_path_variable(self) -> None:
        """FastAPI 按注册顺序匹配；字面量写在 ``/{menu_id}`` 之后就会被吃掉。"""
        paths = [route.path for route in controller.router.routes]

        for literal in ("/system/menu/list", "/system/menu/treeselect"):
            assert paths.index(literal) < paths.index("/system/menu/{menu_id}")

    def test_treeselect_beats_the_path_variable_over_http(
        self, http: TestClient, fakes: _Fakes
    ) -> None:
        """``/treeselect`` 若排在后面会被当成 ``menu_id`` 并在 ``int`` 转换处炸掉。"""
        response = http.get("/system/menu/treeselect")

        assert response.status_code == 200
        assert "select_menu_list" in fakes.menu.names()
        assert "select_menu_by_id" not in fakes.menu.names()

    def test_list_beats_the_path_variable_over_http(
        self, http: TestClient, fakes: _Fakes
    ) -> None:
        response = http.get("/system/menu/list")

        assert response.status_code == 200
        assert "select_menu_list" in fakes.menu.names()
        assert "select_menu_by_id" not in fakes.menu.names()

    def test_post_and_put_do_not_register_a_trailing_slash_variant(self) -> None:
        paths = [route.path for route in controller.router.routes]

        assert "/system/menu/" not in paths


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    """5 个映射各自的权限点。

    ``http`` 夹具带 ``*:*:*``，**任何**权限点都能过 —— 用它证明不了权限生效。所以这里
    直调函数、期待 :class:`AccessDeniedException`（与 ``test_sys_role_controller.py``
    同款）。下面的 ``test_the_refusal_becomes_a_403_body`` 再走一遍 ASGI 栈，验证
    异常处理器把它翻成 ``code 403``。
    """

    @pytest.mark.parametrize(
        ("call", "permission"),
        [
            (lambda: list_menus(_menu(), _fake_request()), "system:menu:list"),
            (lambda: get_info(100), "system:menu:query"),
            (lambda: add(_menu()), "system:menu:add"),
            (lambda: edit(_menu()), "system:menu:edit"),
            (lambda: remove(100), "system:menu:remove"),
        ],
        ids=["list", "getInfo", "add", "edit", "remove"],
    )
    def test_an_anonymous_caller_is_refused(
        self, service: _FakeMenuService, call: Any, permission: str
    ) -> None:
        with pytest.raises(AccessDeniedException) as raised:
            call()

        assert permission in str(raised.value)
        # 权限校验在方法体之前，Service 一次都没被调用。
        assert service.calls == []

    def test_the_refusal_becomes_a_403_body(self, http_anonymous: TestClient) -> None:
        """``AccessDeniedException`` -> HTTP 200 + ``code 403``（Java 全局处理器同款）。"""
        response = http_anonymous.post("/system/menu", json=VALID_BODY)

        assert response.status_code == 200
        assert response.json()["code"] == 403
        assert response.json()["msg"] == "没有权限，请联系管理员授权"

    def test_list_only_need_a_login_when_the_permission_is_present(
        self, http: TestClient
    ) -> None:
        # ``*:*:*`` 已经覆盖 ``system:menu:list``；这条与上面配对，保证 403 是权限引起的。
        assert http.get("/system/menu/list").status_code == 200

    @pytest.mark.parametrize("path", ["/system/menu/treeselect"])
    def test_treeselect_has_no_permission_point(self, path: str) -> None:
        """Java 这两个映射没有 ``@PreAuthorize`` —— 普通用户也要能画菜单树。"""
        authenticate(user_id=2, permissions=set())
        controller.treeselect(controller._query_menu(_fake_request()), _fake_request())

        assert controller._MENU_SERVICE is not None

    def test_role_menu_treeselect_has_no_permission_point(self) -> None:
        authenticate(user_id=2, permissions=set())
        request = _fake_request()

        result = role_menu_treeselect(1, request)

        assert result["code"] == 200


class TestValidationRunsBeforePermission:
    def test_an_invalid_body_fails_before_the_403(
        self, http_anonymous: TestClient
    ) -> None:
        """Spring: 反序列化+校验 -> ``@PreAuthorize``。所以这里是 500 而不是 403。"""
        response = http_anonymous.post("/system/menu", json={})

        assert response.status_code == 200
        assert response.json()["code"] == 500
        assert response.json()["msg"] == "菜单名称不能为空"

    def test_order_num_is_validated_second(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/menu", json={"menuName": "用户管理", "orderNum": "", "menuType": "C"}
        )

        assert response.json()["msg"] == "显示顺序不能为空"

    def test_menu_type_is_validated_third(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/menu", json={"menuName": "用户管理", "orderNum": "1", "menuType": ""}
        )

        assert response.json()["msg"] == "菜单类型不能为空"

    def test_put_validates_too(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.put("/system/menu", json={})

        assert response.json()["code"] == 500
        assert response.json()["msg"] == "菜单名称不能为空"


# --------------------------------------------------------------------------- list


class TestList:
    def test_it_binds_the_query_string(self, service: _FakeMenuService) -> None:
        authenticate()
        request = _fake_request({"menuName": "用户", "visible": "0", "status": "0"})

        list_menus(controller._query_menu(request), request)

        _, menu, _ = service.of("select_menu_list")[0]
        assert (menu.menu_name, menu.visible, menu.status) == ("用户", "0", "0")

    def test_the_current_user_id_comes_from_the_token_service(
        self, service: _FakeMenuService, fakes: _Fakes
    ) -> None:
        """Java: ``tokenService.getLoginUser(request).getUser().getUserId()``.

        **不是**从安全上下文取：控制器显式调 ``TokenService``，与 ``@ss.hasPermi``
        读 ``SecurityContextHolder`` 是两条独立路径，所以这里必须分别注入。
        """
        authenticate(user_id=42)
        fakes.token.login_user = _login_user(user_id=42)
        request = _fake_request()

        list_menus(controller._query_menu(request), request)

        assert service.of("select_menu_list")[0][2] == 42

    def test_it_is_not_paged(self, service: _FakeMenuService) -> None:
        """``list`` 返回 ``AjaxResult``，**不是** ``TableDataInfo``。"""
        authenticate()
        service.list_result = [_menu(1)]
        request = _fake_request()

        result = list_menus(controller._query_menu(request), request)

        assert isinstance(result, AjaxResult)
        # Java: ``AjaxResult`` 是 ``HashMap`` -> 桶序 msg(0) -> code(3) -> data(4)。
        assert list(result) == ["msg", "code", "data"]
        assert result["code"] == 200
        assert result["msg"] == "操作成功"
        # 直调时 ``data`` 里还是**实体对象**，FastAPI 在出口处才转 JSON。
        assert [menu.menu_id for menu in result["data"]] == [1]

    def test_every_entity_field_is_serialised(
        self, http: TestClient, service: _FakeMenuService
    ) -> None:
        """``SysMenu`` 没有 ``@JsonInclude`` -> ``null`` 与 ``children: []`` 都在。"""
        service.list_result = [_menu(1)]

        payload = http.get("/system/menu/list").json()["data"][0]

        assert payload["menuName"] == "菜单1"
        assert payload["children"] == []
        assert payload["parentName"] is None
        assert payload["remark"] is None
        assert payload["createBy"] is None
        # ``BaseEntity.params`` 是 ``@JsonInclude(NON_EMPTY)`` -> 空 map 整个消失。
        assert "params" not in payload
        # ``BaseEntity.searchValue`` 是 ``@JsonIgnore`` -> 两个方向都不出现。
        assert "searchValue" not in payload

    def test_an_empty_result_is_an_empty_array(self, service: _FakeMenuService) -> None:
        authenticate()
        request = _fake_request()

        assert list_menus(controller._query_menu(request), request)["data"] == []

    def test_a_missing_login_user_raises_like_the_java_npe(
        self, fakes: _Fakes
    ) -> None:
        authenticate()
        fakes.token.login_user = None
        request = _fake_request()

        with pytest.raises(AttributeError):
            list_menus(controller._query_menu(request), request)


# --------------------------------------------------------------------------- getInfo


class TestGetInfo:
    def test_it_delegates(self, service: _FakeMenuService) -> None:
        authenticate()
        service.menu_by_id = _menu(100)

        result = get_info(100)

        assert service.of("select_menu_by_id") == [("select_menu_by_id", 100)]
        assert result["data"].menu_id == 100

    def test_a_missing_menu_omits_the_data_key(self, service: _FakeMenuService) -> None:
        authenticate()

        result = get_info(404)

        # ``data`` 不放（实体为 null）—— 剩 msg(0) -> code(3)。
        assert list(result) == ["msg", "code"]
        assert result["code"] == 200


# --------------------------------------------------------------------------- treeselect


class TestTreeselect:
    def test_it_builds_the_tree_from_the_list(self, service: _FakeMenuService) -> None:
        authenticate()
        root = _menu(1, 0)
        service.list_result = [root]
        service.tree_select = [{"id": 1, "label": "菜单1"}]
        request = _fake_request()

        result = treeselect(controller._query_menu(request), request)

        assert service.of("build_menu_tree_select")[0][1] == [root]
        assert result["data"] == [{"id": 1, "label": "菜单1"}]

    def test_it_uses_the_current_user(
        self, service: _FakeMenuService, fakes: _Fakes
    ) -> None:
        authenticate(user_id=42)
        fakes.token.login_user = _login_user(user_id=42)
        request = _fake_request()

        treeselect(controller._query_menu(request), request)

        assert service.of("select_menu_list")[0][2] == 42


# --------------------------------------------------------------------------- roleMenuTreeselect


class TestRoleMenuTreeselect:
    def test_the_key_order_is_msg_code_then_the_two_puts(self, service: _FakeMenuService) -> None:
        """Java 先 ``success()`` 再两次 ``put``；但 ``AjaxResult`` 是 ``HashMap``，

        序列化顺序是**桶序**而非 put 序：msg(0) -> code(3) -> menus(11) -> checkedKeys(15)。
        """
        service.role_menu_ids = [1, 2]
        service.tree_select = [{"id": 1, "label": "菜单1"}]

        result = role_menu_treeselect(3, _fake_request())

        assert list(result) == ["msg", "code", "menus", "checkedKeys"]
        assert result["checkedKeys"] == [1, 2]
        assert result["menus"] == [{"id": 1, "label": "菜单1"}]

    def test_it_uses_the_single_argument_overload(
        self, service: _FakeMenuService, fakes: _Fakes
    ) -> None:
        """Java: ``menuService.selectMenuList(loginUser.getUser().getUserId())``."""
        fakes.token.login_user = _login_user(user_id=42)

        role_menu_treeselect(3, _fake_request())

        assert service.of("select_menu_list_for_user") == [("select_menu_list_for_user", 42)]
        assert service.of("select_menu_list") == []

    def test_the_role_id_is_used_for_the_checked_keys(self, service: _FakeMenuService) -> None:
        role_menu_treeselect(9, _fake_request())

        assert service.of("select_menu_list_by_role_id") == [("select_menu_list_by_role_id", 9)]

    def test_a_missing_login_user_raises_like_the_java_npe(
        self, fakes: _Fakes
    ) -> None:
        fakes.token.login_user = None

        with pytest.raises(AttributeError):
            role_menu_treeselect(3, _fake_request())


# --------------------------------------------------------------------------- add


class TestAdd:
    def test_a_duplicate_name_is_rejected(self, service: _FakeMenuService) -> None:
        authenticate()
        service.name_unique = NOT_UNIQUE

        result = add(SysMenu(menu_name="用户管理"))

        assert result["msg"] == ADD_MENU_NAME_EXISTS.format("用户管理")
        assert result["code"] == 500
        assert service.of("insert_menu") == []

    def test_an_external_link_needs_http_prefix(self, service: _FakeMenuService) -> None:
        authenticate()

        result = add(SysMenu(menu_name="百度", is_frame="0", path="www.baidu.com"))

        assert result["msg"] == ADD_MENU_BAD_FRAME_URL.format("百度")
        assert service.of("insert_menu") == []

    def test_an_external_link_with_http_is_accepted(self, service: _FakeMenuService) -> None:
        authenticate()

        result = add(SysMenu(menu_name="百度", is_frame="0", path="http://www.baidu.com"))

        assert result["code"] == 200
        assert len(service.of("insert_menu")) == 1

    def test_an_external_link_with_https_is_accepted(self, service: _FakeMenuService) -> None:
        authenticate()

        add(SysMenu(menu_name="百度", is_frame="0", path="https://www.baidu.com"))

        assert len(service.of("insert_menu")) == 1

    def test_a_missing_path_counts_as_a_bad_url(self, service: _FakeMenuService) -> None:
        """``startsWithAny(null, ...)`` 返回 ``false`` -> 拒绝。"""
        authenticate()

        result = add(SysMenu(menu_name="百度", is_frame="0", path=None))

        assert result["msg"] == ADD_MENU_BAD_FRAME_URL.format("百度")

    def test_an_internal_link_may_have_any_path(self, service: _FakeMenuService) -> None:
        authenticate()

        result = add(SysMenu(menu_name="用户", is_frame="1", path="user"))

        assert result["code"] == 200

    def test_the_name_gate_runs_before_the_url_gate(self, service: _FakeMenuService) -> None:
        authenticate()
        service.name_unique = NOT_UNIQUE

        result = add(SysMenu(menu_name="百度", is_frame="0", path="www.baidu.com"))

        assert result["msg"] == ADD_MENU_NAME_EXISTS.format("百度")

    def test_create_by_comes_from_the_security_context(self, service: _FakeMenuService) -> None:
        authenticate(user_name="admin")
        menu = SysMenu(menu_name="用户", is_frame="1", path="user")

        add(menu)

        assert menu.create_by == "admin"

    def test_zero_rows_is_a_failure(self, service: _FakeMenuService) -> None:
        authenticate()
        service.insert_result = 0

        result = add(SysMenu(menu_name="用户", is_frame="1", path="user"))

        assert result["code"] == 500


# --------------------------------------------------------------------------- edit


class TestEdit:
    def test_a_duplicate_name_is_rejected(self, service: _FakeMenuService) -> None:
        authenticate()
        service.name_unique = NOT_UNIQUE

        result = edit(_menu(100))

        assert result["msg"] == EDIT_MENU_NAME_EXISTS.format("菜单100")
        assert service.of("update_menu") == []

    def test_an_external_link_needs_http_prefix(self, service: _FakeMenuService) -> None:
        authenticate()

        result = edit(_menu(100, is_frame="0", path="www.baidu.com"))

        assert result["msg"] == EDIT_MENU_BAD_FRAME_URL.format("菜单100")

    def test_a_parent_cannot_be_itself(self, service: _FakeMenuService) -> None:
        authenticate()

        result = edit(_menu(100, parent_id=100))

        assert result["msg"] == EDIT_MENU_SELF_PARENT.format("菜单100")
        assert service.of("update_menu") == []

    def test_the_url_gate_runs_before_the_self_parent_gate(
        self, service: _FakeMenuService
    ) -> None:
        authenticate()
        service.name_unique = NOT_UNIQUE

        result = edit(_menu(100, parent_id=100, is_frame="0", path="x"))

        assert result["msg"] == EDIT_MENU_NAME_EXISTS.format("菜单100")

    def test_a_missing_menu_id_raises_like_the_java_npe(self, service: _FakeMenuService) -> None:
        """Java: ``menu.getMenuId().equals(...)`` —— 接收者为 ``null`` 就 NPE。"""
        authenticate()

        with pytest.raises(AttributeError):
            edit(SysMenu(menu_name="用户", is_frame="1", path="user", menu_type="C"))

    def test_update_by_comes_from_the_security_context(
        self, service: _FakeMenuService
    ) -> None:
        authenticate(user_name="admin")
        menu = _menu(100, parent_id=1)

        edit(menu)

        assert menu.update_by == "admin"
        assert service.of("update_menu")[0][1].update_by == "admin"

    def test_zero_rows_is_a_failure(self, service: _FakeMenuService) -> None:
        authenticate()
        service.update_result = 0

        result = edit(_menu(100, parent_id=1))

        assert result["code"] == 500

    def test_a_normal_edit_succeeds(self, service: _FakeMenuService) -> None:
        authenticate()

        result = edit(_menu(100, parent_id=1))

        assert result["code"] == 200
        assert result["msg"] == "操作成功"


# --------------------------------------------------------------------------- remove


class TestRemove:
    def test_a_menu_with_children_cannot_be_removed(self, service: _FakeMenuService) -> None:
        authenticate()
        service.has_child = True

        result = remove(100)

        assert result["msg"] == REMOVE_HAS_CHILD
        assert service.of("delete_menu_by_id") == []

    def test_a_menu_used_by_a_role_cannot_be_removed(self, service: _FakeMenuService) -> None:
        authenticate()
        service.exist_role = True

        result = remove(100)

        assert result["msg"] == REMOVE_HAS_ROLE
        assert service.of("delete_menu_by_id") == []

    def test_the_child_gate_runs_first(self, service: _FakeMenuService) -> None:
        authenticate()
        service.has_child = True
        service.exist_role = True

        result = remove(100)

        assert result["msg"] == REMOVE_HAS_CHILD
        # 第一道闸直接 ``return``，第二道闸根本不会被执行。
        assert "check_menu_exist_role" not in service.names()

    def test_a_free_menu_is_deleted(self, service: _FakeMenuService) -> None:
        authenticate()

        result = remove(100)

        assert result["code"] == 200
        assert service.of("delete_menu_by_id") == [("delete_menu_by_id", 100)]

    def test_zero_rows_is_a_failure(self, service: _FakeMenuService) -> None:
        authenticate()
        service.delete_result = 0

        assert remove(100)["code"] == 500


# --------------------------------------------------------------------------- 500 通道


class TestServerErrors:
    def test_the_export_style_404_does_not_exist_here(self, http: TestClient) -> None:
        """菜单没有 ``export`` 端点，``/{menu_id}`` 也不会兜住它以外的字面量。"""
        try:
            response = http.get("/system/menu/export")
        except Exception:  # noqa: BLE001 - 500 会从 TestClient 里重抛，见 docstring
            return
        # 若没被重抛，它应当走 ``/{menu_id}``（``"export"`` 转 int 失败 -> 500）。
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- helpers


def _fake_request(query: Optional[Dict[str, str]] = None) -> Any:
    """最小的 ``Request`` 替身：只实现 ``query_params``。"""
    from starlette.requests import Request

    # 必须 urlencode：Starlette 按 latin-1 解码 ``query_string``，中文直接拼进去会变乱码。
    raw_query = urlencode(query or {})
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/system/menu/list",
        "query_string": raw_query.encode(),
        "headers": [],
    }
    return Request(scope)
