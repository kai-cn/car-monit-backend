"""``SysPostController`` -- ``/system/post`` 的 6 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysPostController.java
#   + ruoyi-common/.../core/controller/BaseController.java

这一层测什么
------------
Service 已经被 ``test_sys_post_service.py`` 覆盖，所以全部注入假 Service，只测
**控制器自己的判断**。它们都是"前端约定"，改掉了接口不报错，只会让页面静默失效：

* 路由注册顺序：``/list`` 与 ``/optionselect`` 必须在 ``/{post_id}`` 之前
  （FastAPI 按注册顺序匹配，Spring 的 ``AntPathMatcher`` 优先字面量，结果一致）；
* ``export`` **没有**注册路由（缺 ``ExcelUtil``），但未登录时仍要先撞安全过滤器；
* ``add`` / ``edit`` 的"编码已存在"提示里插的是 **post_name**，不是 post_code；
* ``optionselect`` 没有 ``@PreAuthorize``，只要求登录，且返回全量（不分页）。

``@Validated`` 与 ``@PreAuthorize`` 的先后
------------------------------------------
Java 的顺序是"参数解析（含校验）→ 方法代理（含 ``@PreAuthorize``）"，所以
**没权限的请求只要请求体不合法，回的也是 500 而不是 403**。
:class:`TestValidationRunsBeforePermission` 用"未登录 + 非法请求体"直接验证这一点：
如果哪天有人把 ``ValidPost`` 改成函数体的第一条语句，这个用例会立刻变红。

为什么分两种驱动方式
--------------------
* 直调函数：能拿到返回值对象本身，断言 ``AjaxResult`` 的键值最直观（与
  ``test_sys_user_controller.py`` 一致）；
* ``TestClient``：只有走 ASGI 栈才会真正解析 ``Depends`` 和路由表，
  校验顺序、路径匹配、JSON 形状都只能在这一层验证。用**独立的 mini app**
  （只挂本控制器的 router + 异常处理器），避开 ``SecurityMiddleware`` 对
  MySQL/Redis 的依赖。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_post_controller as controller
from app.api.system.sys_post_controller import (
    ADD_POST_CODE_EXISTS,
    ADD_POST_NAME_EXISTS,
    EDIT_POST_CODE_EXISTS,
    EDIT_POST_NAME_EXISTS,
    add,
    get_info,
    list_posts,
    optionselect,
    remove,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.common.exception.exceptions import AccessDeniedException, CustomException
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.sys_post import SysPost

#: 一个能通过 ``@Validated`` 的请求体（三个字段都是 ``@NotBlank``）。
VALID_BODY: Dict[str, Any] = {"postCode": "ceo", "postName": "董事长", "postSort": "1"}


# --------------------------------------------------------------------------- fakes


class _FakePostService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysPost] = []
        self.post_all_result: List[SysPost] = []
        self.post_by_id: Optional[SysPost] = None
        self.name_unique = "0"
        self.code_unique = "0"
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        self.delete_error: Optional[BaseException] = None
        #: ``select_post_list`` 被调用时挂起中的分页参数（真实 mapper 会在这里 ``take_page()``）。
        self.page_taken: Any = None

    def select_post_list(self, post: SysPost) -> List[SysPost]:
        self.calls.append(("select_post_list", post.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_post_all(self) -> List[SysPost]:
        self.calls.append(("select_post_all",))
        return self.post_all_result

    def select_post_by_id(self, post_id: int) -> Optional[SysPost]:
        self.calls.append(("select_post_by_id", post_id))
        return self.post_by_id

    def check_post_name_unique(self, post: SysPost) -> str:
        self.calls.append(("check_post_name_unique", post.post_name))
        return self.name_unique

    def check_post_code_unique(self, post: SysPost) -> str:
        self.calls.append(("check_post_code_unique", post.post_code))
        return self.code_unique

    def insert_post(self, post: SysPost) -> int:
        self.calls.append(("insert_post", post.model_copy(deep=True)))
        return self.insert_result

    def update_post(self, post: SysPost) -> int:
        self.calls.append(("update_post", post.model_copy(deep=True)))
        return self.update_result

    def delete_post_by_ids(self, post_ids: Sequence[int]) -> int:
        self.calls.append(("delete_post_by_ids", list(post_ids)))
        if self.delete_error is not None:
            raise self.delete_error
        return self.delete_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者与安全上下文。"""
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakePostService()
    monkeypatch.setattr(controller, "_POST_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_post_controller()


@pytest.fixture
def http() -> Any:
    """已登录的 mini app（``*:*:*`` 权限，等同超级管理员）。"""
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    """未登录的 mini app —— 用来验证校验先于权限。"""
    return TestClient(_build_app(login=False))


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:
        # Java: ``JwtAuthenticationTokenFilter`` —— 只把 LoginUser 放进上下文。
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


def authenticate(user_id: int = 2, user_name: str = "ry", permissions: Optional[set] = None) -> SysUser:
    """直调函数时用的登录态（与 ``test_sys_user_controller.py`` 同款）。"""
    user = SysUser(user_id=user_id, user_name=user_name)
    login_user = LoginUser(user=user, permissions=permissions or {"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    """7 个映射的路径 / 动词。"""

    def test_the_seven_paths_are_registered(self) -> None:
        registered = {(route.path, tuple(sorted(route.methods))) for route in controller.router.routes}

        assert registered == {
            ("/system/post/list", ("GET",)),
            ("/system/post/export", ("GET",)),
            ("/system/post/optionselect", ("GET",)),
            ("/system/post/{post_id}", ("GET",)),
            ("/system/post", ("POST",)),
            ("/system/post", ("PUT",)),
            ("/system/post/{post_ids}", ("DELETE",)),
        }

    def test_export_comes_before_the_path_variable(self) -> None:
        """``/export`` 排在 ``/{post_id}`` 后面的话 ``"export"`` 会转 int 失败。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/post/export") < paths.index("/system/post/{post_id}")

    def test_literal_paths_come_before_the_path_variable(self) -> None:
        """FastAPI 按注册顺序匹配；``/list`` 写在 ``/{post_id}`` 之后就会被吃掉。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/post/optionselect") < paths.index("/system/post/{post_id}")
        assert paths.index("/system/post/list") < paths.index("/system/post/{post_id}")

    def test_the_list_beats_the_path_variable_over_http(self, http: TestClient) -> None:
        """顺序正确时 ``GET /list`` 走的是列表端点，``post_id`` 不会被解析成 "list"。"""
        response = http.get("/system/post/list")

        # 列表用的是 TableDataInfo（total/rows/code/msg），详情用的是 AjaxResult。
        assert response.json().keys() == {"total", "rows", "code", "msg"}


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    """``@PreAuthorize("@ss.hasPermi(...)")`` 的四个标识。"""

    @pytest.mark.parametrize(
        "call, permission",
        [
            (lambda: list_posts(SysPost()), "system:post:list"),
            (lambda: get_info(1), "system:post:query"),
            (lambda: add(SysPost(post_code="a", post_name="b", post_sort="1")), "system:post:add"),
            (lambda: remove("1"), "system:post:remove"),
        ],
    )
    def test_an_anonymous_caller_is_refused(self, service: Any, call: Any, permission: str) -> None:
        with pytest.raises(AccessDeniedException):
            call()

        # 权限校验在方法体之前，Service 一次都没被调用。
        assert service.calls == []

    def test_edit_is_guarded_too(self) -> None:
        from app.api.system.sys_post_controller import edit

        with pytest.raises(AccessDeniedException):
            edit(SysPost(post_id=1, post_code="a", post_name="b", post_sort="1"))

    def test_a_partial_permission_does_not_pass(self) -> None:
        """``hasPermi`` 是**精确匹配**，``system:post:*`` 不算拥有 ``system:post:list``。"""
        authenticate(permissions={"system:post:*"})

        with pytest.raises(AccessDeniedException):
            list_posts(SysPost())

    def test_optionselect_needs_no_permission_at_all(self, service: Any) -> None:
        """Java: ``optionselect`` 上没有 ``@PreAuthorize`` —— 未登录也能走到方法体。"""
        service.post_all_result = [SysPost(post_id=1, post_name="董事长")]

        response = optionselect()

        assert response["code"] == 200
        assert service.calls == [("select_post_all",)]

    def test_an_access_denied_becomes_http_200_code_403(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.get("/system/post/1")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}


# --------------------------------------------------------------------------- 校验


class TestValidationRunsBeforePermission:
    """未登录 + 非法请求体 -> 500（校验先跑）；合法请求体 -> 403。"""

    def test_a_missing_code_is_reported_before_the_403(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post("/system/post", json={"postName": "董事长", "postSort": "1"})

        assert response.status_code == 200
        # 若顺序反了，这里会是 {"code":403,...}
        assert response.json() == {"code": 500, "msg": "岗位编码不能为空"}

    def test_a_missing_name_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post("/system/post", json={"postCode": "ceo", "postSort": "1"})

        assert response.json() == {"code": 500, "msg": "岗位名称不能为空"}

    def test_a_missing_sort_is_reported(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.post(
            "/system/post", json={"postCode": "ceo", "postName": "董事长"}
        )

        assert response.json() == {"code": 500, "msg": "显示顺序不能为空"}

    def test_the_first_violation_wins(self, http_anonymous: TestClient) -> None:
        """全部为空时，报的是**声明顺序**里的第一条。

        Java: ``getFieldError()`` 取 ``BindingResult`` 的第一个错误，而顺序由
        ``POST_CONSTRAINTS`` 决定（getPostCode -> getPostName -> getPostSort）。
        """
        response = http_anonymous.post("/system/post", json={})

        assert response.json() == {"code": 500, "msg": "岗位编码不能为空"}

    def test_an_overlong_name_is_reported(self, http_anonymous: TestClient) -> None:
        body = dict(VALID_BODY, postName="岗" * 51)

        response = http_anonymous.post("/system/post", json=body)

        assert response.json() == {"code": 500, "msg": "岗位名称长度不能超过50个字符"}

    def test_an_overlong_code_is_reported(self, http_anonymous: TestClient) -> None:
        body = dict(VALID_BODY, postCode="c" * 65)

        response = http_anonymous.post("/system/post", json=body)

        assert response.json() == {"code": 500, "msg": "岗位编码长度不能超过64个字符"}

    def test_the_boundaries_are_inclusive(self, http_anonymous: TestClient) -> None:
        """``@Size(max = 50)`` 是闭区间：正好 50 个字符合法，落到 403（校验已通过）。"""
        body = dict(VALID_BODY, postName="岗" * 50, postCode="c" * 64)

        response = http_anonymous.post("/system/post", json=body)

        assert response.json()["code"] == 403

    def test_edit_validates_the_same_way(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.put("/system/post", json={"postId": 3, "postName": "董事长"})

        assert response.json() == {"code": 500, "msg": "岗位编码不能为空"}

    def test_a_blank_string_counts_as_missing(self, http_anonymous: TestClient) -> None:
        """``@NotBlank`` 比 ``@NotNull`` 严格：``"   "`` 也算空。"""
        response = http_anonymous.post("/system/post", json=dict(VALID_BODY, postName="   "))

        assert response.json() == {"code": 500, "msg": "岗位名称不能为空"}

    def test_validation_does_not_fire_on_the_query_endpoints(self, http: TestClient) -> None:
        """``list`` / ``getInfo`` 的形参没有 ``@Validated``，空条件照常查询。"""
        response = http.get("/system/post/list")

        assert response.json()["code"] == 200


# --------------------------------------------------------------------------- 查询


class TestListEndpoint:
    def test_the_query_string_is_bound_to_the_entity(self, http: TestClient, service: Any) -> None:
        query = urlencode({"postCode": "ceo", "postName": "董事", "status": "0"})

        response = http.get(f"/system/post/list?{query}")

        assert response.json()["code"] == 200
        post = service.of("select_post_list")[0][1]
        assert (post.post_code, post.post_name, post.status) == ("ceo", "董事", "0")

    def test_the_response_is_a_paged_table(self, http: TestClient, service: Any) -> None:
        service.list_result = [SysPost(post_id=1), SysPost(post_id=2)]

        body = http.get("/system/post/list").json()

        assert (body["code"], body["msg"], body["total"]) == (200, "查询成功", 2)
        assert [row["postId"] for row in body["rows"]] == [1, 2]

    def test_a_paged_service_result_supplies_the_real_total(
        self, http: TestClient, service: Any
    ) -> None:
        from app.common.core.page.page_helper import PageList

        service.list_result = PageList([SysPost(post_id=1)], total=57, page_num=1, page_size=10)

        assert http.get("/system/post/list").json()["total"] == 57

    def test_start_page_is_called_so_the_mapper_can_take_it(self, http: TestClient, service: Any) -> None:
        """``list`` 必须先 ``start_page()``，否则 mapper 的 ``take_page()`` 拿到 ``None``。

        具体数值在这个 mini app 里是缺省值：``build_page_request()`` 从
        ``RequestContextMiddleware`` 放的上下文里读 ``pageNum``/``pageSize``，
        而这里没装那个中间件（完整应用里有）。要验证的是"有没有挂起"，不是"挂起了几"。
        """
        http.get("/system/post/list")

        assert service.page_taken is not None


class TestOptionselectEndpoint:
    def test_it_returns_the_full_list_unpaged(self, http: TestClient, service: Any) -> None:
        service.post_all_result = [SysPost(post_id=1), SysPost(post_id=2)]

        body = http.get("/system/post/optionselect").json()

        # AjaxResult.success(data)，不是 TableDataInfo。
        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert [row["postId"] for row in body["data"]] == [1, 2]


class TestGetInfoEndpoint:
    def test_the_id_comes_from_the_path(self, http: TestClient, service: Any) -> None:
        service.post_by_id = SysPost(post_id=7, post_name="项目经理")

        body = http.get("/system/post/7").json()

        assert service.calls == [("select_post_by_id", 7)]
        assert body["data"]["postName"] == "项目经理"

    def test_a_missing_row_yields_no_data_key(self, http: TestClient, service: Any) -> None:
        """``AjaxResult`` 在 ``data`` 为 null 时**不输出**该键（不是 ``"data": null``）。"""
        service.post_by_id = None

        body = http.get("/system/post/404").json()

        assert body == {"code": 200, "msg": "操作成功"}

    def test_a_non_numeric_id_is_a_500_in_the_body(self, http: TestClient) -> None:
        """Java: ``MethodArgumentTypeMismatchException`` -> HTTP 200 + code 500。"""
        body = http.get("/system/post/abc").json()

        assert body["code"] == 500


# --------------------------------------------------------------------------- 新增


class TestAddEndpoint:
    def test_the_name_collision_is_reported_with_the_post_name(
        self, http: TestClient, service: Any
    ) -> None:
        service.name_unique = "1"

        body = http.post("/system/post", json=VALID_BODY).json()

        assert body == {"code": 500, "msg": ADD_POST_NAME_EXISTS.format("董事长")}
        assert "董事长" in body["msg"]
        # 名字冲突时不再查编码，也不写库。
        assert service.calls == [("check_post_name_unique", "董事长")]

    def test_the_code_collision_message_inserts_the_post_name(
        self, http: TestClient, service: Any
    ) -> None:
        """Java 源码写的就是 ``post.getPostName()``，不是 ``postCode`` —— 别"修正"。"""
        service.code_unique = "1"

        body = http.post("/system/post", json=VALID_BODY).json()

        assert body == {"code": 500, "msg": ADD_POST_CODE_EXISTS.format("董事长")}
        assert "ceo" not in body["msg"]

    def test_the_creator_is_taken_from_the_security_context(
        self, http: TestClient, service: Any
    ) -> None:
        body = http.post("/system/post", json=VALID_BODY).json()

        assert body == {"code": 200, "msg": "操作成功"}
        inserted = service.of("insert_post")[0][1]
        # Java: post.setCreateBy(getUsername())
        assert inserted.create_by == "ry"

    def test_a_zero_row_insert_reports_failure(self, http: TestClient, service: Any) -> None:
        service.insert_result = 0

        body = http.post("/system/post", json=VALID_BODY).json()

        assert body == {"code": 500, "msg": "操作失败"}

    def test_the_json_field_names_are_camel_case(self, http: TestClient, service: Any) -> None:
        """前端传的是 ``postCode``/``postSort``，落到实体上是 ``post_code``/``post_sort``。"""
        http.post("/system/post", json=dict(VALID_BODY, remark="备注"))

        inserted = service.of("insert_post")[0][1]
        assert (inserted.post_code, inserted.post_name, inserted.post_sort) == ("ceo", "董事长", "1")
        assert inserted.remark == "备注"


# --------------------------------------------------------------------------- 修改


class TestEditEndpoint:
    def test_the_update_goes_through_with_the_updater(
        self, http: TestClient, service: Any
    ) -> None:
        body = http.put("/system/post", json=dict(VALID_BODY, postId=5)).json()

        assert body == {"code": 200, "msg": "操作成功"}
        updated = service.of("update_post")[0][1]
        assert (updated.post_id, updated.update_by) == (5, "ry")

    def test_the_name_collision_blocks_the_update(self, http: TestClient, service: Any) -> None:
        service.name_unique = "1"

        body = http.put("/system/post", json=dict(VALID_BODY, postId=5)).json()

        assert body == {"code": 500, "msg": EDIT_POST_NAME_EXISTS.format("董事长")}
        assert service.of("update_post") == []

    def test_the_code_collision_blocks_the_update(self, http: TestClient, service: Any) -> None:
        service.code_unique = "1"

        body = http.put("/system/post", json=dict(VALID_BODY, postId=5)).json()

        assert body == {"code": 500, "msg": EDIT_POST_CODE_EXISTS.format("董事长")}
        assert service.of("update_post") == []


# --------------------------------------------------------------------------- 删除


class TestRemoveEndpoint:
    def test_the_comma_separated_ids_become_a_list_of_ints(
        self, http: TestClient, service: Any
    ) -> None:
        body = http.delete("/system/post/5,6,7").json()

        assert body == {"code": 200, "msg": "操作成功"}
        assert service.calls == [("delete_post_by_ids", [5, 6, 7])]

    def test_an_assigned_post_returns_http_200_with_code_500(
        self, http: TestClient, service: Any
    ) -> None:
        """``CustomException`` 由通用 ``RuntimeError`` 处理器接住，状态码仍是 200。"""
        service.delete_error = CustomException("项目经理已分配,不能删除")

        response = http.delete("/system/post/5")
        body = response.json()

        assert response.status_code == 200
        assert body == {"code": 500, "msg": "项目经理已分配,不能删除"}

    def test_a_non_numeric_id_raises_like_spring_binding(self, service: Any) -> None:
        """Java ``StringToArrayConverter`` 转 ``Long`` 失败 -> 500。

        直调时抛 ``ValueError``（与 ``test_sys_user_controller.py`` 同款断言）。
        走 ASGI 时它落到 ``@ExceptionHandler(Exception.class)``，客户端看到的是
        HTTP 200 + ``{"code":500,...}``；Starlette 会额外往服务端日志重抛一次，
        这正是 ``TestClient(raise_server_exceptions=True)`` 会失败的原因。
        """
        authenticate()

        with pytest.raises(ValueError):
            remove("5,abc")

        assert service.calls == []

    def test_a_zero_row_delete_reports_failure(self, http: TestClient, service: Any) -> None:
        service.delete_result = 0

        body = http.delete("/system/post/999").json()

        assert body == {"code": 500, "msg": "操作失败"}


# --------------------------------------------------------------------------- 文案


class TestMessageConstants:
    """四条文案逐字照抄 Java 的字符串拼接（含中文全角逗号）。"""

    def test_the_four_templates(self) -> None:
        assert ADD_POST_NAME_EXISTS.format("A") == "新增岗位'A'失败，岗位名称已存在"
        assert ADD_POST_CODE_EXISTS.format("A") == "新增岗位'A'失败，岗位编码已存在"
        assert EDIT_POST_NAME_EXISTS.format("A") == "修改岗位'A'失败，岗位名称已存在"
        assert EDIT_POST_CODE_EXISTS.format("A") == "修改岗位'A'失败，岗位编码已存在"

    def test_the_result_is_an_ajax_result(self, service: Any) -> None:
        authenticate()
        service.name_unique = "1"

        result = add(SysPost(post_code="a", post_name="b", post_sort="1"))

        assert isinstance(result, AjaxResult)
        assert result["code"] == 500
