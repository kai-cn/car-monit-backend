"""``TestController`` -- ``/test/user`` 的 5 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/TestController.java

这一层测什么
------------
这是一个纯内存脚手架，没有 Mapper / Service，所以全部用例都打在**控制器约定**上：

* 5 个映射的路径与动词；
* ``R`` 与 ``AjaxResult`` 的**形状差异**：``data`` 为 ``null`` 时 ``R`` **保留**
  ``"data": null``（``AjaxResult`` 会省略这个键）；
* ``save`` 读的是 **request parameter**（query / 表单），**不读 JSON 体**；
  ``update`` 反过来只读 JSON 体；
* ``users`` 的 ``LinkedHashMap`` 语义：``save`` 已存在的键不动位置，
  ``update``（``remove`` + ``put``）把它挪到末尾；
* 每个分支的原样文案："用户ID不能为空" / "用户不存在"；
* 未登录时落到 ``anyRequest().authenticated()``，回 HTTP 200 + ``code 401``。
"""

from __future__ import annotations

from typing import Any, Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.tool import test_controller as controller
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def _fresh_users() -> Iterator[None]:
    """每个用例都从两条种子数据开始（Java 侧只能重启进程）。"""
    controller.reset_users()
    SecurityContextHolder.clear_context()
    yield
    controller.reset_users()
    SecurityContextHolder.clear_context()


def _build_app(login: bool = True) -> FastAPI:
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


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app())


# --------------------------------------------------------------------------- 路由表


class TestRouteTable:
    def test_the_five_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }

        assert registered == {
            ("/test/user/list", ("GET",)),
            ("/test/user/{user_id}", ("GET",)),
            ("/test/user/save", ("POST",)),
            ("/test/user/update", ("PUT",)),
            ("/test/user/{user_id}", ("DELETE",)),
        }

    def test_list_is_registered_before_the_path_variable(self) -> None:
        """两个都是 ``GET``，``/list`` 排在后面会被当成 ``userId = "list"``。"""
        paths = [(route.path, tuple(sorted(route.methods))) for route in controller.router.routes]

        assert paths.index(("/test/user/list", ("GET",))) < paths.index(
            ("/test/user/{user_id}", ("GET",))
        )

    def test_no_permission_point_is_required(self) -> None:
        """Java 里 5 个方法都**没有** ``@PreAuthorize`` —— 一个装饰器不应挂上去。

        ``pre_authorize_permi`` 用的是 ``functools.wraps``，被它包过的端点**不是**原函数；
        这里用恒等比较把"有没有权限包装器"一起钉住。
        """
        endpoints = {route.endpoint for route in controller.router.routes}

        assert endpoints == {
            controller.user_list,
            controller.get_user,
            controller.save,
            controller.update,
            controller.delete,
        }


# --------------------------------------------------------------------------- 列表 / 详情


class TestList:
    def test_returns_the_two_seeded_users_in_insertion_order(self, http: Any) -> None:
        response = http.get("/test/user/list")

        body = response.json()
        assert response.status_code == 200
        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert [user["userId"] for user in body["data"]] == [1, 2]

    def test_each_user_carries_exactly_the_four_java_fields(self, http: Any) -> None:
        body = http.get("/test/user/list").json()

        assert list(body["data"][0].keys()) == ["userId", "username", "password", "mobile"]

    def test_the_seeded_values_match_java(self, http: Any) -> None:
        body = http.get("/test/user/list").json()

        assert body["data"] == [
            {"userId": 1, "username": "admin", "password": "admin123", "mobile": "15888888888"},
            {"userId": 2, "username": "ry", "password": "admin123", "mobile": "15666666666"},
        ]

    def test_mutating_the_answer_does_not_touch_the_store(self, http: Any) -> None:
        """``list`` 回的是新列表，改它不应影响内存表（Java 的 ``new ArrayList<>()``）。"""
        first = http.get("/test/user/list").json()
        first["data"].clear()

        assert len(http.get("/test/user/list").json()["data"]) == 2


class TestGetUser:
    def test_found_returns_the_entity(self, http: Any) -> None:
        body = http.get("/test/user/1").json()

        assert body == {
            "code": 200,
            "msg": "操作成功",
            "data": {"userId": 1, "username": "admin", "password": "admin123", "mobile": "15888888888"},
        }

    def test_missing_returns_fail_with_null_data(self, http: Any) -> None:
        response = http.get("/test/user/99")

        body = response.json()
        assert response.status_code == 200
        assert body["code"] == 500
        assert body["msg"] == "用户不存在"
        # ``R`` 与 ``AjaxResult`` 的分水岭：data 键**在**，值是 null
        assert "data" in body and body["data"] is None

    def test_non_numeric_id_is_a_200_with_code_500(self, http: Any) -> None:
        """Java: ``MethodArgumentTypeMismatchException`` -> HTTP 200 + ``code 500``。"""
        response = http.get("/test/user/abc")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- 新增


class TestSave:
    def test_query_string_binds_the_entity(self, http: Any) -> None:
        """Java 的 ``save`` **没有** ``@RequestBody`` -> 读 request parameter。"""
        response = http.post(
            "/test/user/save",
            params={"userId": 3, "username": "new", "password": "pwd", "mobile": "13900000000"},
        )

        body = response.json()
        assert body == {"code": 200, "msg": "操作成功", "data": None}
        assert http.get("/test/user/3").json()["data"]["username"] == "new"

    def test_urlencoded_form_body_binds_the_entity(self, http: Any) -> None:
        """Tomcat 的 ``getParameter`` 同样覆盖 urlencoded 请求体。"""
        response = http.post(
            "/test/user/save",
            data={"userId": "4", "username": "form", "password": "pwd", "mobile": "13900000001"},
        )

        assert response.json()["code"] == 200
        assert http.get("/test/user/4").json()["data"]["username"] == "form"

    def test_json_body_is_ignored(self, http: Any) -> None:
        """发 JSON 给 ``/save`` 只会得到"用户ID不能为空" —— Java 也是这样。"""
        response = http.post(
            "/test/user/save",
            json={"userId": 5, "username": "json", "password": "pwd", "mobile": "13900000002"},
        )

        body = response.json()
        assert body["code"] == 500
        assert body["msg"] == "用户ID不能为空"
        assert http.get("/test/user/5").json()["code"] == 500

    def test_query_wins_over_the_form_body(self, http: Any) -> None:
        """Tomcat 先解析 query string，同名参数以 query 为准。"""
        response = http.post(
            "/test/user/save?username=from-query",
            data={"userId": "6", "username": "from-form", "password": "pwd", "mobile": "139"},
        )

        assert response.json()["code"] == 200
        assert http.get("/test/user/6").json()["data"]["username"] == "from-query"

    def test_saving_an_existing_id_keeps_its_position(self, http: Any) -> None:
        """``LinkedHashMap#put`` 改值不动位置 -> 用户 1 仍排第一。"""
        http.post("/test/user/save", params={"userId": 1, "username": "renamed"})

        body = http.get("/test/user/list").json()
        assert [user["userId"] for user in body["data"]] == [1, 2]
        assert body["data"][0]["username"] == "renamed"

    def test_missing_user_id_is_rejected_before_writing(self, http: Any) -> None:
        response = http.post("/test/user/save", params={"username": "no-id"})

        body = response.json()
        assert body["code"] == 500
        assert body["msg"] == "用户ID不能为空"
        assert len(http.get("/test/user/list").json()["data"]) == 2

    def test_empty_user_id_counts_as_missing(self, http: Any) -> None:
        """Spring 的 ``StringToNumberConverterFactory`` 把空串转成 ``null``。"""
        response = http.post("/test/user/save", params={"userId": "", "username": "empty"})

        assert response.json()["msg"] == "用户ID不能为空"


# --------------------------------------------------------------------------- 更新


class TestUpdate:
    def test_json_body_updates_and_moves_the_row_to_the_end(self, http: Any) -> None:
        """``remove`` + ``put`` -> ``LinkedHashMap`` 里位置被推到末尾。"""
        response = http.put("/test/user/update", json={"userId": 1, "username": "updated"})

        assert response.json() == {"code": 200, "msg": "操作成功", "data": None}
        body = http.get("/test/user/list").json()
        assert [user["userId"] for user in body["data"]] == [2, 1]
        assert body["data"][-1]["username"] == "updated"

    def test_missing_user_id_is_rejected(self, http: Any) -> None:
        response = http.put("/test/user/update", json={"username": "no-id"})

        assert response.json()["msg"] == "用户ID不能为空"

    def test_unknown_user_id_is_rejected(self, http: Any) -> None:
        response = http.put("/test/user/update", json={"userId": 99, "username": "ghost"})

        assert response.json() == {"code": 500, "msg": "用户不存在", "data": None}

    def test_query_string_is_ignored(self, http: Any) -> None:
        """``@RequestBody`` 只读 JSON 体 —— query 上的 userId 不参与。"""
        response = http.put("/test/user/update?userId=1", json={"username": "x"})

        assert response.json()["msg"] == "用户ID不能为空"


# --------------------------------------------------------------------------- 删除


class TestDelete:
    def test_existing_user_is_removed(self, http: Any) -> None:
        response = http.delete("/test/user/2")

        assert response.json() == {"code": 200, "msg": "操作成功", "data": None}
        assert http.get("/test/user/list").json()["data"] == [
            {"userId": 1, "username": "admin", "password": "admin123", "mobile": "15888888888"}
        ]

    def test_missing_user_reports_the_java_message(self, http: Any) -> None:
        response = http.delete("/test/user/99")

        assert response.json() == {"code": 500, "msg": "用户不存在", "data": None}

    def test_deleting_twice_fails_the_second_time(self, http: Any) -> None:
        assert http.delete("/test/user/1").json()["code"] == 200
        assert http.delete("/test/user/1").json()["code"] == 500


# --------------------------------------------------------------------------- 鉴权


class TestSecurity:
    def test_anonymous_call_answers_200_with_code_401(self, client: Any) -> None:
        """``/test/**`` 没有 SecurityConfig 规则 -> ``anyRequest().authenticated()``。"""
        response = client.get("/test/user/list")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 401
        assert body["msg"] == "请求访问：/test/user/list，认证失败，无法访问系统资源"

    def test_the_router_is_registered_on_the_real_app(self, client: Any) -> None:
        paths = set(client.app.openapi()["paths"])

        assert "/test/user/list" in paths
