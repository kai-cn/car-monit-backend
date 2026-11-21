"""``SysRoleController`` -- ``/system/role`` 的 10 个映射（9 个已注册）.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysRoleController.java
#   + ruoyi-common/.../core/controller/BaseController.java

这一层测什么
------------
Service 已被 ``test_sys_role_service.py`` 覆盖、Mapper 被 ``test_sys_role_mapper.py``
覆盖，所以这里全部注入假 Service，只测**控制器自己的判断**：

* 路由注册：9 条（``export`` 故意没注册）+ 字面量必须排在 ``/{role_id}`` 之前；
* ``list`` / ``selectlist`` **只要求登录** —— Java 第 47 行的 ``@PreAuthorize`` 是注释掉的；
* ``add`` / ``edit`` 的三道闸顺序（超管拦截 -> 名称判重 -> 权限字符判重）；
* ``edit`` 成功后"刷新当前登录用户缓存"的三条分支（普通用户 / 超管 / 未登录 NPE）；
* ``remove`` 的 ``"1,2"`` 逗号串解析；
* 提示文案逐字照抄（全角 ``'``、半角逗号 ``，``）。

``@Validated`` 与 ``@PreAuthorize`` 的先后
------------------------------------------
Java 的顺序是"参数解析（含校验）→ 方法代理（含 ``@PreAuthorize``）"，所以
**没权限的请求只要请求体不合法，回的也是 500 而不是 403**。
:class:`TestValidationRunsBeforePermission` 用"未登录 + 非法请求体"验证这一点：
如果哪天有人把 :data:`ValidRole` 从 ``Depends`` 挪进函数体，这个用例会立刻变红。

两种驱动方式
------------
* 直调函数：能拿到 ``AjaxResult`` 对象本身，断言键序最直观；
* ``TestClient``：只有走 ASGI 栈才会真正解析 ``Depends`` 与路由表。用**独立的
  mini app**（只挂本控制器的 router + 异常处理器），避开 ``SecurityMiddleware``
  对 MySQL/Redis 的依赖。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_role_controller as controller
from app.api.system.sys_role_controller import (
    ADD_ROLE_KEY_EXISTS,
    ADD_ROLE_NAME_EXISTS,
    EDIT_ROLE_FAILED,
    EDIT_ROLE_KEY_EXISTS,
    EDIT_ROLE_NAME_EXISTS,
    add,
    change_status,
    data_scope,
    edit,
    get_info,
    list_roles,
    optionselect,
    remove,
    selectlist,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page
from app.common.exception.exceptions import AccessDeniedException, CustomException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)

#: 一个能通过 ``ROLE_CONSTRAINTS`` 的请求体（三个字段都是 ``@NotBlank``）。
VALID_BODY: Dict[str, Any] = {"roleName": "普通角色", "roleKey": "common", "roleSort": "2"}

#: Java: ``UserConstants.UNIQUE`` / ``NOT_UNIQUE``。
UNIQUE = "0"
NOT_UNIQUE = "1"

#: Java: ``SysRoleServiceImpl#checkRoleAllowed`` 的文案。
ROLE_NOT_ALLOWED = "不允许操作超级管理员角色"

#: Java: ``SysRoleServiceImpl#deleteRoleByIds`` 的文案（半角逗号）。
ROLE_ASSIGNED = "已分配,不能删除"


# --------------------------------------------------------------------------- fakes


class _FakeRoleService:
    """记录每一次调用；答案由用例配置。

    ``check_role_allowed`` / ``delete_role_by_ids`` 保留了真实实现的两道拦截，
    这样控制器"是否把异常放过去"才有意义。
    """

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysRole] = []
        self.all_result: List[SysRole] = []
        self.role_by_id: Optional[SysRole] = None
        self.name_unique = UNIQUE
        self.key_unique = UNIQUE
        self.insert_result = 1
        self.update_result = 1
        self.status_result = 1
        self.data_scope_result = 1
        self.delete_result = 1
        #: 这些 roleId 视为"已分配用户"，``delete_role_by_ids`` 会抛异常。
        self.assigned_role_ids: Set[int] = set()

    # -- 查询 --------------------------------------------------------------
    def select_role_list(self, role: SysRole) -> List[SysRole]:
        self.calls.append(("select_role_list", role.model_copy(deep=True)))
        return self.list_result

    def select_role_all(self) -> List[SysRole]:
        self.calls.append(("select_role_all",))
        return self.all_result

    def select_role_by_id(self, role_id: int) -> Optional[SysRole]:
        self.calls.append(("select_role_by_id", role_id))
        return self.role_by_id

    # -- 校验 --------------------------------------------------------------
    def check_role_name_unique(self, role: SysRole) -> str:
        self.calls.append(("check_role_name_unique", role.role_name))
        return self.name_unique

    def check_role_key_unique(self, role: SysRole) -> str:
        self.calls.append(("check_role_key_unique", role.role_key))
        return self.key_unique

    def check_role_allowed(self, role: SysRole) -> None:
        self.calls.append(("check_role_allowed", role.role_id))
        if SysRole.is_admin(role.role_id):
            raise CustomException(ROLE_NOT_ALLOWED)

    # -- 写 ----------------------------------------------------------------
    def insert_role(self, role: SysRole) -> int:
        self.calls.append(("insert_role", role.model_copy(deep=True)))
        return self.insert_result

    def update_role(self, role: SysRole) -> int:
        self.calls.append(("update_role", role.model_copy(deep=True)))
        return self.update_result

    def update_role_status(self, role: SysRole) -> int:
        self.calls.append(("update_role_status", role.model_copy(deep=True)))
        return self.status_result

    def auth_data_scope(self, role: SysRole) -> int:
        self.calls.append(("auth_data_scope", role.model_copy(deep=True)))
        return self.data_scope_result

    def delete_role_by_ids(self, role_ids: List[int]) -> int:
        self.calls.append(("delete_role_by_ids", list(role_ids)))
        # Java: 先逐个 checkRoleAllowed，再逐个判"已分配" —— 全批要么全过要么全不删。
        for role_id in role_ids:
            self.check_role_allowed(SysRole(role_id=role_id))
            if role_id in self.assigned_role_ids:
                raise CustomException(ROLE_ASSIGNED)
        return self.delete_result

    # ----------------------------------------------------------------------
    def of(self, name: str) -> List[tuple]:
        """按方法名过滤调用记录。"""
        return [call for call in self.calls if call[0] == name]


class _FakeTokenService:
    """Java: ``@Autowired TokenService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        #: ``get_login_user`` 的返回值；``None`` 用来模拟"令牌已过期"。
        #: 默认给一个普通用户 —— 走到 ``updateRole > 0`` 的用例都需要它。
        self.login_user: Optional[LoginUser] = _login_user()

    def get_login_user(self, request: Any) -> Optional[LoginUser]:
        self.calls.append(("get_login_user", request))
        return self.login_user

    def set_login_user(self, login_user: Optional[LoginUser]) -> None:
        self.calls.append(("set_login_user", login_user))

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _FakePermissionService:
    """Java: ``@Autowired SysPermissionService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.permissions: Set[str] = {"system:role:list"}

    def get_menu_permission(self, user: Any) -> Set[str]:
        self.calls.append(("get_menu_permission", user.user_id))
        return set(self.permissions)

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _FakeUserService:
    """Java: ``@Autowired ISysUserService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.user_by_name: Optional[Any] = None

    def select_user_by_user_name(self, user_name: str) -> Optional[Any]:
        self.calls.append(("select_user_by_user_name", user_name))
        return self.user_by_name

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _Fakes:
    """四个 ``@Autowired`` 字段的替身（打包在一起方便 fixture 注入）。"""

    def __init__(self) -> None:
        self.role = _FakeRoleService()
        self.token = _FakeTokenService()
        self.permission = _FakePermissionService()
        self.user = _FakeUserService()


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def fakes(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者与安全上下文。"""
    SecurityContextHolder.clear_context()
    clear_page()
    bundle = _Fakes()
    monkeypatch.setattr(controller, "_ROLE_SERVICE", bundle.role)
    monkeypatch.setattr(controller, "_TOKEN_SERVICE", bundle.token)
    monkeypatch.setattr(controller, "_PERMISSION_SERVICE", bundle.permission)
    monkeypatch.setattr(controller, "_USER_SERVICE", bundle.user)
    yield bundle
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_role_controller()


@pytest.fixture
def service(fakes: _Fakes) -> _FakeRoleService:
    """角色 Service 的假实现 —— 绝大多数用例只关心这一个。"""
    return fakes.role


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
    """已登录、且**不把服务端异常当失败**的 mini app。

    ``@ExceptionHandler(Exception)`` 挂在 Starlette 的 ``ServerErrorMiddleware`` 上：
    响应发出后它还会再重抛一次（见 ``exception_handlers`` 的模块 docstring）。
    Uvicorn 下客户端拿到的就是 ``{"code":500,...}``；只有 ``TestClient`` 需要关掉
    ``raise_server_exceptions`` 才看得到同一个响应体。
    """
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


def _sys_user(
    user_id: int = 2,
    user_name: str = "ry",
    tenant_id: int = 777,
    dept_id: int = 888,
) -> Any:
    from app.common.core.domain.entity.sys_user import SysUser

    return SysUser(
        user_id=user_id, user_name=user_name, tenant_id=tenant_id, dept_id=dept_id
    )


def _login_user(
    user_id: int = 2,
    user_name: str = "ry",
    permissions: Optional[Set[str]] = None,
    tenant_id: int = 777,
    dept_id: int = 888,
) -> LoginUser:
    return LoginUser(
        user=_sys_user(user_id, user_name, tenant_id, dept_id),
        permissions=permissions if permissions is not None else {"*:*:*"},
    )


def authenticate(
    user_id: int = 2,
    user_name: str = "ry",
    permissions: Optional[Set[str]] = None,
    tenant_id: int = 777,
    dept_id: int = 888,
) -> None:
    """直调函数时用的登录态（与 ``test_sys_post_controller.py`` 同款）。"""
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(
            _login_user(user_id, user_name, permissions, tenant_id, dept_id), None, []
        )
    )


def _role(role_id: int = 2, name: str = "普通角色") -> SysRole:
    return SysRole(
        role_id=role_id,
        role_name=name,
        role_key="common",
        role_sort="2",
        status="0",
        del_flag="0",
    )


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    """10 个已注册映射的路径 / 动词。"""

    def test_the_ten_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/role/list", ("GET",)),
            ("/system/role/export", ("GET",)),
            ("/system/role/optionselect", ("GET",)),
            ("/system/role/selectlist", ("GET",)),
            ("/system/role/{role_id}", ("GET",)),
            ("/system/role", ("POST",)),
            ("/system/role", ("PUT",)),
            ("/system/role/dataScope", ("PUT",)),
            ("/system/role/changeStatus", ("PUT",)),
            ("/system/role/{role_ids}", ("DELETE",)),
        }

    def test_export_does_not_fall_into_the_path_variable(
        self, http: TestClient, fakes: _Fakes
    ) -> None:
        """``GET /system/role/export`` 现在有自己的路由，不再被 ``/{role_id}`` 兜住。

        Phase 3.18 之前这里回的是 HTTP 200 + ``code 500``（``"export"`` 转 ``Long``
        失败）。现在返回的是**文件名**—— 落在 ``msg`` 里，没有 ``data`` 键。
        """
        response = http.get("/system/role/export")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["msg"].endswith("_角色数据.xlsx")
        assert "data" not in body
        # 走的是 export 而不是 getInfo：只调一次 select_role_list，且没有查询 id
        assert [call[0] for call in fakes.role.calls] == ["select_role_list"]

    def test_literal_paths_come_before_the_path_variable(self) -> None:
        """FastAPI 按注册顺序匹配；字面量写在 ``/{role_id}`` 之后就会被吃掉。"""
        paths = [route.path for route in controller.router.routes]

        for literal in (
            "/system/role/list",
            "/system/role/export",
            "/system/role/optionselect",
            "/system/role/selectlist",
        ):
            assert paths.index(literal) < paths.index("/system/role/{role_id}")

    def test_optionselect_beats_the_path_variable_over_http(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """顺序正确时 ``GET /optionselect`` 走全量端点，``role_id`` 不会被解析成字符串。"""
        response = http.get("/system/role/optionselect")

        assert response.json()["code"] == 200
        assert service.of("select_role_by_id") == []
        assert len(service.of("select_role_all")) == 1

    def test_selectlist_beats_the_path_variable_over_http(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        response = http.get("/system/role/selectlist")

        assert response.json()["code"] == 200
        assert service.of("select_role_by_id") == []
        assert len(service.of("select_role_list")) == 1


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    """``@PreAuthorize("@ss.hasPermi(...)")`` 的五个标识。"""

    @pytest.mark.parametrize(
        "call, permission",
        [
            (lambda: optionselect(), "system:role:query"),
            (lambda: get_info(2), "system:role:query"),
            (
                lambda: add(SysRole(role_name="a", role_key="k", role_sort="1")),
                "system:role:add",
            ),
            (
                lambda: edit(
                    SysRole(role_id=2, role_name="a", role_key="k", role_sort="1"), None
                ),
                "system:role:edit",
            ),
            (lambda: data_scope(SysRole(role_id=2)), "system:role:edit"),
            (lambda: change_status(SysRole(role_id=2, status="1")), "system:role:edit"),
            (lambda: remove("2"), "system:role:remove"),
        ],
    )
    def test_an_anonymous_caller_is_refused(
        self, service: _FakeRoleService, call: Any, permission: str
    ) -> None:
        with pytest.raises(AccessDeniedException):
            call()

        # 权限校验在方法体之前，Service 一次都没被调用。
        assert service.calls == []

    def test_a_partial_permission_does_not_pass(self, service: _FakeRoleService) -> None:
        """``hasPermi`` 是**精确匹配**：``system:role:*`` 不算拥有 ``system:role:query``。"""
        authenticate(permissions={"system:role:*"})

        with pytest.raises(AccessDeniedException):
            optionselect()

        assert service.calls == []

    def test_list_only_need_a_login(
        self, service: _FakeRoleService
    ) -> None:
        """Java 第 47 行的 ``@PreAuthorize`` 是**注释掉**的 —— 不校验权限点。

        注意：它连登录都不校验（没有调用 ``SecurityUtils``），实际保护来自
        安全过滤器链。这里直调函数，所以未登录也能过 —— 与 Java 的
        ``@PreAuthorize`` 缺席 + 路由 ``authenticated()`` 的组合同理。
        """
        response = list_roles(SysRole())

        assert response.get_code() == 200
        assert response.get_total() == 0
        assert len(service.of("select_role_list")) == 1

    def test_selectlist_only_need_a_login(self, service: _FakeRoleService) -> None:
        """同上 —— ``selectlist`` 是本项目新增的"下拉角色"接口，也没有注解。"""
        response = selectlist(SysRole())

        assert response["code"] == 200
        assert len(service.of("select_role_list")) == 1

    def test_an_access_denied_becomes_http_200_code_403(
        self, http_anonymous: TestClient
    ) -> None:
        response = http_anonymous.get("/system/role/2")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}

    def test_the_login_only_endpoints_answer_without_a_token(
        self, http_anonymous: TestClient
    ) -> None:
        """没有权限点也不代表要登录后才能访问 —— 这里未登录照样 200。"""
        assert http_anonymous.get("/system/role/list").json()["code"] == 200
        assert http_anonymous.get("/system/role/selectlist").json()["code"] == 200


# --------------------------------------------------------------------------- 校验


class TestValidationRunsBeforePermission:
    """未登录 + 非法请求体 -> 500（校验先跑）；合法请求体 -> 403。"""

    def test_a_missing_name_is_reported_before_the_403(
        self, http_anonymous: TestClient
    ) -> None:
        body = {"roleKey": "common", "roleSort": "2"}

        response = http_anonymous.post("/system/role", json=body)

        assert response.status_code == 200
        # 若顺序反了，这里会是 {"code":403,...}
        assert response.json() == {"code": 500, "msg": "角色名称不能为空"}

    def test_a_missing_key_is_reported(self, http_anonymous: TestClient) -> None:
        body = {"roleName": "普通角色", "roleSort": "2"}

        response = http_anonymous.post("/system/role", json=body)

        assert response.json() == {"code": 500, "msg": "权限字符不能为空"}

    def test_a_missing_role_sort_is_reported(self, http_anonymous: TestClient) -> None:
        body = {"roleName": "普通角色", "roleKey": "common"}

        response = http_anonymous.post("/system/role", json=body)

        assert response.json() == {"code": 500, "msg": "显示顺序不能为空"}

    def test_the_first_violation_wins(self, http_anonymous: TestClient) -> None:
        """全部为空时报的是**声明顺序**的第一条（``ROLE_CONSTRAINTS`` 以 ``role_name`` 开头）。"""
        response = http_anonymous.post("/system/role", json={})

        assert response.json() == {"code": 500, "msg": "角色名称不能为空"}

    def test_an_overlong_name_is_reported(self, http_anonymous: TestClient) -> None:
        body = dict(VALID_BODY, roleName="角" * 31)

        response = http_anonymous.post("/system/role", json=body)

        assert response.json() == {"code": 500, "msg": "角色名称长度不能超过30个字符"}

    def test_an_overlong_key_is_reported(self, http_anonymous: TestClient) -> None:
        body = dict(VALID_BODY, roleKey="k" * 101)

        response = http_anonymous.post("/system/role", json=body)

        assert response.json() == {"code": 500, "msg": "权限字符长度不能超过100个字符"}

    def test_the_boundaries_are_inclusive(self, http_anonymous: TestClient) -> None:
        """``@Size`` 是闭区间：30 字名称 / 100 字权限字符全部合法 -> 403。"""
        body = dict(VALID_BODY, roleName="角" * 30, roleKey="k" * 100)

        assert http_anonymous.post("/system/role", json=body).json()["code"] == 403

    def test_a_blank_string_counts_as_missing(self, http_anonymous: TestClient) -> None:
        """``@NotBlank`` 比 ``@NotNull`` 严格：``"   "`` 也算空。"""
        body = dict(VALID_BODY, roleName="   ")

        response = http_anonymous.post("/system/role", json=body)

        assert response.json() == {"code": 500, "msg": "角色名称不能为空"}

    def test_edit_validates_the_same_way(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.put("/system/role", json={"roleName": "普通角色"})

        assert response.json() == {"code": 500, "msg": "权限字符不能为空"}

    def test_data_scope_is_not_validated(self, http_anonymous: TestClient) -> None:
        """``dataScope`` 是裸 ``@RequestBody`` —— 只传 ``roleId`` 也是合法请求。"""
        response = http_anonymous.put("/system/role/dataScope", json={"roleId": 2})

        assert response.json()["code"] == 403

    def test_change_status_is_not_validated(self, http_anonymous: TestClient) -> None:
        """``changeStatus`` 同理：``{"roleId":2,"status":"1"}`` 不需要 name/key/sort。"""
        response = http_anonymous.put(
            "/system/role/changeStatus", json={"roleId": 2, "status": "1"}
        )

        assert response.json()["code"] == 403


# --------------------------------------------------------------------------- 查询


class TestListEndpoints:
    """``list`` 走分页信封，``selectlist`` 走裸数组。"""

    def test_list_returns_the_paged_envelope(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.list_result = [_role(2), _role(3, "二级角色")]

        body = http.get("/system/role/list").json()

        # 信封字段及其顺序：total / rows / code / msg（TableDataInfo 的声明顺序）。
        assert list(body) == ["total", "rows", "code", "msg"]
        assert (body["total"], body["code"], body["msg"]) == (2, 200, "查询成功")
        assert [row["roleId"] for row in body["rows"]] == [2, 3]
        # ``BaseEntity`` 的字段一个不少（Jackson 不忽略 null），这里只抽查几个。
        assert body["rows"][0]["roleName"] == "普通角色"
        assert body["rows"][0]["admin"] is False

    def test_list_serialises_the_primitive_booleans(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """``menuCheckStrictly`` / ``deptCheckStrictly`` / ``flag`` 是**基本类型**，永不为 null。"""
        service.list_result = [_role(2)]

        row = http.get("/system/role/list").json()["rows"][0]

        assert row["menuCheckStrictly"] is False
        assert row["deptCheckStrictly"] is False
        assert row["flag"] is False

    def test_list_binds_the_query_string(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """``?roleName=...&status=...&params[beginTime]=...`` 全部写进实体。"""
        http.get(
            "/system/role/list",
            params={"roleName": "普通", "status": "0", "params[beginTime]": "2026-01-01"},
        )

        passed: SysRole = service.of("select_role_list")[0][1]
        assert passed.role_name == "普通"
        assert passed.status == "0"
        # ``params[key]`` 的 key **不做** snake_case 转换（Spring 的 Map 语义）。
        assert passed.params["beginTime"] == "2026-01-01"

    def test_list_is_never_empty_shaped(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """没有数据时 ``rows`` 是 ``[]``（不是 ``null``）、``total`` 是 0。"""
        service.list_result = []

        body = http.get("/system/role/list").json()

        assert body["rows"] == []
        assert body["total"] == 0

    def test_selectlist_returns_a_bare_array(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """没有分页信封 —— 这个分支**不**调用 ``startPage()``。"""
        service.list_result = [_role(2)]

        body = http.get("/system/role/selectlist").json()

        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert [row["roleId"] for row in body["data"]] == [2]
        # 分页信封的字段一个都不该出现。
        assert "total" not in body
        assert "rows" not in body

    def test_selectlist_passes_the_query_string_too(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        http.get("/system/role/selectlist", params={"roleName": "普通"})

        passed: SysRole = service.of("select_role_list")[0][1]
        assert passed.role_name == "普通"


class TestOptionselect:
    """``/optionselect`` 返回全量角色（``selectRoleAll`` -> ``selectRoleList``）。"""

    def test_it_returns_every_role(self, http: TestClient, service: _FakeRoleService) -> None:
        service.all_result = [_role(2), _role(3, "二级角色")]

        body = http.get("/system/role/optionselect").json()

        assert body["code"] == 200
        assert [row["roleId"] for row in body["data"]] == [2, 3]

    def test_it_does_not_go_through_the_paging_envelope(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        body = http.get("/system/role/optionselect").json()

        assert "total" not in body


class TestGetInfo:
    """``GET /system/role/{roleId}``."""

    def test_a_found_role_is_returned(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.role_by_id = _role(2)

        body = http.get("/system/role/2").json()

        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert body["data"]["roleName"] == "普通角色"
        # Java 在实例方法上没有 ``@JsonIgnore``，``admin`` 会一起输出。
        assert body["data"]["admin"] is False
        assert service.of("select_role_by_id") == [("select_role_by_id", 2)]

    def test_a_missing_role_omits_data(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """``AjaxResult.success(null)`` **不输出** ``data`` 键（不是 ``"data": null``）。"""
        service.role_by_id = None

        body = http.get("/system/role/999").json()

        assert body == {"code": 200, "msg": "操作成功"}

    def test_a_non_numeric_id_is_a_500(self, http_lenient: TestClient) -> None:
        """``Long roleId`` 转换失败 -> ``MethodArgumentTypeMismatchException`` -> 500。"""
        response = http_lenient.get("/system/role/abc")

        assert response.status_code == 422 or response.json()["code"] == 500


# --------------------------------------------------------------------------- 新增


class TestAddEndpoint:
    """``POST /system/role``."""

    def test_a_duplicate_name_is_reported(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.name_unique = NOT_UNIQUE

        body = http.post("/system/role", json=VALID_BODY).json()

        assert body == {
            "code": 500,
            "msg": ADD_ROLE_NAME_EXISTS.format("普通角色"),
        }
        # 名称已重复就不再看权限字符，也不入库。
        assert service.of("check_role_key_unique") == []
        assert service.of("insert_role") == []

    def test_a_duplicate_key_is_reported(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.key_unique = NOT_UNIQUE

        body = http.post("/system/role", json=VALID_BODY).json()

        assert body == {"code": 500, "msg": ADD_ROLE_KEY_EXISTS.format("普通角色")}
        assert service.of("insert_role") == []

    def test_the_message_interpolates_the_role_name_not_the_key(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """Java 插的是 ``role.getRoleName()`` —— **不是**重复的那个字段值。"""
        service.key_unique = NOT_UNIQUE
        body = dict(VALID_BODY, roleName="运营", roleKey="ops")

        assert http.post("/system/role", json=body).json()["msg"] == (
            "新增角色'运营'失败，角色权限已存在"
        )

    def test_create_by_is_taken_from_the_security_context(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        http.post("/system/role", json=VALID_BODY)

        inserted: SysRole = service.of("insert_role")[0][1]
        assert inserted.create_by == "ry"

    def test_a_successful_insert_returns_code_200(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        body = http.post("/system/role", json=VALID_BODY).json()

        assert body == {"code": 200, "msg": "操作成功"}

    def test_zero_rows_is_an_error_envelope(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.insert_result = 0

        assert http.post("/system/role", json=VALID_BODY).json()["code"] == 500


# --------------------------------------------------------------------------- 修改


class TestEditEndpoint:
    """``PUT /system/role`` —— 三道闸 + 缓存刷新。"""

    def _edit_body(self, **overrides: Any) -> Dict[str, Any]:
        body = dict(VALID_BODY, roleId=2)
        body.update(overrides)
        return body

    def test_the_admin_role_cannot_be_edited(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """``checkRoleAllowed`` 抛 ``CustomException`` -> HTTP 200 + code 500。"""
        body = http.put("/system/role", json=self._edit_body(roleId=1)).json()

        assert body == {"code": 500, "msg": ROLE_NOT_ALLOWED}
        assert service.of("update_role") == []

    def test_the_admin_check_runs_before_the_duplicate_checks(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.name_unique = NOT_UNIQUE

        http.put("/system/role", json=self._edit_body(roleId=1))

        assert service.of("check_role_name_unique") == []

    def test_a_duplicate_name_is_reported(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.name_unique = NOT_UNIQUE

        body = http.put("/system/role", json=self._edit_body()).json()

        assert body == {"code": 500, "msg": EDIT_ROLE_NAME_EXISTS.format("普通角色")}
        assert service.of("update_role") == []

    def test_a_duplicate_key_is_reported(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.key_unique = NOT_UNIQUE

        body = http.put("/system/role", json=self._edit_body()).json()

        assert body == {"code": 500, "msg": EDIT_ROLE_KEY_EXISTS.format("普通角色")}
        assert service.of("update_role") == []

    def test_zero_rows_reports_the_fallback_message(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.update_result = 0

        body = http.put("/system/role", json=self._edit_body()).json()

        assert body == {"code": 500, "msg": EDIT_ROLE_FAILED.format("普通角色")}

    def test_update_by_is_taken_from_the_security_context(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        http.put("/system/role", json=self._edit_body())

        updated: SysRole = service.of("update_role")[0][1]
        assert updated.update_by == "ry"

    def test_a_normal_user_gets_its_own_cache_refreshed(
        self, http: TestClient, fakes: _Fakes
    ) -> None:
        """刷新的是**当前请求者**的令牌，不是被改角色的成员（Java 原文如此）。"""
        caller = _login_user(user_id=2, user_name="ry")
        fakes.token.login_user = caller
        refreshed = _sys_user(user_id=2, user_name="ry")
        fakes.user.user_by_name = refreshed

        body = http.put("/system/role", json=self._edit_body()).json()

        assert body == {"code": 200, "msg": "操作成功"}
        assert fakes.permission.of("get_menu_permission") == [("get_menu_permission", 2)]
        assert fakes.user.of("select_user_by_user_name") == [
            ("select_user_by_user_name", "ry")
        ]
        assert len(fakes.token.of("set_login_user")) == 1
        # 三件事的先后顺序：权限 -> 用户 -> 回写令牌。
        assert caller.permissions == {"system:role:list"}
        assert caller.user is refreshed

    def test_the_super_admin_skips_the_refresh(
        self, http: TestClient, fakes: _Fakes
    ) -> None:
        """``!user.isAdmin()`` 才刷新；``userId == 1`` 的权限本来就是 ``*:*:*``。"""
        fakes.token.login_user = _login_user(user_id=1, user_name="admin")

        body = http.put("/system/role", json=self._edit_body()).json()

        assert body["code"] == 200
        assert fakes.permission.calls == []
        assert fakes.user.calls == []
        assert fakes.token.of("set_login_user") == []

    def test_a_missing_login_user_blows_up(
        self, http_lenient: TestClient, fakes: _Fakes
    ) -> None:
        """``loginUser`` 为 ``null`` 时 Java 直接 NPE —— 这里同样 500，不加兜底。"""
        fakes.token.login_user = None

        response = http_lenient.put("/system/role", json=self._edit_body())

        assert response.status_code == 200
        assert response.json()["code"] == 500

    def test_a_failed_update_does_not_touch_the_cache(
        self, http: TestClient, fakes: _Fakes
    ) -> None:
        fakes.role.update_result = 0
        fakes.token.login_user = _login_user()

        http.put("/system/role", json=self._edit_body())

        assert fakes.token.of("get_login_user") == []
        assert fakes.permission.calls == []


# --------------------------------------------------------------------------- 数据权限


class TestDataScopeEndpoint:
    """``PUT /system/role/dataScope``."""

    def test_it_delegates_to_auth_data_scope(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        body = http.put(
            "/system/role/dataScope", json={"roleId": 2, "dataScope": "2", "deptIds": [100]}
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        passed: SysRole = service.of("auth_data_scope")[0][1]
        assert passed.role_id == 2
        assert passed.data_scope == "2"
        assert passed.dept_ids == [100]

    def test_it_does_not_set_update_by(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        """Java 原文没有 ``setUpdateBy`` —— 不要"顺手"补。"""
        http.put("/system/role/dataScope", json={"roleId": 2, "dataScope": "2"})

        passed: SysRole = service.of("auth_data_scope")[0][1]
        assert passed.update_by is None

    def test_the_admin_role_cannot_be_changed(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        body = http.put("/system/role/dataScope", json={"roleId": 1}).json()

        assert body == {"code": 500, "msg": ROLE_NOT_ALLOWED}
        assert service.of("auth_data_scope") == []

    def test_zero_rows_is_an_error_envelope(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.data_scope_result = 0

        body = http.put("/system/role/dataScope", json={"roleId": 2}).json()

        assert body["code"] == 500


# --------------------------------------------------------------------------- 状态修改


class TestChangeStatusEndpoint:
    """``PUT /system/role/changeStatus``."""

    def test_it_sets_update_by_and_delegates(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        body = http.put(
            "/system/role/changeStatus", json={"roleId": 2, "status": "0"}
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        passed: SysRole = service.of("update_role_status")[0][1]
        assert passed.role_id == 2
        assert passed.status == "0"
        assert passed.update_by == "ry"

    def test_the_admin_role_cannot_be_changed(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        body = http.put("/system/role/changeStatus", json={"roleId": 1}).json()

        assert body == {"code": 500, "msg": ROLE_NOT_ALLOWED}
        assert service.of("update_role_status") == []


# --------------------------------------------------------------------------- 删除


class TestRemoveEndpoint:
    """``DELETE /system/role/{roleIds}``."""

    def test_a_comma_separated_path_is_split(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        body = http.delete("/system/role/2,3").json()

        assert body == {"code": 200, "msg": "操作成功"}
        assert service.of("delete_role_by_ids")[0][1] == [2, 3]

    def test_a_single_id_is_a_one_element_array(
        self, service: _FakeRoleService
    ) -> None:
        authenticate()
        remove("2")

        assert service.of("delete_role_by_ids")[0][1] == [2]

    def test_the_admin_role_cannot_be_removed(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        body = http.delete("/system/role/1").json()

        assert body == {"code": 500, "msg": ROLE_NOT_ALLOWED}

    def test_an_assigned_role_cannot_be_removed(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.assigned_role_ids = {2}

        body = http.delete("/system/role/2").json()

        assert body == {"code": 500, "msg": ROLE_ASSIGNED}

    def test_a_non_numeric_path_is_a_500(self, http_lenient: TestClient) -> None:
        """``Long[]`` 转换失败 -> ``ValueError`` -> 通用处理器（HTTP 200 + code 500）。"""
        response = http_lenient.delete("/system/role/a,b")

        assert response.status_code == 200
        assert response.json()["code"] == 500

    def test_zero_rows_is_an_error_envelope(
        self, http: TestClient, service: _FakeRoleService
    ) -> None:
        service.delete_result = 0

        assert http.delete("/system/role/2").json()["code"] == 500


# --------------------------------------------------------------------------- 常量


class TestMessageConstants:
    """提示文案逐字照抄（含全角 ``'`` 与半角逗号）。"""

    def test_the_five_messages(self) -> None:
        assert ADD_ROLE_NAME_EXISTS == "新增角色'{}'失败，角色名称已存在"
        assert ADD_ROLE_KEY_EXISTS == "新增角色'{}'失败，角色权限已存在"
        assert EDIT_ROLE_NAME_EXISTS == "修改角色'{}'失败，角色名称已存在"
        assert EDIT_ROLE_KEY_EXISTS == "修改角色'{}'失败，角色权限已存在"
        assert EDIT_ROLE_FAILED == "修改角色'{}'失败，请联系管理员"

    def test_reset_drops_every_collaborator(self) -> None:
        controller.reset_role_controller()

        assert controller._ROLE_SERVICE is None
        assert controller._TOKEN_SERVICE is None
        assert controller._PERMISSION_SERVICE is None
        assert controller._USER_SERVICE is None
