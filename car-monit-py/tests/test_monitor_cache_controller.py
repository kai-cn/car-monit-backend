"""``CacheController`` —— ``GET /monitor/cache``.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/monitor/CacheController.java

三条 ``RedisCallback``
----------------------
Java 用 ``redisTemplate.execute(new RedisCallback<Properties>() {...})`` 发三条命令：

1. ``INFO``            -> ``Properties``（扁平 ``key -> String``）
2. ``INFO commandstats`` -> ``Properties``
3. ``DBSIZE``          -> ``Long``

``RedisTemplate#execute`` 在 ``redis-py`` 里没有对应物（后者本身就是“裸连接”风格），
所以控制器用 ``_execute_raw`` 自己借连接发命令 —— 目的是绕开 ``redis-py`` 给 ``INFO``
注册的 response callback（它会把回复解析成嵌套 dict，与 Java 的扁平 ``Properties``
不同形状）。用例因此要在 ``_FakeRedis.connection_pool`` 上提供 ``get_connection`` /
``release`` 这对接口；底层真正发出命令的仍是 ``execute_command``，用例断言的正是
**命令本身**，而不是某个封装层的形状。

``Properties`` 是无序的
-----------------------
``java.util.Properties`` 继承 ``Hashtable``，``stringPropertyNames()`` 的迭代顺序
不确定；Python 侧按 ``INFO`` 文本的原始顺序输出。键集合相同，顺序稳定 —— 前端按 key
取值，不受影响。用例把"保持文本顺序"这件事钉住，免得以后有人换成 ``sorted()``。
"""

from __future__ import annotations

from typing import Any, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.monitor import cache_controller as controller
from app.api.monitor.cache_controller import (
    COMMAND_STATS_PREFIX,
    build_command_stats,
    get_info,
    parse_info,
    substring_between,
)
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)


# --------------------------------------------------------------------------- fakes

HTTP_INFO = """# Server
redis_version:6.2.6
redis_git_sha1:00000000
redis_build_id:4a4e5f1a1b0e4e5a:99
redis_mode:standalone
os:Linux 5.15.0 x86_64

# Clients
connected_clients:3
blocked_clients:0

# Memory
used_memory:1234567
used_memory_human:1.18M
maxmemory:0
"""

COMMAND_STATS_INFO = """# Commandstats
cmdstat_get:calls=12,usec=100,usec_per_call=8.33
cmdstat_set:calls=3,usec=40,usec_per_call=13.33
"""


class _FakeConnection:
    """``redis.connection.Connection`` 的最小替身：先存命令，再回原始回复."""

    def __init__(self, client: "_FakeRedis") -> None:
        self.client = client
        self.command: Optional[tuple] = None

    def send_command(self, *args: Any) -> None:
        assert self.command is None, "send_command() twice without read_response()"
        self.command = args

    def read_response(self) -> Any:
        assert self.command is not None, "read_response() before send_command()"
        command = self.command
        self.command = None
        return self.client.execute_command(*command)


class _FakeConnectionPool:
    """``ConnectionPool`` 的最小替身：借出 / 归还连接，并记录 ``command_name``."""

    def __init__(self, client: "_FakeRedis") -> None:
        self.client = client
        self.requested: List[Any] = []
        self.released: List[_FakeConnection] = []

    def get_connection(
        self, command_name: Any = None, *args: Any, **options: Any
    ) -> _FakeConnection:
        self.requested.append(command_name)
        return _FakeConnection(self.client)

    def release(self, connection: _FakeConnection) -> None:
        self.released.append(connection)


class _FakeRedis:
    """``redis.Redis`` 的最小替身 —— 只实现控制器用到的两个命令."""

    def __init__(self) -> None:
        self.executed: List[tuple] = []
        self.info_text = HTTP_INFO
        self.command_stats_text = COMMAND_STATS_INFO
        self.db_size = 17
        self.connection_pool = _FakeConnectionPool(self)

    def execute_command(self, *args: Any) -> str:
        self.executed.append(args)
        if args == ("INFO",):
            return self.info_text
        if args == ("INFO", "commandstats"):
            return self.command_stats_text
        raise AssertionError(f"unexpected command: {args!r}")

    def dbsize(self) -> int:
        self.executed.append(("DBSIZE",))
        return self.db_size


class _FakeRedisCache:
    """Java: ``@Autowired RedisCache`` —— 控制器只碰 ``.client``."""

    def __init__(self, client: Optional[_FakeRedis] = None) -> None:
        self.client = client or _FakeRedis()


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def redis(monkeypatch: pytest.MonkeyPatch) -> _FakeRedis:
    SecurityContextHolder.clear_context()
    client = _FakeRedis()
    monkeypatch.setattr(controller, "_REDIS_CACHE", _FakeRedisCache(client))
    authenticate()
    yield client
    SecurityContextHolder.clear_context()
    controller.reset_cache_controller()


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app())


def authenticate(permissions: Optional[set] = None) -> SysUser:
    user = SysUser(user_id=1, user_name="admin")
    login_user = LoginUser(token="t", user=user, permissions=permissions or {"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _build_app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(controller.router)
    return application


# --------------------------------------------------------------------------- parseInfo


class TestParseInfo:
    """``parseInfo(null)`` -> 空 ``Properties``；段落行与空行被丢掉."""

    def test_none_gives_an_empty_map(self) -> None:
        assert parse_info(None) == {}

    def test_blank_text_gives_an_empty_map(self) -> None:
        assert parse_info("") == {}

    def test_section_comments_are_dropped(self) -> None:
        parsed = parse_info("# Server\nredis_version:6.2.6\n")
        assert parsed == {"redis_version": "6.2.6"}

    def test_blank_lines_are_dropped(self) -> None:
        assert parse_info("\n\nredis_port:6379\n\n") == {"redis_port": "6379"}

    def test_lines_without_a_colon_are_dropped(self) -> None:
        """``Properties.load`` 对没有分隔符的行直接跳过，不报错."""
        assert parse_info("garbage\nredis_mode:standalone\n") == {
            "redis_mode": "standalone"
        }

    def test_split_happens_on_the_first_colon_only(self) -> None:
        """``redis_build_id`` 自己就带 ``:`` —— 值必须完整保留."""
        assert parse_info("redis_build_id:4a4e5f:99\n") == {
            "redis_build_id": "4a4e5f:99"
        }

    def test_leading_whitespace_is_skipped(self) -> None:
        """行的前导空白与值的前导空白都被跳过（``Properties.load0``）."""
        assert parse_info("  used_memory: 1234567\n") == {"used_memory": "1234567"}

    def test_trailing_whitespace_is_preserved(self) -> None:
        """Java 的 ``Properties.load`` **不**裁尾部空白 —— 这里也不裁."""
        assert parse_info("used_memory:1234567 \n") == {"used_memory": "1234567 "}

    def test_empty_value_is_kept_as_an_empty_string(self) -> None:
        """``used_memory:`` 后面的空值在 ``Properties`` 里是 ``""``，不是缺键."""
        assert parse_info("used_memory:\n") == {"used_memory": ""}

    def test_the_real_info_payload(self) -> None:
        parsed = parse_info(HTTP_INFO)

        assert parsed["redis_version"] == "6.2.6"
        assert parsed["used_memory_human"] == "1.18M"
        assert "# Server" not in parsed
        assert "Server" not in parsed

    def test_insertion_order_follows_the_text(self) -> None:
        """Java 的 ``Properties`` 无序；这里稳定按文本顺序（见模块 docstring）."""
        parsed = parse_info(HTTP_INFO)
        assert list(parsed)[:3] == [
            "redis_version",
            "redis_git_sha1",
            "redis_build_id",
        ]


# --------------------------------------------------------------------------- substringBetween


class TestSubstringBetween:
    """Java: ``StringUtils.substringBetween(str, open, close)`` —— 任一侧缺失回 ``null``."""

    def test_extracts_the_middle(self) -> None:
        assert substring_between("calls=12,usec=100", "calls=", ",usec") == "12"

    def test_null_input_returns_none(self) -> None:
        assert substring_between(None, "calls=", ",usec") is None

    def test_missing_open_token_returns_none(self) -> None:
        assert substring_between("usec=100", "calls=", ",usec") is None

    def test_missing_close_token_returns_none(self) -> None:
        assert substring_between("calls=12", "calls=", ",usec") is None

    def test_open_token_takes_precedence_when_it_appears_later(self) -> None:
        """Java 先 ``indexOf(open)`` 再在后面找 ``close`` —— 顺序不能反."""
        assert substring_between("usec=1,calls=7,usec=2", "calls=", ",usec") == "7"

    def test_empty_middle_is_an_empty_string(self) -> None:
        assert substring_between("calls=,usec=1", "calls=", ",usec") == ""


# --------------------------------------------------------------------------- commandStats


class TestBuildCommandStats:
    """``cmdstat_<cmd>`` -> ``{"name": <cmd>, "value": <calls>}``."""

    def test_strips_the_cmdstat_prefix(self) -> None:
        pie = build_command_stats({"cmdstat_get": "calls=12,usec=100,usec_per_call=8.33"})

        assert pie == [{"name": "get", "value": "12"}]

    def test_value_is_the_calls_count_as_a_string(self) -> None:
        """``substringBetween`` 返回 ``String`` —— 不是数字，前端 echarts 照样能用."""
        pie = build_command_stats({"cmdstat_set": "calls=3,usec=40"})
        assert pie[0]["value"] == "3"
        assert isinstance(pie[0]["value"], str)

    def test_a_key_without_the_prefix_keeps_its_name(self) -> None:
        """Java: ``StringUtils.removeStart`` —— 前缀不存在时原样返回."""
        pie = build_command_stats({"custom": "calls=1,usec=1"})
        assert pie[0]["name"] == "custom"

    def test_a_value_without_calls_yields_none(self) -> None:
        assert build_command_stats({"cmdstat_get": "broken"}) == [
            {"name": "get", "value": None}
        ]

    def test_empty_input_gives_an_empty_list(self) -> None:
        assert build_command_stats({}) == []

    def test_order_follows_the_source_mapping(self) -> None:
        pie = build_command_stats(
            {
                "cmdstat_get": "calls=12,usec=1",
                "cmdstat_set": "calls=3,usec=1",
            }
        )
        assert [item["name"] for item in pie] == ["get", "set"]

    def test_the_real_commandstats_payload(self) -> None:
        pie = build_command_stats(parse_info(COMMAND_STATS_INFO))

        assert pie == [
            {"name": "get", "value": "12"},
            {"name": "set", "value": "3"},
        ]

    def test_the_prefix_constant_is_the_java_literal(self) -> None:
        assert COMMAND_STATS_PREFIX == "cmdstat_"


# --------------------------------------------------------------------------- 端点


class TestRoutes:
    def test_only_the_bare_path_is_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }
        assert registered == {("/monitor/cache", ("GET",))}

    def test_get_info_takes_no_parameters(self) -> None:
        """Java: ``@GetMapping() public AjaxResult getInfo() throws Exception``."""
        assert get_info.__wrapped__.__code__.co_argcount == 0  # type: ignore[attr-defined]


class TestGetInfo:
    def test_returns_the_three_sections(self, redis: _FakeRedis) -> None:
        body = get_info()

        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert set(body["data"]) == {"info", "dbSize", "commandStats"}

    def test_info_is_the_flattened_map(self, redis: _FakeRedis) -> None:
        data = get_info()["data"]
        assert data["info"]["redis_version"] == "6.2.6"

    def test_db_size_is_a_number(self, redis: _FakeRedis) -> None:
        data = get_info()["data"]
        assert data["dbSize"] == 17
        assert isinstance(data["dbSize"], int)

    def test_command_stats_is_the_pie_list(self, redis: _FakeRedis) -> None:
        data = get_info()["data"]
        assert data["commandStats"] == [
            {"name": "get", "value": "12"},
            {"name": "set", "value": "3"},
        ]

    def test_exactly_three_commands_are_sent(self, redis: _FakeRedis) -> None:
        get_info()

        assert redis.executed == [
            ("INFO",),
            ("INFO", "commandstats"),
            ("DBSIZE",),
        ]

    def test_info_reads_go_through_a_borrowed_connection(self, redis: _FakeRedis) -> None:
        """``INFO`` 必须走裸连接（照抄 ``RedisCallback``），且连接用完必归还."""
        get_info()

        pool = redis.connection_pool
        assert pool.requested == ["INFO", "INFO"]
        assert len(pool.released) == 2

    def test_the_callback_is_not_reused_for_both_info_calls(
        self, redis: _FakeRedis
    ) -> None:
        """``INFO`` 与 ``INFO commandstats`` 必须是**两条**命令，不能共用一个缓存值."""
        data = get_info()["data"]

        assert "redis_version" in data["info"]
        assert "cmdstat_get" not in data["info"]
        assert "redis_version" not in data["commandStats"][0]

    def test_an_empty_redis_still_answers(self, redis: _FakeRedis) -> None:
        redis.info_text = ""
        redis.command_stats_text = ""
        redis.db_size = 0

        data = get_info()["data"]

        assert data["info"] == {}
        assert data["commandStats"] == []
        assert data["dbSize"] == 0

    def test_over_http(self, http: Any) -> None:
        response = http.get("/monitor/cache")

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 200
        assert payload["data"]["dbSize"] == 17


class TestPermission:
    def test_anonymous_is_rejected(self) -> None:
        """没有登录态时 ``@PreAuthorize`` 直接拒绝（不碰 Redis）."""
        SecurityContextHolder.clear_context()
        with pytest.raises(Exception):
            get_info()

    def test_a_user_without_the_permission_is_rejected(self) -> None:
        SecurityContextHolder.clear_context()
        authenticate(permissions={"monitor:online:list"})
        with pytest.raises(Exception):
            get_info()

    def test_the_required_permission_is_exact(self) -> None:
        """``hasPermi`` 是**精确匹配** —— ``monitor:cache:*`` 不算."""
        SecurityContextHolder.clear_context()
        authenticate(permissions={"monitor:cache:*"})
        with pytest.raises(Exception):
            get_info()

    def test_http_403_envelope(self, http: Any) -> None:
        SecurityContextHolder.clear_context()
        response = http.get("/monitor/cache")

        assert response.status_code == 200
        assert response.json()["code"] == 403
        assert response.json()["msg"] == "没有权限，请联系管理员授权"
