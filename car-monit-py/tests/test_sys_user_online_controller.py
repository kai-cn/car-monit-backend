"""``SysUserOnlineController`` + ``SysUserOnlineService`` —— ``/monitor/online``.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/monitor/SysUserOnlineController.java
#   ruoyi-system/.../service/impl/SysUserOnlineServiceImpl.java

在线用户的数据源是 **Redis**，不是数据库
----------------------------------------
没有 mapper、没有分页、没有 SQL。Java 的做法是 ``redisCache.keys("login_tokens:*")``
扫出全部会话键，再逐个 ``getCacheObject(key)`` 反序列化回 ``LoginUser``。所以：

* ``list`` 里**没有** ``startPage()``，前端传 ``pageSize=10`` 也会拿到全部在线用户，
  且 ``total`` 是列表长度（``new PageInfo(list).getTotal()``）；
* 结果是 ``Collections.reverse`` 之后的**倒序**；
* ``isNotEmpty`` 而不是 ``isBlank``：``" "`` 算"有值"，会真的去比对然后查出空结果。

三个分支与 Java 完全一致（都有 -> 只有 ip -> 只有用户名 -> 都没有），
第三个分支多一个 ``isNotNull(user.getUser())``，第一、二个没有 —— 这是 Java 原文，
所以脏值在"按 ip 过滤"时会 NPE（-> code 500），在"按用户名过滤"时只是被跳过。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.monitor import sys_user_online_controller as controller
from app.api.monitor.sys_user_online_controller import force_logout, list_online
from app.common.constant.constants import LOGIN_TOKEN_KEY
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.service.sys_user_online_service import SysUserOnlineService


# --------------------------------------------------------------------------- fakes


class _FakeRedisCache:
    """``RedisCache`` 的最小替身 —— 只实现 Service 用到的那两个方法."""

    def __init__(self) -> None:
        #: ``login_tokens:<token>`` -> ``LoginUser``（``None`` 模拟"键在但值坏了"）
        self.store: Dict[str, Optional[LoginUser]] = {}
        self.keys_calls: List[str] = []
        self.deleted: List[str] = []

    def keys(self, pattern: str) -> List[str]:
        self.keys_calls.append(pattern)
        # 模拟 Redis 的键顺序（``KEYS`` 不保证有序；用例靠它验证 reverse）
        return list(self.store)

    def get_cache_object(self, key: str) -> Optional[LoginUser]:
        return self.store.get(key)

    def delete_object(self, key: str) -> bool:
        self.deleted.append(key)
        self.store.pop(key, None)
        return True


@pytest.fixture
def redis(monkeypatch: Any) -> _FakeRedisCache:
    """假 Redis，同时填进控制器的 ``_REDIS_CACHE``（强退用的是它）。"""
    fake = _FakeRedisCache()
    monkeypatch.setattr(controller, "_REDIS_CACHE", fake)
    return fake


@pytest.fixture
def service(redis: _FakeRedisCache, monkeypatch: Any) -> SysUserOnlineService:
    """假 Service，同时填进控制器的 ``_USER_ONLINE_SERVICE``。"""
    stub = SysUserOnlineService(redis_cache=redis)  # type: ignore[arg-type]
    monkeypatch.setattr(controller, "_USER_ONLINE_SERVICE", stub)
    return stub


@pytest.fixture(autouse=True)
def controller_wiring(monkeypatch: pytest.MonkeyPatch) -> None:
    SecurityContextHolder.clear_context()
    authenticate()
    yield
    SecurityContextHolder.clear_context()
    controller.reset_user_online_controller()


@pytest.fixture
def http(service: SysUserOnlineService) -> Any:
    """mini app；依赖 ``service`` 保证假协作者已注入（否则会去连真 Redis）。"""
    return TestClient(_build_app())


def authenticate() -> SysUser:
    user = SysUser(user_id=1, user_name="admin")
    login_user = LoginUser(token="t", user=user, permissions={"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _build_app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(controller.router)
    return application


def _login_user(
    token: str = "t1",
    user_name: str = "admin",
    ipaddr: str = "127.0.0.1",
    dept_name: Optional[str] = "研发部门",
) -> LoginUser:
    """一条 Redis 里的会话（``LoginUser`` 的 JSON 反序列化结果）。"""
    dept = SysDept(dept_name=dept_name) if dept_name is not None else None
    user = SysUser(user_id=1, user_name=user_name, dept=dept)
    return LoginUser(
        token=token,
        session_id=f"session-{token}",
        login_time=1_700_000_000_000,
        ipaddr=ipaddr,
        login_location="内网IP",
        browser="Chrome 12",
        os="Windows 11",
        user=user,
    )


# --------------------------------------------------------------------------- Service


class TestServiceBranches:
    def test_no_filter_returns_every_session_reversed(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob"),
        }
        rows = service.select_online_by_info()

        # ``Collections.reverse`` 之后才是最终顺序
        assert [row.token_id for row in rows] == ["b", "a"]

    def test_scan_uses_the_login_token_prefix(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        service.select_online_by_info()
        assert redis.keys_calls == [LOGIN_TOKEN_KEY + "*"]

    def test_filter_by_ipaddr(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice", ipaddr="10.0.0.1"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob", ipaddr="10.0.0.2"),
        }
        rows = service.select_online_by_info(ipaddr="10.0.0.1")

        assert [row.user_name for row in rows] == ["alice"]

    def test_filter_by_user_name(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob"),
        }
        rows = service.select_online_by_info(user_name="bob")

        assert [row.user_name for row in rows] == ["bob"]

    def test_both_filters_are_anded(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice", ipaddr="10.0.0.1"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "alice", ipaddr="10.0.0.2"),
        }
        rows = service.select_online_by_info(ipaddr="10.0.0.1", user_name="alice")

        assert [row.token_id for row in rows] == ["a"]

    def test_both_filters_must_match_not_either(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        """``if (A && B)`` —— 只满足一个的用户**不能**出现。"""
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice", ipaddr="10.0.0.9"),
        }
        assert service.select_online_by_info(ipaddr="10.0.0.1", user_name="alice") == []

    def test_a_blank_filter_is_treated_as_absent(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        """RuoYi 的 ``isEmpty(String)`` 会 ``trim()`` —— ``" "`` 算空，等于不过滤。"""
        redis.store = {LOGIN_TOKEN_KEY + "a": _login_user("a", "alice")}

        assert len(service.select_online_by_info(ipaddr=" ")) == 1
        assert len(service.select_online_by_info(user_name=" ")) == 1


class TestServiceDirtyValues:
    """``loginUserToUserOnline`` 返回 ``null`` -> 被 ``removeAll`` 扔掉."""

    def test_a_session_without_a_user_is_dropped(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {
            LOGIN_TOKEN_KEY + "a": LoginUser(token="a", user=None),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob"),
        }
        rows = service.select_online_by_info()

        assert [row.token_id for row in rows] == ["b"]

    def test_a_null_value_in_redis_is_dropped(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {LOGIN_TOKEN_KEY + "a": None}
        assert service.select_online_by_info() == []

    def test_login_user_to_user_online_copies_every_field(self) -> None:
        online = SysUserOnlineService(redis_cache=_FakeRedisCache()).login_user_to_user_online(  # type: ignore[arg-type]
            _login_user("t9", "alice")
        )

        assert online is not None
        assert online.token_id == "t9"
        assert online.session_id == "session-t9"
        assert online.user_name == "alice"
        assert online.ipaddr == "127.0.0.1"
        assert online.login_location == "内网IP"
        assert online.browser == "Chrome 12"
        assert online.os == "Windows 11"
        assert online.login_time == 1_700_000_000_000
        assert online.dept_name == "研发部门"

    def test_missing_dept_leaves_dept_name_null(self) -> None:
        online = SysUserOnlineService(redis_cache=_FakeRedisCache()).login_user_to_user_online(  # type: ignore[arg-type]
            _login_user("t9", dept_name=None)
        )
        assert online is not None
        assert online.dept_name is None

    def test_login_user_to_user_online_returns_none_for_null_user(self) -> None:
        service = SysUserOnlineService(redis_cache=_FakeRedisCache())  # type: ignore[arg-type]
        assert service.login_user_to_user_online(None) is None
        assert service.login_user_to_user_online(LoginUser(token="x")) is None


class TestServiceDeadCode:
    """``selectUserOnlineList`` 没有调用方，按原则第 4 条照搬."""

    def test_it_returns_every_session_reversed(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob"),
        }
        rows = service.select_user_online_list()
        assert [row.token_id for row in rows] == ["b", "a"]


# --------------------------------------------------------------------------- Controller


class TestRoutes:
    def test_the_two_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }
        assert registered == {
            ("/monitor/online/list", ("GET",)),
            ("/monitor/online/{token_id}", ("DELETE",)),
        }


class TestListEndpoint:
    def test_returns_all_sessions_without_paging(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob"),
        }
        body = list_online(None, None).to_dict()

        assert body["code"] == 200
        assert body["msg"] == "查询成功"
        # 没有 startPage()：total 就是列表长度
        assert body["total"] == 2
        assert len(body["rows"]) == 2

    def test_rows_are_serialized_with_camel_case_aliases(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {LOGIN_TOKEN_KEY + "a": _login_user("a", "alice")}
        row = list_online(None, None).to_dict()["rows"][0].model_dump(by_alias=True)

        assert row["tokenId"] == "a"
        assert row["userName"] == "alice"
        assert row["deptName"] == "研发部门"
        # loginTime 是 epoch **毫秒**数字，不是格式化字符串
        assert row["loginTime"] == 1_700_000_000_000

    def test_user_name_query_uses_the_camel_case_name(
        self, http: Any, redis: _FakeRedisCache
    ) -> None:
        """前端发 ``userName``（Java 形参名），不是 ``user_name``。"""
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob"),
        }
        response = http.get("/monitor/online/list", params={"userName": "bob"})

        assert response.status_code == 200
        assert [row["userName"] for row in response.json()["rows"]] == ["bob"]

    def test_ipaddr_query(self, http: Any, redis: _FakeRedisCache) -> None:
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice", ipaddr="10.0.0.1"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob", ipaddr="10.0.0.2"),
        }
        response = http.get("/monitor/online/list", params={"ipaddr": "10.0.0.2"})

        assert [row["userName"] for row in response.json()["rows"]] == ["bob"]

    def test_both_parameters_are_optional(self, http: Any, redis: _FakeRedisCache) -> None:
        """Java 形参没有 ``@RequestParam`` -> ``required = false``，不会 422。"""
        redis.store = {LOGIN_TOKEN_KEY + "a": _login_user("a", "alice")}
        response = http.get("/monitor/online/list")

        assert response.status_code == 200
        assert len(response.json()["rows"]) == 1

    def test_page_size_is_ignored(self, http: Any, redis: _FakeRedisCache) -> None:
        """前端会带 ``pageNum`` / ``pageSize``，服务端**完全不看**。"""
        redis.store = {
            LOGIN_TOKEN_KEY + "a": _login_user("a", "alice"),
            LOGIN_TOKEN_KEY + "b": _login_user("b", "bob"),
        }
        response = http.get("/monitor/online/list", params={"pageNum": 1, "pageSize": 1})

        assert len(response.json()["rows"]) == 2


class TestForceLogout:
    def test_deletes_the_session_key(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        redis.store = {LOGIN_TOKEN_KEY + "abc": _login_user("abc")}
        body = force_logout("abc")

        assert redis.deleted == [LOGIN_TOKEN_KEY + "abc"]
        assert body["code"] == 200
        assert "data" not in body

    def test_an_unknown_token_is_still_success(
        self, service: SysUserOnlineService, redis: _FakeRedisCache
    ) -> None:
        """``deleteObject`` 的返回值被丢弃 —— 删不到也是 200。"""
        body = force_logout("does-not-exist")

        assert redis.deleted == [LOGIN_TOKEN_KEY + "does-not-exist"]
        assert body["code"] == 200

    def test_over_http(self, http: Any, redis: _FakeRedisCache) -> None:
        redis.store = {LOGIN_TOKEN_KEY + "abc": _login_user("abc")}
        response = http.delete("/monitor/online/abc")

        assert response.status_code == 200
        assert response.json() == {"code": 200, "msg": "操作成功"}
        assert redis.store == {}
