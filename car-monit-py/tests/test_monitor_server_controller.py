"""``ServerController`` —— ``GET /monitor/server``.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/monitor/ServerController.java

这里只测**控制器的骨头**：路由、权限点、``copyTo()`` -> ``AjaxResult.success(server)``
这条装配顺序。``Cpu`` / ``Mem`` / ``Jvm`` / ``Sys`` / ``SysFileInfo`` / ``Server`` 本身的
行为（含 ``Cpu.getTotal()`` 的既有 bug、``convertFileSize`` 的取整）在
``tests/test_server_domain.py`` 里逐条钉住，不在这里重复。

用假 ``Server`` 而不是真的采集
------------------------------
真 ``Server.copy_to()`` 会 ``time.sleep(1)``（``OSHI_WAIT_SECOND = 1000``），
拿它做用例既慢又依赖宿主机的 CPU / 磁盘，断言不出任何东西。所以这里把控制器模块里的
``Server`` 换成记录调用的替身 —— Java 侧对应的写法是
``when(serverService.getInfo())`` 这类桩。真实采集留给 ``test_server_domain.py`` 的
``TestRealCollectionSmoke``（它只断言"不炸 + 形状对"）。
"""

from __future__ import annotations

from typing import Any, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.monitor import server_controller as controller
from app.api.monitor.server_controller import get_info
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)

#: 假 ``Server.to_json_dict()`` 的返回值 —— 形状与真的一致（见 server.py）。
SERVER_PAYLOAD = {
    "cpu": {"cpuNum": 8, "total": 1234.5, "sys": 1.2, "used": 3.4, "wait": 0.0, "free": 95.4},
    "mem": {"total": 31.25, "used": 12.5, "free": 18.75, "usage": 40.0},
    "jvm": {"total": 31.25, "max": 31.25, "free": 18.75, "used": 12.5, "usage": 40.0},
    "sys": {
        "computerName": "dev",
        "computerIp": "127.0.0.1",
        "userDir": "/srv",
        "osName": "Linux",
        "osArch": "amd64",
    },
    "sysFiles": [
        {
            "dirName": "/",
            "sysTypeName": "ext4",
            "typeName": "本地固定磁盘 (ext4)",
            "total": "100.0 GB",
            "free": "40.0 GB",
            "used": "60.0 GB",
            "usage": 60.0,
        }
    ],
}


# --------------------------------------------------------------------------- fakes


class _FakeServer:
    """Java: ``new Server(); server.copyTo();`` 里的 ``Server``."""

    instances: List["_FakeServer"] = []
    #: 置 true 时 ``copy_to`` 抛错，用来验证"不 catch"
    fail_on_copy = False

    def __init__(self) -> None:
        self.calls: List[str] = []
        _FakeServer.instances.append(self)

    def copy_to(self) -> None:
        self.calls.append("copy_to")
        if _FakeServer.fail_on_copy:
            raise OSError("psutil: no such process")

    def to_json_dict(self) -> Any:
        self.calls.append("to_json_dict")
        return SERVER_PAYLOAD


@pytest.fixture(autouse=True)
def server(monkeypatch: pytest.MonkeyPatch) -> Any:
    SecurityContextHolder.clear_context()
    _FakeServer.instances = []
    _FakeServer.fail_on_copy = False
    monkeypatch.setattr(controller, "Server", _FakeServer)
    authenticate()
    yield _FakeServer
    SecurityContextHolder.clear_context()


@pytest.fixture
def http() -> Any:
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_lenient() -> Any:
    """``ServerErrorMiddleware`` 发完 code 500 的 body 后会**重新抛出** —— 要看到 body
    就得关掉 ``raise_server_exceptions``（与 ``test_sys_logininfor_controller.py`` 同做法）."""
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


@pytest.fixture
def http_anonymous() -> Any:
    return TestClient(_build_app(login=False))


def authenticate(permissions: Optional[set] = None) -> SysUser:
    user = SysUser(user_id=1, user_name="admin")
    login_user = LoginUser(token="t", user=user, permissions=permissions or {"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)

    @application.middleware("http")
    async def _fake_jwt(request: Any, call_next: Any) -> Any:
        # ``SecurityContextHolder`` 是 contextvars 实现：autouse fixture 里设的登录态会
        # 跟着请求跑进工作线程，所以“匿名”那条必须**每个请求清一次**。
        SecurityContextHolder.clear_context()
        if login:
            authenticate()
        return await call_next(request)

    application.include_router(controller.router)
    return application


# --------------------------------------------------------------------------- 路由


class TestRoutes:
    def test_the_bare_path_is_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in controller.router.routes
        }
        assert registered == {("/monitor/server", ("GET",))}

    def test_it_takes_no_parameters(self) -> None:
        """Java: ``@GetMapping() public AjaxResult getInfo() throws Exception``."""
        assert get_info.__wrapped__.__code__.co_argcount == 0  # type: ignore[attr-defined]

    def test_there_is_no_trailing_slash_variant(self) -> None:
        """``@GetMapping()`` 映射的是 ``/monitor/server`` 本身，没有 ``/monitor/server/``."""
        paths = [route.path for route in controller.router.routes]
        assert "/monitor/server/" not in paths


# --------------------------------------------------------------------------- 端点


class TestGetInfo:
    def test_copy_to_runs_before_serialization(self, http: Any, server: Any) -> None:
        """Java: ``server.copyTo(); return AjaxResult.success(server);`` —— 顺序不能反."""
        get_info()

        assert server.instances[0].calls == ["copy_to", "to_json_dict"]

    def test_a_fresh_server_is_created_per_request(self, http: Any, server: Any) -> None:
        get_info()
        get_info()

        assert len(server.instances) == 2
        assert server.instances[0] is not server.instances[1]

    def test_the_envelope_is_success_with_data(self, server: Any) -> None:
        body = get_info()

        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert "data" in body

    def test_the_payload_is_verbatim(self, server: Any) -> None:
        assert get_info()["data"] == SERVER_PAYLOAD

    def test_the_five_sections_are_present(self, server: Any) -> None:
        data = get_info()["data"]
        assert set(data) == {"cpu", "mem", "jvm", "sys", "sysFiles"}

    def test_a_copy_to_failure_is_not_swallowed(self, server: Any) -> None:
        """Java 的 ``getInfo() throws Exception`` —— 异常交给全局处理器，不是就地 catch."""
        server.fail_on_copy = True

        with pytest.raises(OSError):
            get_info()

    def test_over_http(self, http: Any) -> None:
        response = http.get("/monitor/server")

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 200
        assert payload["data"]["cpu"]["cpuNum"] == 8

    def test_over_http_a_failure_becomes_code_500(
        self, http_lenient: Any, server: Any
    ) -> None:
        """Java: ``getInfo() throws Exception`` -> 全局处理器回 **HTTP 200 + code 500**."""
        server.fail_on_copy = True
        response = http_lenient.get("/monitor/server")

        assert response.status_code == 200
        assert response.json()["code"] == 500


# --------------------------------------------------------------------------- 权限


class TestPermission:
    def test_the_permission_is_monitor_server_list(self) -> None:
        SecurityContextHolder.clear_context()
        authenticate(permissions={"monitor:server:list"})
        assert get_info()["code"] == 200

    def test_another_monitor_permission_is_not_enough(self) -> None:
        """``hasPermi`` 精确匹配 —— ``monitor:cache:list`` 不能顶替."""
        SecurityContextHolder.clear_context()
        authenticate(permissions={"monitor:cache:list"})
        with pytest.raises(Exception):
            get_info()

    def test_anonymous_is_rejected(self, http_anonymous: Any) -> None:
        response = http_anonymous.get("/monitor/server")

        assert response.status_code == 200
        assert response.json()["code"] == 403
        assert response.json()["msg"] == "没有权限，请联系管理员授权"
