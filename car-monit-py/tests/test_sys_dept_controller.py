"""``SysDeptController`` -- ``/system/dept`` 的 11 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysDeptController.java
#   + ruoyi-common/.../core/controller/BaseController.java

这一层测什么
------------
Service 已经被 ``test_sys_dept_service.py`` 覆盖，Mapper 被 ``test_sys_dept_mapper.py``
覆盖，所以这里全部注入假 Service，只测**控制器自己的判断**：

* 路由注册顺序：六个字面量路径必须在 ``/{dept_id}`` 之前，否则 ``treeselect``
  会被当成 ``dept_id``（并且因为类型是 int 直接 422）；
* 11 个映射里只有 6 个带 ``@PreAuthorize`` —— 另外五个**登录即可**，含全量部门树；
* ``treeselectNew`` 的 ``flag`` 分支表（未知值落到 ``deptId = -1``，**不是**查全部）；
* ``edit`` 的三道闸顺序（判重 -> 上级不能是自己 -> 停用前不能有未停用子部门）；
* ``add`` / ``edit`` 的提示文案逐字照抄（含全角 ``！`` 与半角逗号）。

``@Validated`` 与 ``@PreAuthorize`` 的先后
------------------------------------------
Java 的顺序是"参数解析（含校验）→ 方法代理（含 ``@PreAuthorize``）"，所以
**没权限的请求只要请求体不合法，回的也是 500 而不是 403**。
:class:`TestValidationRunsBeforePermission` 用"未登录 + 非法请求体"直接验证这一点：
如果哪天有人把 ``ValidDept`` 从 ``Depends`` 挪进函数体，这个用例会立刻变红。

为什么分两种驱动方式
--------------------
* 直调函数：能拿到 ``AjaxResult`` 对象本身，断言键序最直观；
* ``TestClient``：只有走 ASGI 栈才会真正解析 ``Depends`` 与路由表。用**独立的
  mini app**（只挂本控制器的 router + 异常处理器），避开 ``SecurityMiddleware``
  对 MySQL/Redis 的依赖。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_dept_controller as controller
from app.api.system.sys_dept_controller import (
    ADD_DEPT_NAME_EXISTS,
    EDIT_DEPT_HAS_ACTIVE_CHILD,
    EDIT_DEPT_NAME_EXISTS,
    EDIT_DEPT_SELF_PARENT,
    REMOVE_HAS_CHILD,
    REMOVE_HAS_USER,
    UNIT_FLAG,
    _apply_flag,
    _is_excluded,
    _same_id,
    add,
    edit,
    exclude_child,
    get_company_list,
    get_info,
    get_list,
    list_depts,
    remove,
    role_dept_treeselect,
    treeselect,
    treeselect_new,
)
from app.common.constant.user_constants import DEPT_DISABLE
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.domain.tree_select import TreeSelect
from app.common.exception.exceptions import AccessDeniedException, CustomException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)

#: 一个能通过 ``DEPT_CONSTRAINTS`` 的请求体（``deptName`` / ``orderNum`` 是必填）。
VALID_BODY: Dict[str, Any] = {"deptName": "财务部", "orderNum": "1"}

#: 未登录时提示的文案由 ``SecurityUtils`` 抛出，五个"登录即可"的端点里有三个会用到。
NO_LOGIN = "获取用户账户异常"


# --------------------------------------------------------------------------- fakes


class _FakeDeptService:
    """记录每一次调用；答案由用例配置。"""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysDept] = []
        self.tree_result: List[TreeSelect] = []
        self.dept_by_id: Optional[SysDept] = None
        self.name_unique = "0"
        self.normal_children = 0
        self.child_count = 0
        self.user_count = 0
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        self.role_dept_ids: List[int] = []

    # -- 查询 --------------------------------------------------------------
    def select_dept_list(self, dept: SysDept) -> List[SysDept]:
        self.calls.append(("select_dept_list", dept.model_copy(deep=True)))
        return self.list_result

    def select_dept_by_id(self, dept_id: int) -> Optional[SysDept]:
        self.calls.append(("select_dept_by_id", dept_id))
        return self.dept_by_id

    def build_dept_tree_select(self, depts: Sequence[SysDept]) -> List[TreeSelect]:
        self.calls.append(("build_dept_tree_select", len(depts)))
        return self.tree_result

    def select_dept_list_by_role_id(self, role_id: int) -> List[int]:
        self.calls.append(("select_dept_list_by_role_id", role_id))
        return self.role_dept_ids

    def select_normal_children_dept_by_id(self, dept_id: int) -> int:
        self.calls.append(("select_normal_children_dept_by_id", dept_id))
        return self.normal_children

    def has_child_by_dept_id(self, dept_id: int) -> bool:
        self.calls.append(("has_child_by_dept_id", dept_id))
        return self.child_count > 0

    def check_dept_exist_user(self, dept_id: int) -> bool:
        self.calls.append(("check_dept_exist_user", dept_id))
        return self.user_count > 0

    def check_dept_name_unique(self, dept: SysDept) -> str:
        self.calls.append(("check_dept_name_unique", dept.dept_name))
        return self.name_unique

    # -- 写 ----------------------------------------------------------------
    def insert_dept(self, dept: SysDept) -> int:
        self.calls.append(("insert_dept", dept.model_copy(deep=True)))
        return self.insert_result

    def update_dept(self, dept: SysDept) -> int:
        self.calls.append(("update_dept", dept.model_copy(deep=True)))
        return self.update_result

    def delete_dept_by_id(self, dept_id: int) -> int:
        self.calls.append(("delete_dept_by_id", dept_id))
        return self.delete_result

    # ----------------------------------------------------------------------
    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者与安全上下文。"""
    SecurityContextHolder.clear_context()
    fake = _FakeDeptService()
    monkeypatch.setattr(controller, "_DEPT_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    controller.reset_dept_controller()


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
    响应发出后它还会再重抛一次（见 ``exception_handlers`` 的模块 docstring）。Uvicorn
    下客户端拿到的就是 ``{"code":500,...}``；只有 ``TestClient`` 需要关掉
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
                UsernamePasswordAuthenticationToken(
                    _login_user(), None, []
                )
            )
            return await call_next(request)

    application.include_router(controller.router)
    return application


def _login_user(
    user_id: int = 2,
    user_name: str = "ry",
    permissions: Optional[set] = None,
    tenant_id: int = 777,
    dept_id: int = 888,
) -> LoginUser:
    return LoginUser(
        user=_sys_user(user_id, user_name, tenant_id, dept_id),
        permissions=permissions if permissions is not None else {"*:*:*"},
    )


def _sys_user(user_id: int, user_name: str, tenant_id: int, dept_id: int) -> Any:
    from app.common.core.domain.entity.sys_user import SysUser

    return SysUser(
        user_id=user_id, user_name=user_name, tenant_id=tenant_id, dept_id=dept_id
    )


def authenticate(
    user_id: int = 2,
    user_name: str = "ry",
    permissions: Optional[set] = None,
    tenant_id: int = 777,
    dept_id: int = 888,
) -> None:
    """直调函数时用的登录态（与 ``test_sys_post_controller.py`` 同款）。"""
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(
            _login_user(user_id, user_name, permissions, tenant_id, dept_id), None, []
        )
    )


def _dept(dept_id: int, parent_id: Optional[int], name: str, ancestors: Optional[str]) -> SysDept:
    return SysDept(
        dept_id=dept_id, parent_id=parent_id, dept_name=name, ancestors=ancestors
    )


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    """11 个映射的路径 / 动词。"""

    def test_the_eleven_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/dept/list", ("GET",)),
            ("/system/dept/getList", ("GET",)),
            ("/system/dept/list/exclude/{dept_id}", ("GET",)),
            ("/system/dept/treeselect", ("GET",)),
            ("/system/dept/treeselectNew", ("GET",)),
            ("/system/dept/roleDeptTreeselect/{role_id}", ("GET",)),
            ("/system/dept/getCompanyList", ("GET",)),
            ("/system/dept/{dept_id}", ("GET",)),
            ("/system/dept", ("POST",)),
            ("/system/dept", ("PUT",)),
            ("/system/dept/{dept_id}", ("DELETE",)),
        }

    def test_literal_paths_come_before_the_path_variable(self) -> None:
        """FastAPI 按注册顺序匹配；字面量写在 ``/{dept_id}`` 之后就会被吃掉。"""
        paths = [route.path for route in controller.router.routes]

        for literal in (
            "/system/dept/list",
            "/system/dept/getList",
            "/system/dept/list/exclude/{dept_id}",
            "/system/dept/treeselect",
            "/system/dept/treeselectNew",
            "/system/dept/roleDeptTreeselect/{role_id}",
            "/system/dept/getCompanyList",
        ):
            assert paths.index(literal) < paths.index("/system/dept/{dept_id}")

    def test_treeselect_beats_the_path_variable_over_http(
        self, http: TestClient, service: Any
    ) -> None:
        """顺序正确时 ``GET /treeselect`` 走树端点，``dept_id`` 不会被解析成 "treeselect"。"""
        response = http.get("/system/dept/treeselect")

        assert response.json()["code"] == 200
        assert service.of("select_dept_by_id") == []


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    """``@PreAuthorize("@ss.hasPermi(...)")`` 的六个标识。"""

    @pytest.mark.parametrize(
        "call, permission",
        [
            (lambda: list_depts(SysDept()), "system:dept:list"),
            (lambda: exclude_child(100), "system:dept:list"),
            (lambda: get_info(100), "system:dept:query"),
            (lambda: add(SysDept(dept_name="a", order_num="1")), "system:dept:add"),
            (lambda: edit(SysDept(dept_id=1, dept_name="a", order_num="1")), "system:dept:edit"),
            (lambda: remove(100), "system:dept:remove"),
        ],
    )
    def test_an_anonymous_caller_is_refused(
        self, service: Any, call: Any, permission: str
    ) -> None:
        with pytest.raises(AccessDeniedException):
            call()

        # 权限校验在方法体之前，Service 一次都没被调用。
        assert service.calls == []

    def test_a_partial_permission_does_not_pass(self, service: Any) -> None:
        """``hasPermi`` 是**精确匹配**：``system:dept:*`` 不算拥有 ``system:dept:list``。"""
        authenticate(permissions={"system:dept:*"})

        with pytest.raises(AccessDeniedException):
            list_depts(SysDept())

        assert service.calls == []

    @pytest.mark.parametrize(
        "call",
        [
            lambda: get_list(SysDept()),
            lambda: treeselect(SysDept()),
            lambda: treeselect_new(SysDept(flag="allDept")),
            lambda: role_dept_treeselect(2),
            lambda: get_company_list(),
        ],
    )
    def test_five_endpoints_only_need_a_login(self, service: Any, call: Any) -> None:
        """Java 源码上这五个**没有** ``@PreAuthorize`` —— 任何登录用户都能拿全量部门树。"""
        response = call()

        assert response["code"] == 200
        assert service.calls != []

    def test_an_access_denied_becomes_http_200_code_403(
        self, http_anonymous: TestClient
    ) -> None:
        response = http_anonymous.get("/system/dept/100")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}

    def test_the_login_only_endpoints_answer_without_a_token(
        self, http_anonymous: TestClient
    ) -> None:
        """没有权限点也不代表要登录后才能访问 —— 这里未登录照样 200。"""
        assert http_anonymous.get("/system/dept/getList").json()["code"] == 200
        assert http_anonymous.get("/system/dept/treeselect").json()["code"] == 200
        assert http_anonymous.get("/system/dept/getCompanyList").json()["code"] == 200


# --------------------------------------------------------------------------- 校验


class TestValidationRunsBeforePermission:
    """未登录 + 非法请求体 -> 500（校验先跑）；合法请求体 -> 403。"""

    def test_a_missing_name_is_reported_before_the_403(
        self, http_anonymous: TestClient
    ) -> None:
        response = http_anonymous.post("/system/dept", json={"orderNum": "1"})

        assert response.status_code == 200
        # 若顺序反了，这里会是 {"code":403,...}
        assert response.json() == {"code": 500, "msg": "部门名称不能为空"}

    def test_a_missing_order_num_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post("/system/dept", json={"deptName": "财务部"})

        assert response.json() == {"code": 500, "msg": "显示顺序不能为空"}

    def test_the_first_violation_wins(self, http_anonymous: TestClient) -> None:
        """全部为空时报的是**声明顺序**的第一条（``DEPT_CONSTRAINTS`` 以 ``dept_name`` 开头）。"""
        response = http_anonymous.post("/system/dept", json={})

        assert response.json() == {"code": 500, "msg": "部门名称不能为空"}

    def test_an_overlong_name_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dept", json=dict(VALID_BODY, deptName="部" * 31)
        )

        assert response.json() == {"code": 500, "msg": "部门名称长度不能超过30个字符"}

    def test_an_overlong_phone_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dept", json=dict(VALID_BODY, phone="1" * 12)
        )

        assert response.json() == {"code": 500, "msg": "联系电话长度不能超过11个字符"}

    def test_a_malformed_email_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/dept", json=dict(VALID_BODY, email="not-an-email")
        )

        assert response.json() == {"code": 500, "msg": "邮箱格式不正确"}

    def test_an_overlong_email_is_reported(self, http_anonymous: TestClient) -> None:
        """``Email`` 排在 ``Size`` 之前：先过格式，再过长度。"""
        response = http_anonymous.post(
            "/system/dept", json=dict(VALID_BODY, email="a" * 45 + "@b.com")
        )

        assert response.json() == {"code": 500, "msg": "邮箱长度不能超过50个字符"}

    def test_the_boundaries_are_inclusive(self, http_anonymous: TestClient) -> None:
        """``@Size`` 是闭区间：30 字名字 / 11 位电话 / 50 字邮箱全部合法 -> 403。"""
        body = dict(
            VALID_BODY, deptName="部" * 30, phone="1" * 11, email="a" * 44 + "@b.com"
        )

        assert http_anonymous.post("/system/dept", json=body).json()["code"] == 403

    def test_a_blank_string_counts_as_missing(self, http_anonymous: TestClient) -> None:
        """``@NotBlank`` 比 ``@NotNull`` 严格：``"   "`` 也算空。"""
        response = http_anonymous.post(
            "/system/dept", json=dict(VALID_BODY, deptName="   ")
        )

        assert response.json() == {"code": 500, "msg": "部门名称不能为空"}

    def test_the_lax_email_rule_matches_hibernate(self, http_anonymous: TestClient) -> None:
        """``@Email`` 只校验 ``. {0,64}@域名``，**不**校验本地部分的字符集。

        Java 的 ``"a b@c.d"`` 是通过的；这里若"顺手收紧"就会拒绝 Java 接受的输入。
        """
        body = dict(VALID_BODY, email="a b@c.d")

        assert http_anonymous.post("/system/dept", json=body).json()["code"] == 403

    def test_a_blank_email_is_accepted(self, http_anonymous: TestClient) -> None:
        """Hibernate 的 ``@Email`` 对 ``""`` 返回 true。"""
        body = dict(VALID_BODY, email="")

        assert http_anonymous.post("/system/dept", json=body).json()["code"] == 403

    def test_edit_validates_the_same_way(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.put(
            "/system/dept", json={"deptId": 100, "deptName": "财务部"}
        )

        assert response.json() == {"code": 500, "msg": "显示顺序不能为空"}

    def test_the_query_endpoints_do_not_validate(self, http: TestClient) -> None:
        """``list`` / ``treeselect`` / ``treeselectNew`` 的形参没有 ``@Validated``。"""
        assert http.get("/system/dept/list").json()["code"] == 200
        assert http.get("/system/dept/treeselectNew?flag=allDept").json()["code"] == 200


# --------------------------------------------------------------------------- 列表


class TestListEndpoints:
    def test_the_query_string_is_bound_to_the_entity(
        self, http: TestClient, service: Any
    ) -> None:
        query = urlencode({"deptName": "财务", "status": "0", "parentId": "100"})

        response = http.get(f"/system/dept/list?{query}")

        assert response.json()["code"] == 200
        dept = service.of("select_dept_list")[0][1]
        assert (dept.dept_name, dept.status, dept.parent_id) == ("财务", "0", 100)

    def test_the_response_is_an_unpaged_array(
        self, http: TestClient, service: Any
    ) -> None:
        """``AjaxResult.success(List)``，**不是** ``TableDataInfo``（没有 total/rows）。"""
        service.list_result = [SysDept(dept_id=100, dept_name="总公司")]

        body = http.get("/system/dept/list").json()

        assert body.keys() == {"code", "msg", "data"}
        assert (body["code"], body["msg"]) == (200, "操作成功")
        assert [row["deptId"] for row in body["data"]] == [100]

    def test_an_empty_result_still_emits_the_data_key(
        self, http: TestClient, service: Any
    ) -> None:
        service.list_result = []

        assert http.get("/system/dept/list").json() == {
            "code": 200,
            "msg": "操作成功",
            "data": [],
        }

    def test_get_list_and_list_do_the_same_thing(self, service: Any) -> None:
        """两个映射的函数体一字不差，区别只在权限 —— 不要合并。"""
        authenticate()
        service.list_result = [SysDept(dept_id=100)]

        first = list_depts(SysDept())
        second = get_list(SysDept())

        assert first == second
        assert len(service.of("select_dept_list")) == 2


# --------------------------------------------------------------------------- 排除节点


class TestExcludeChild:
    def test_self_and_descendants_are_dropped(
        self, http: TestClient, service: Any
    ) -> None:
        service.list_result = [
            _dept(100, 0, "总公司", "0"),
            _dept(101, 100, "财务部", "0,100"),
            _dept(102, 101, "会计科", "0,100,101"),
            _dept(200, 0, "另一家公司", "0"),
        ]

        body = http.get("/system/dept/list/exclude/101").json()

        assert [row["deptId"] for row in body["data"]] == [100, 200]

    def test_the_query_carries_no_condition(self, service: Any) -> None:
        """Java: ``deptService.selectDeptList(new SysDept())`` —— 先查全量再在内存里筛。"""
        authenticate()
        service.list_result = []

        exclude_child(101)

        assert service.of("select_dept_list")[0][1] == SysDept()

    def test_a_null_ancestors_column_is_not_excluded(self) -> None:
        """``ArrayUtils.contains(null, ...)`` 返回 false —— 脏数据不会被排除。"""
        assert _is_excluded(_dept(300, 100, "脏数据", None), 101) is False

    def test_ancestors_is_split_on_commas_not_matched_as_substring(self) -> None:
        """``"0,1001"`` 里有 ``1001``，不含 ``100`` —— 按元素比，不是 ``in`` 子串。"""
        assert _is_excluded(_dept(1001, 100, "a", "0,1001"), 100) is False
        assert _is_excluded(_dept(1001, 100, "a", "0,1001"), 1001) is True

    def test_a_department_without_an_id_raises_like_java(self) -> None:
        """``d.getDeptId().intValue()`` 对 null 抛 NPE。"""
        with pytest.raises(AttributeError):
            _is_excluded(SysDept(dept_id=None, ancestors="0"), 100)


# --------------------------------------------------------------------------- 下拉树


class TestTreeselect:
    def test_the_tree_comes_from_the_service(self, http: TestClient, service: Any) -> None:
        service.tree_result = [
            TreeSelect(
                id=100,
                label="总公司",
                children=[TreeSelect(id=101, label="财务部")],
            )
        ]

        body = http.get("/system/dept/treeselect").json()

        assert body["data"] == [
            {"id": 100, "label": "总公司", "children": [{"id": 101, "label": "财务部"}]}
        ]

    def test_a_leaf_has_no_children_key(self, http: TestClient, service: Any) -> None:
        """``TreeSelect.children`` 是 ``@JsonInclude(NON_EMPTY)``。"""
        service.tree_result = [TreeSelect(id=101, label="财务部")]

        assert http.get("/system/dept/treeselect").json()["data"] == [
            {"id": 101, "label": "财务部"}
        ]

    def test_the_query_is_passed_through(self, service: Any) -> None:
        """``treeselect?parentId=100`` 只查子树，**不做** flag 处理。"""
        treeselect(SysDept(parent_id=100, flag="myDept"))

        query = service.of("select_dept_list")[0][1]
        assert (query.parent_id, query.tenant_id, query.dept_id) == (100, None, None)


class TestTreeselectNewFlags:
    """``_apply_flag`` 的分支表 —— 未知 flag 落到 ``deptId = -1``，不是查全部。"""

    @pytest.mark.parametrize("flag", ["myDept", "myDeptCg"])
    def test_my_dept_filters_by_the_callers_tenant(self, service: Any, flag: str) -> None:
        authenticate(tenant_id=777)

        treeselect_new(SysDept(flag=flag))

        assert service.of("select_dept_list")[0][1].tenant_id == 777

    @pytest.mark.parametrize("flag", ["sjzbDept", "sjzbDeptCg"])
    def test_sjzb_dept_filters_by_data_id(self, service: Any, flag: str) -> None:
        authenticate(tenant_id=777)

        treeselect_new(SysDept(flag=flag))

        # Java: dept.setDataId(SecurityUtils.getTenantId() + "") —— 字符串
        assert service.of("select_dept_list")[0][1].data_id == "777"

    def test_is_uint_filters_by_the_unit_flag(self, service: Any) -> None:
        treeselect_new(SysDept(flag="isUint"))

        assert service.of("select_dept_list")[0][1].is_uint == UNIT_FLAG == "1"

    def test_all_dept_adds_nothing(self, service: Any) -> None:
        treeselect_new(SysDept(flag="allDept"))

        query = service.of("select_dept_list")[0][1]
        # flag 本身留在实体上（Java 也不清），但四个过滤字段一个都没被写。
        assert (query.dept_id, query.tenant_id, query.data_id, query.is_uint) == (
            None,
            None,
            None,
            None,
        )

    def test_only_my_dept_filters_by_the_callers_department(self, service: Any) -> None:
        authenticate(dept_id=888)

        treeselect_new(SysDept(flag="onlyMyDept"))

        assert service.of("select_dept_list")[0][1].dept_id == 888

    @pytest.mark.parametrize("flag", ["whatever", "", None])
    def test_an_unknown_flag_queries_a_missing_department(
        self, service: Any, flag: Optional[str]
    ) -> None:
        """Java 的 ``else`` 分支是 ``setDeptId(-1L)`` —— 结果是**空列表**，不是全量。"""
        treeselect_new(SysDept(flag=flag))

        assert service.of("select_dept_list")[0][1].dept_id == -1

    def test_the_flag_is_trimmed_first(self, service: Any) -> None:
        """``CommonUtil.isNull`` 会 trim，所以 ``"  myDept  "`` 仍然命中第一档。"""
        authenticate(tenant_id=777)

        treeselect_new(SysDept(flag="  myDept  "))

        assert service.of("select_dept_list")[0][1].tenant_id == 777

    def test_the_tree_is_built_after_the_flag_is_applied(self, service: Any) -> None:
        treeselect_new(SysDept(flag="allDept"))

        assert [name for name, _ in service.calls] == [
            "select_dept_list",
            "build_dept_tree_select",
        ]

    def test_an_anonymous_caller_hits_security_utils_not_a_403(self) -> None:
        """``treeselectNew?flag=myDept`` 没有权限点，但方法体会去读登录用户 -> 500。"""
        with pytest.raises(CustomException) as error:
            treeselect_new(SysDept(flag="myDept"))

        assert str(error.value) == NO_LOGIN


# --------------------------------------------------------------------------- 角色部门树


class TestRoleDeptTreeselect:
    def test_the_key_order_follows_the_hash_map_bucket_order(
        self, http: TestClient, service: Any
    ) -> None:
        """``AjaxResult.success()`` 是 HashMap：msg(0) -> code(3) -> depts(14) -> checkedKeys(15)。"""
        service.role_dept_ids = [100, 101]
        service.tree_result = [TreeSelect(id=100, label="总公司")]

        body = http.get("/system/dept/roleDeptTreeselect/2").json()

        assert list(body.keys()) == ["msg", "code", "depts", "checkedKeys"]
        assert body["checkedKeys"] == [100, 101]
        assert body["depts"] == [{"id": 100, "label": "总公司"}]

    def test_the_departments_are_read_unfiltered(self, service: Any) -> None:
        role_dept_treeselect(2)

        assert service.of("select_dept_list")[0][1] == SysDept()
        assert service.of("select_dept_list_by_role_id") == [
            ("select_dept_list_by_role_id", 2)
        ]

    def test_the_call_order_is_checked_keys_first(self, service: Any) -> None:
        role_dept_treeselect(2)

        assert [name for name, _ in service.calls] == [
            "select_dept_list",
            "select_dept_list_by_role_id",
            "build_dept_tree_select",
        ]


# --------------------------------------------------------------------------- 单位列表


class TestGetCompanyList:
    def test_it_queries_is_uint_one(self, http: TestClient, service: Any) -> None:
        """等价于 ``GET /list?isUint=1``，但**不接受**任何查询条件。"""
        http.get("/system/dept/getCompanyList?deptName=财务")

        query = service.of("select_dept_list")[0][1]
        assert query == SysDept(is_uint=UNIT_FLAG)
        assert query.dept_name is None

    def test_it_returns_an_array(self, http: TestClient, service: Any) -> None:
        service.list_result = [SysDept(dept_id=100)]

        body = http.get("/system/dept/getCompanyList").json()

        assert body.keys() == {"code", "msg", "data"}
        assert [row["deptId"] for row in body["data"]] == [100]


# --------------------------------------------------------------------------- 详情


class TestGetInfo:
    def test_the_id_comes_from_the_path(self, http: TestClient, service: Any) -> None:
        service.dept_by_id = SysDept(dept_id=7, dept_name="财务部")

        body = http.get("/system/dept/7").json()

        assert service.calls == [("select_dept_by_id", 7)]
        assert body["data"]["deptName"] == "财务部"

    def test_a_missing_row_yields_no_data_key(
        self, http: TestClient, service: Any
    ) -> None:
        """``AjaxResult`` 在 ``data`` 为 null 时**不输出**该键。"""
        service.dept_by_id = None

        assert http.get("/system/dept/404").json() == {"code": 200, "msg": "操作成功"}

    def test_a_non_numeric_id_is_a_500_in_the_body(self, http: TestClient) -> None:
        """Java: ``MethodArgumentTypeMismatchException`` -> HTTP 200 + code 500。"""
        assert http.get("/system/dept/abc").json()["code"] == 500


# --------------------------------------------------------------------------- 新增


class TestAddEndpoint:
    def test_the_name_collision_is_reported(self, http: TestClient, service: Any) -> None:
        service.name_unique = "1"

        body = http.post("/system/dept", json=VALID_BODY).json()

        assert body == {"code": 500, "msg": ADD_DEPT_NAME_EXISTS.format("财务部")}
        # 名字冲突时不再写库。
        assert service.of("insert_dept") == []

    def test_the_creator_is_taken_from_the_security_context(
        self, http: TestClient, service: Any
    ) -> None:
        body = http.post("/system/dept", json=VALID_BODY).json()

        assert body == {"code": 200, "msg": "操作成功"}
        # Java: dept.setCreateBy(getUsername())
        assert service.of("insert_dept")[0][1].create_by == "ry"

    def test_a_zero_row_insert_reports_failure(self, http: TestClient, service: Any) -> None:
        service.insert_result = 0

        assert http.post("/system/dept", json=VALID_BODY).json() == {
            "code": 500,
            "msg": "操作失败",
        }

    def test_the_json_field_names_are_camel_case(
        self, http: TestClient, service: Any
    ) -> None:
        """前端传 ``parentId``/``isUint``，落到实体上是 ``parent_id``/``is_uint``。"""
        http.post(
            "/system/dept",
            json=dict(VALID_BODY, parentId=100, isUint="1", deptName="财务部"),
        )

        inserted = service.of("insert_dept")[0][1]
        assert (inserted.parent_id, inserted.is_uint, inserted.dept_name) == (
            100,
            "1",
            "财务部",
        )

    def test_the_order_num_is_accepted_as_a_number(
        self, http: TestClient, service: Any
    ) -> None:
        """列是 varchar，前端 ``el-input-number`` 会送数字 —— Jackson 照样收。"""
        http.post("/system/dept", json={"deptName": "财务部", "orderNum": 3})

        assert service.of("insert_dept")[0][1].order_num == "3"


# --------------------------------------------------------------------------- 修改


class TestEditEndpoint:
    def test_the_update_goes_through_with_the_updater(
        self, http: TestClient, service: Any
    ) -> None:
        body = http.put(
            "/system/dept", json=dict(VALID_BODY, deptId=5, parentId=0)
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        updated = service.of("update_dept")[0][1]
        assert (updated.dept_id, updated.parent_id, updated.update_by) == (5, 0, "ry")

    def test_the_name_collision_blocks_the_update(
        self, http: TestClient, service: Any
    ) -> None:
        service.name_unique = "1"

        body = http.put("/system/dept", json=dict(VALID_BODY, deptId=5)).json()

        assert body == {"code": 500, "msg": EDIT_DEPT_NAME_EXISTS.format("财务部")}
        assert service.calls == [("check_dept_name_unique", "财务部")]

    def test_a_department_cannot_be_its_own_parent(
        self, http: TestClient, service: Any
    ) -> None:
        body = http.put(
            "/system/dept", json=dict(VALID_BODY, deptId=5, parentId=5)
        ).json()

        assert body == {"code": 500, "msg": EDIT_DEPT_SELF_PARENT.format("财务部")}
        assert service.of("update_dept") == []

    def test_a_missing_parent_id_raises_like_java(
        self, http_lenient: TestClient, service: Any
    ) -> None:
        """``dept.getParentId().equals(...)`` 在 ``parentId`` 为 null 时 NPE -> 500。

        注意这条**不是**校验错误：``parentId`` 上没有 ``@NotNull``，Java 是进了方法体
        才炸的。所以两个请求体在这里都合法，差别只在有没有 ``parentId``。
        """
        body = http_lenient.put("/system/dept", json=dict(VALID_BODY, deptId=5)).json()

        assert body["code"] == 500
        assert service.of("update_dept") == []

    def test_a_disabled_department_with_active_children_is_refused(
        self, http: TestClient, service: Any
    ) -> None:
        service.normal_children = 2

        body = http.put(
            "/system/dept",
            json=dict(VALID_BODY, deptId=5, parentId=0, status=DEPT_DISABLE),
        ).json()

        assert body == {"code": 500, "msg": EDIT_DEPT_HAS_ACTIVE_CHILD}
        assert service.of("update_dept") == []

    def test_the_children_check_only_fires_when_disabling(
        self, http: TestClient, service: Any
    ) -> None:
        """``status = "0"``（正常）时不查子部门，即使子部门数不为 0 也照常更新。"""
        service.normal_children = 2

        body = http.put(
            "/system/dept", json=dict(VALID_BODY, deptId=5, parentId=0, status="0")
        ).json()

        assert body == {"code": 200, "msg": "操作成功"}
        assert service.of("select_normal_children_dept_by_id") == []

    def test_the_three_guards_short_circuit_in_order(self, service: Any) -> None:
        """三道闸的顺序：判重 -> 上级不能是自己 -> 停用前的子部门检查。"""
        authenticate()
        service.name_unique = "1"
        service.normal_children = 9

        result = edit(
            SysDept(dept_id=5, parent_id=5, dept_name="财务部", order_num="1", status=DEPT_DISABLE)
        )

        assert result["msg"] == EDIT_DEPT_NAME_EXISTS.format("财务部")
        assert [name for name, *_ in service.calls] == ["check_dept_name_unique"]

    def test_the_active_child_message_uses_a_full_width_exclamation(self) -> None:
        assert EDIT_DEPT_HAS_ACTIVE_CHILD.endswith("！")


# --------------------------------------------------------------------------- 删除


class TestRemoveEndpoint:
    def test_a_department_with_children_is_refused(
        self, http: TestClient, service: Any
    ) -> None:
        service.child_count = 1

        body = http.delete("/system/dept/100").json()

        assert body == {"code": 500, "msg": REMOVE_HAS_CHILD}
        # 有下级就不再查用户、也不删。
        assert service.calls == [("has_child_by_dept_id", 100)]

    def test_a_department_with_users_is_refused(
        self, http: TestClient, service: Any
    ) -> None:
        service.user_count = 1

        body = http.delete("/system/dept/100").json()

        assert body == {"code": 500, "msg": REMOVE_HAS_USER}
        assert service.of("delete_dept_by_id") == []

    def test_a_clean_department_is_deleted(self, http: TestClient, service: Any) -> None:
        body = http.delete("/system/dept/100").json()

        assert body == {"code": 200, "msg": "操作成功"}
        assert service.of("delete_dept_by_id") == [("delete_dept_by_id", 100)]

    def test_a_zero_row_delete_reports_failure(self, http: TestClient, service: Any) -> None:
        service.delete_result = 0

        assert http.delete("/system/dept/999").json() == {"code": 500, "msg": "操作失败"}

    def test_a_non_numeric_id_is_a_500_in_the_body(self, http: TestClient) -> None:
        assert http.delete("/system/dept/abc").json()["code"] == 500


# --------------------------------------------------------------------------- 辅助函数


class TestHelpers:
    def test_same_id_is_false_for_a_null_argument(self) -> None:
        """Java: ``5L.equals(null)`` -> false。"""
        assert _same_id(5, None) is False

    def test_same_id_raises_for_a_null_receiver(self) -> None:
        """Java: ``null.equals(5L)`` -> NPE。不能写成 ``left == right``。"""
        with pytest.raises(AttributeError):
            _same_id(None, None)

    def test_same_id_is_true_for_equal_values(self) -> None:
        assert _same_id(5, 5) is True
        assert _same_id(5, 6) is False

    def test_apply_flag_writes_only_one_field(self, service: Any) -> None:
        """每个分支只动一个字段，不叠加。"""
        authenticate(tenant_id=777, dept_id=888)
        dept = SysDept(flag="isUint")

        _apply_flag(dept)

        assert (dept.is_uint, dept.tenant_id, dept.data_id, dept.dept_id) == (
            UNIT_FLAG,
            None,
            None,
            None,
        )

    def test_apply_flag_compares_the_trimmed_flag(self) -> None:
        """``isNull`` 先 trim 再比，所以 ``" allDept "`` 不会掉进 else。"""
        dept = SysDept(flag=" allDept ")

        _apply_flag(dept)

        assert dept.dept_id is None


# --------------------------------------------------------------------------- 文案


class TestMessageConstants:
    """六条文案逐字照抄 Java 的字符串拼接（含全角 ``！`` 与半角逗号）。"""

    def test_the_templates(self) -> None:
        assert ADD_DEPT_NAME_EXISTS.format("A") == "新增部门'A'失败，部门名称已存在"
        assert EDIT_DEPT_NAME_EXISTS.format("A") == "修改部门'A'失败，部门名称已存在"
        assert EDIT_DEPT_SELF_PARENT.format("A") == "修改部门'A'失败，上级部门不能是自己"

    def test_the_two_verbatim_messages(self) -> None:
        assert EDIT_DEPT_HAS_ACTIVE_CHILD == "该部门包含未停用的子部门！"
        assert REMOVE_HAS_CHILD == "存在下级部门,不允许删除"
        assert REMOVE_HAS_USER == "部门存在用户,不允许删除"

    def test_the_unit_flag(self) -> None:
        assert UNIT_FLAG == "1"

    def test_a_collision_returns_an_ajax_result(self, service: Any) -> None:
        authenticate()
        service.name_unique = "1"

        result = add(SysDept(dept_name="财务部", order_num="1"))

        assert isinstance(result, AjaxResult)
        assert result["code"] == 500
