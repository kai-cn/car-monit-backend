"""``SysNoticeController`` -- ``/system/notice`` 的 7 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysNoticeController.java
#   + ruoyi-framework/.../config/SecurityConfig.java（``/system/notice/view/**``）

这一层测什么
------------
Service 已被 ``test_sys_notice_service.py`` 覆盖，所以全部注入假 Service，只测
**控制器自己的约定**：

* 7 个映射全部注册（本切片**没有** ``export``，与 post / role / menu 都不同）；
* 只有 ``add`` / ``edit`` / ``remove`` 带 ``@PreAuthorize``；``list`` 的注解在
  Java 里是**注释掉的**，``listquery`` / ``getInfo`` 本来就没有 —— 这四个"登录即可"；
* ``listquery`` 在 ``startPage()`` 之后**强制** ``status = "0"``；
* ``/view/{noticeId}`` 与 ``/{noticeId}`` 查的是同一个 service 方法，
  区别只在安全规则（``anonymous()``）；
* 声明顺序：``/list`` / ``/listquery`` / ``/view/{id}`` 必须在 ``/{id}`` 之前。

``@Validated`` 是个空壳
------------------------
``add`` / ``edit`` 上有 ``@Validated``，但 :class:`SysNotice` **一个约束注解都没有**，
所以 Hibernate Validator 放行一切。这里因此**没有** ``ValidNotice`` 依赖：
``{}`` / 空标题 / 超长标题都能一路走到方法体。:class:`TestNoValidation` 把这个
"什么都不校验"的现状钉住 —— 将来若有人补了 ``@NotBlank``，用例会立刻变红，
提醒他那是**行为改变**而不是修 bug。

为什么分两种驱动方式
--------------------
* 直调函数：能拿到返回值对象本身，断言 ``AjaxResult`` / ``TableDataInfo`` 的键值最直观；
* ``TestClient``：只有走 ASGI 栈才会真正解析路由与 ``Depends``。用**独立的 mini app**
  （只挂本控制器的 router + 异常处理器），避开 ``SecurityMiddleware`` 对 MySQL/Redis 的依赖。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import sys_notice_controller as controller
from app.api.system.sys_notice_controller import (
    add,
    edit,
    get_info,
    get_view_info,
    list_notices,
    listquery,
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
from app.system.domain.sys_notice import SysNotice

#: 公告实体**没有**约束注解，所以最小请求体就是 ``{}``。
MINIMAL_BODY: Dict[str, Any] = {}

#: 一个"前端真实会发"的请求体。
FULL_BODY: Dict[str, Any] = {
    "noticeTitle": "系统升级公告",
    "noticeType": "2",
    "noticeContent": "<p>今晚维护</p>",
    "status": "0",
}


# --------------------------------------------------------------------------- fakes


class _FakeNoticeService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysNotice] = []
        self.by_id_result: Optional[SysNotice] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        #: ``select_notice_list`` 被调用时挂起中的分页参数（真实 mapper 会在这里 ``take_page()``）。
        self.page_taken: Any = None

    def select_notice_list(self, notice: SysNotice) -> List[SysNotice]:
        self.calls.append(("select_notice_list", notice.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_notice_by_id(self, notice_id: int) -> Optional[SysNotice]:
        self.calls.append(("select_notice_by_id", notice_id))
        return self.by_id_result

    def insert_notice(self, notice: SysNotice) -> int:
        self.calls.append(("insert_notice", notice.model_copy(deep=True)))
        return self.insert_result

    def update_notice(self, notice: SysNotice) -> int:
        self.calls.append(("update_notice", notice.model_copy(deep=True)))
        return self.update_result

    def delete_notice_by_ids(self, notice_ids: Sequence[int]) -> int:
        self.calls.append(("delete_notice_by_ids", list(notice_ids)))
        return self.delete_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def service(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者与安全上下文。"""
    SecurityContextHolder.clear_context()
    clear_page()
    fake = _FakeNoticeService()
    monkeypatch.setattr(controller, "_NOTICE_SERVICE", fake)
    yield fake
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_notice_controller()


@pytest.fixture
def http() -> Any:
    """已登录的 mini app（``*:*:*`` 权限，等同超级管理员）。"""
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_anonymous() -> Any:
    """未登录的 mini app —— 用来验证权限点。"""
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


def authenticate(
    user_id: int = 2, user_name: str = "ry", permissions: Optional[set] = None
) -> SysUser:
    """直调函数时用的登录态（与 ``test_sys_post_controller.py`` 同款）。"""
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
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/system/notice/list", ("GET",)),
            ("/system/notice/listquery", ("GET",)),
            ("/system/notice/view/{notice_id}", ("GET",)),
            ("/system/notice/{notice_id}", ("GET",)),
            ("/system/notice", ("POST",)),
            ("/system/notice", ("PUT",)),
            ("/system/notice/{notice_ids}", ("DELETE",)),
        }

    def test_export_is_not_registered_either(self) -> None:
        """Java 的 ``SysNoticeController`` 本来就没有 ``export``。"""
        assert not any(route.path.endswith("/export") for route in controller.router.routes)

    def test_literal_paths_come_before_the_path_variable(self) -> None:
        """FastAPI 按注册顺序匹配；``/list`` 写在 ``/{notice_id}`` 之后就会被吃掉。"""
        paths = [route.path for route in controller.router.routes]

        assert paths.index("/system/notice/listquery") < paths.index("/system/notice/{notice_id}")
        assert paths.index("/system/notice/list") < paths.index("/system/notice/{notice_id}")
        assert paths.index("/system/notice/view/{notice_id}") < paths.index(
            "/system/notice/{notice_id}"
        )

    def test_the_list_beats_the_path_variable_over_http(self, http: TestClient) -> None:
        """顺序正确时 ``GET /list`` 走的是列表端点，``notice_id`` 不会被解析成 "list"。"""
        response = http.get("/system/notice/list")

        # 列表用 TableDataInfo（total/rows/code/msg），详情用 AjaxResult。
        assert response.json().keys() == {"total", "rows", "code", "msg"}

    def test_listquery_beats_the_path_variable_too(
        self, http: TestClient, service: Any
    ) -> None:
        response = http.get("/system/notice/listquery")

        assert response.json().keys() == {"total", "rows", "code", "msg"}
        assert service.of("select_notice_list")[0][1].status == "0"

    def test_view_is_its_own_route(self, http: TestClient) -> None:
        """``/view/1`` 有两段，不会被单段的 ``/{notice_id}`` 吞掉。"""
        response = http.get("/system/notice/view/1")

        assert response.json() == {"code": 200, "msg": "操作成功"}


# --------------------------------------------------------------------------- 权限


class TestPermissions:
    """只有 3 个权限点：``add`` / ``edit`` / ``remove``。"""

    @pytest.mark.parametrize(
        "call",
        [
            lambda: add(SysNotice(notice_title="标题")),
            lambda: edit(SysNotice(notice_id=1, notice_title="标题")),
            lambda: remove("1"),
        ],
    )
    def test_the_three_write_endpoints_are_guarded(
        self, service: Any, call: Any
    ) -> None:
        with pytest.raises(AccessDeniedException):
            call()

        # 权限校验在方法体之前，Service 一次都没被调用。
        assert service.calls == []

    def test_list_needs_no_permission(self, service: Any) -> None:
        """Java 里 ``@PreAuthorize("@ss.hasPermi('system:notice:list')")`` 是**注释掉的**。"""
        service.list_result = [SysNotice(notice_id=1, notice_title="标题")]

        table = list_notices(SysNotice())

        assert table.code == 200
        assert [row.notice_id for row in table.rows] == [1]

    def test_listquery_needs_no_permission(self, service: Any) -> None:
        table = listquery(SysNotice())

        assert table.code == 200
        assert service.of("select_notice_list") != []

    def test_get_info_needs_no_permission(self, service: Any) -> None:
        service.by_id_result = SysNotice(notice_id=5)

        response = get_info(5)

        assert response["code"] == 200
        # 直调时 ``data`` 是实体对象本身（没经 JSON 序列化）
        assert response["data"].notice_id == 5

    def test_a_partial_permission_does_not_pass(self) -> None:
        """``hasPermi`` 是**精确匹配**，``system:notice:*`` 不算拥有 ``system:notice:add``。"""
        authenticate(permissions={"system:notice:*"})

        with pytest.raises(AccessDeniedException):
            add(SysNotice(notice_title="标题"))

    def test_an_access_denied_becomes_http_200_code_403(self, http_anonymous: TestClient) -> None:
        response = http_anonymous.delete("/system/notice/1")

        assert response.status_code == 200
        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}


# --------------------------------------------------------------------------- listquery


class TestListQuery:
    def test_status_is_forced_to_zero(self, service: Any) -> None:
        """客户端传 ``status=1`` 也会被覆盖成 ``"0"``。"""
        listquery(SysNotice(status="1"))

        assert service.of("select_notice_list")[0][1].status == "0"

    def test_other_filters_survive_the_override(self, service: Any) -> None:
        listquery(SysNotice(notice_title="升级", status="1", buss_id="9"))

        query = service.of("select_notice_list")[0][1]
        assert query.notice_title == "升级"
        assert query.buss_id == "9"
        assert query.status == "0"

    def test_the_page_is_started_before_the_query(self, service: Any) -> None:
        """``startPage()`` 在方法体第一行；分页参数由 mapper 的 ``take_page`` 取走。"""
        listquery(SysNotice())

        assert service.page_taken is not None
        assert service.page_taken.get_page_num() == 1
        assert service.page_taken.get_page_size() == 10

    def test_list_does_not_override_the_status(self, service: Any) -> None:
        """``list`` 没有那一行 —— ``status`` 传什么就是什么。"""
        list_notices(SysNotice(status="1"))

        assert service.of("select_notice_list")[0][1].status == "1"


# --------------------------------------------------------------------------- add / edit


class TestWriteEndpoints:
    def test_add_writes_the_user_name(self, service: Any) -> None:
        """控制器写 ``userName``；真实 Service 随后会用 ``userId`` 覆盖它。"""
        authenticate(user_name="ry")

        response = add(SysNotice(notice_title="标题"))

        assert response["code"] == 200
        assert service.of("insert_notice")[0][1].create_by == "ry"

    def test_edit_writes_the_user_name(self, service: Any) -> None:
        authenticate(user_name="ry")

        edit(SysNotice(notice_id=1, notice_title="标题"))

        assert service.of("update_notice")[0][1].update_by == "ry"

    def test_add_returns_a_failure_when_nothing_was_inserted(self, service: Any) -> None:
        authenticate()
        service.insert_result = 0

        assert add(SysNotice(notice_title="标题"))["code"] == 500

    def test_edit_returns_a_failure_when_nothing_was_updated(self, service: Any) -> None:
        authenticate()
        service.update_result = 0

        assert edit(SysNotice(notice_id=1))["code"] == 500


# --------------------------------------------------------------------------- remove


class TestRemove:
    def test_comma_separated_ids_are_parsed(self, service: Any) -> None:
        authenticate()

        remove("1,2,3")

        assert service.of("delete_notice_by_ids") == [("delete_notice_by_ids", [1, 2, 3])]

    def test_a_single_id_is_a_one_element_array(self, service: Any) -> None:
        authenticate()

        remove("7")

        assert service.of("delete_notice_by_ids") == [("delete_notice_by_ids", [7])]

    def test_a_failure_result_is_reported(self, service: Any) -> None:
        authenticate()
        service.delete_result = 0

        assert remove("1,2")["code"] == 500


# --------------------------------------------------------------------------- view / getInfo


class TestDetailEndpoints:
    def test_view_and_get_info_hit_the_same_method(self, service: Any) -> None:
        service.by_id_result = SysNotice(notice_id=5, notice_title="标题")

        view = get_view_info(5)
        info = get_info(5)

        assert view == info
        assert [call[1] for call in service.of("select_notice_by_id")] == [5, 5]

    def test_a_missing_notice_omits_the_data_key(self, service: Any) -> None:
        """Java ``success(null)`` -> ``{"code":200,"msg":"操作成功"}``（**没有** ``data`` 键）。"""
        assert get_info(404) == {"code": 200, "msg": "操作成功"}


# --------------------------------------------------------------------------- 无校验


class TestNoValidation:
    """``@Validated`` 在 Java 里是空壳（实体零约束），这里也不许凭空加约束。"""

    def test_an_empty_body_reaches_the_permission_check(self, http_anonymous: TestClient) -> None:
        """若哪天补了 ``@NotBlank``，这里会变成 ``code 500`` 而不是 ``403``。"""
        response = http_anonymous.post("/system/notice", json=MINIMAL_BODY)

        assert response.json() == {"code": 403, "msg": "没有权限，请联系管理员授权"}

    def test_an_empty_title_is_accepted(self, http: TestClient) -> None:
        """空标题能一路走到 Service（Java 也是如此，库里允许空标题）。"""
        response = http.post("/system/notice", json={"noticeTitle": ""})

        assert response.json()["code"] == 200

    def test_an_overlong_title_is_accepted(self, http: TestClient) -> None:
        """没有 ``@Size``：超长标题不会被拦，最终由数据库列宽决定。"""
        response = http.post("/system/notice", json={"noticeTitle": "标" * 200})

        assert response.json()["code"] == 200

    def test_a_broken_body_fails_before_the_permission_check(
        self, http_anonymous: TestClient
    ) -> None:
        """``noticeId`` 不是数字 -> 反序列化先失败（200 + code 500），与 Spring 同序。"""
        response = http_anonymous.post("/system/notice", json={"noticeId": "abc"})

        assert response.status_code == 200
        assert response.json()["code"] == 500

    def test_the_full_body_round_trips(self, http: TestClient) -> None:
        response = http.put("/system/notice", json=dict(FULL_BODY, noticeId=1))

        assert response.json()["code"] == 200
