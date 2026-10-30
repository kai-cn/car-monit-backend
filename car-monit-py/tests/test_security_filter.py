"""Spring Security filter chain -- the answer every caller actually gets.

# Migrated from: (no Java test) -- behaviour copied from
#   SecurityConfig, JwtAuthenticationTokenFilter, AuthenticationEntryPointImpl,
#   LogoutSuccessHandlerImpl, ExceptionTranslationFilter

Why this file exists
--------------------
The Java project has no security test at all, so nothing documents what an unauthenticated
client sees. Those answers are surprising enough to be worth pinning:

* a refusal is usually **HTTP 200** with ``{"code":401,...}`` in the body;
* a *forbidden* (authenticated but not allowed) answer is a **real 403** with a completely
  different body -- Spring's ``BasicErrorController``;
* an unmapped path answers **401**, not 404, because authorisation runs before routing;
* ``anonymous()`` rules **reject logged-in callers**, so ``/system/file/view/**`` is a 403 for
  every real user.

Each test names the Spring class that produces the behaviour.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.common.constant.constants import LOGIN_TOKEN_KEY
from app.common.core.context import request_context
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.redis.redis_cache import RedisCache
from app.framework.config.security_config import AccessMode, resolve_access
from app.framework.manager.factory import async_factory as async_factory_module
from app.framework.manager.async_manager import AsyncManager
from app.framework.security.context.security_context import (
    AnonymousAuthenticationToken,
    UsernamePasswordAuthenticationToken,
)
from app.framework.security.filter import jwt_authentication_token_filter as jwt_filter_module
from app.framework.security.handle.authentication_entry_point_impl import (
    reset_authentication_entry_point,
)
from app.framework.security.handle.logout_success_handler_impl import reset_logout_success_handler
from app.framework.web.service import token_service as token_service_module
from app.framework.web.service.token_service import get_token_service, reset_token_service
from app.middleware.security import is_allowed
from app.system.domain.sys_logininfor import SysLogininfor

WINDOWS_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

#: A path matched by ``anyRequest().authenticated()`` and *not* mapped to a controller, so
#: reaching the router is observable as a 404 instead of a 401.
#:
#: 这块探针以前借的是"已配置规则但还没迁移的 controller"路径（``/system/user/list`` ->
#: ``/system/dept/list`` -> ``/system/menu/list`` -> ``/system/config/list`` ->
#: ``/monitor/online/list``）。每迁移一个包就得搬家一次，已经搬了五次 —— 所以现在换成
#: 一个**任何语言里都永远不存在**的路径：它不匹配 ``AUTHORIZATION_RULES`` 里的任何一条，
#: 必然落到 ``anyRequest().authenticated()``，而 controller 永远查不到 ⇒ 恒为 404。
#: Java 侧同样是 404（``BasicErrorController``），两边可观测行为一致，且以后迁移任何
#: 模块都不需要再动这个常量。
PROTECTED_UNMAPPED_PATH = "/migration/probe/never-mapped"


# --------------------------------------------------------------------------- fakes


class FakeRedis:
    """Minimal ``redis.Redis`` stand-in (same shape as the one in ``test_token_service``)."""

    def __init__(self) -> None:
        self.store: Dict[str, str] = {}
        self.ttls: Dict[str, Optional[int]] = {}

    def set(self, key: str, value: str, px: Optional[int] = None, nx: bool = False) -> Optional[bool]:
        if nx and key in self.store:
            return None
        self.store[key] = value
        self.ttls[key] = px
        return True

    def get(self, key: str) -> Optional[str]:
        return self.store.get(key)

    def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            if key in self.store:
                del self.store[key]
                self.ttls.pop(key, None)
                removed += 1
        return removed

    def exists(self, key: str) -> int:
        return 1 if key in self.store else 0


class _RecordingLogininforService:
    """Collects the rows ``AsyncFactory.record_logininfor`` would have inserted."""

    def __init__(self, rows: List[SysLogininfor]) -> None:
        self._rows = rows

    def insert_logininfor(self, logininfor: SysLogininfor) -> int:
        self._rows.append(logininfor)
        return 1


def make_request(headers: Optional[Dict[str, str]] = None) -> Request:
    """A Starlette ``Request`` for code that resolves the request from the context."""
    raw_headers = [
        (name.lower().encode("latin-1"), value.encode("latin-1"))
        for name, value in (headers or {}).items()
    ]
    scope: Dict[str, Any] = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/login",
        "root_path": "",
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 54321),
        "server": ("testserver", 80),
    }
    return Request(scope)


# --------------------------------------------------------------------------- fixtures


@pytest.fixture()
def session_store(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    """Point the (lazily resolved) ``RedisCache`` at a dict, and restore it afterwards."""
    fake = FakeRedis()
    monkeypatch.setattr(token_service_module, "get_redis_cache", lambda: RedisCache(client=fake))  # type: ignore[arg-type]
    reset_token_service()
    yield fake
    reset_token_service()


@pytest.fixture()
def audit_rows(monkeypatch: pytest.MonkeyPatch) -> List[SysLogininfor]:
    """Capture audit rows and run the "async" task inline.

    ``AsyncManager`` is the only piece replaced: the task factory itself
    (``AsyncFactory.record_logininfor``) runs unchanged, so the status mapping and the
    browser/os stamp are all under test.
    """
    rows: List[SysLogininfor] = []
    monkeypatch.setattr(async_factory_module, "get_logininfor_service", lambda: _RecordingLogininforService(rows))
    monkeypatch.setattr(AsyncManager, "execute", lambda self, task: task())
    return rows


@pytest.fixture()
def authenticated_token(session_store: FakeRedis) -> str:
    """Mint a token the way ``/login`` will, through the public ``TokenService`` API."""
    service = get_token_service()
    request_context.set_request(make_request({"User-Agent": WINDOWS_CHROME_UA}))
    try:
        login_user = LoginUser(
            user=SysUser(user_id=1, user_name="admin"),
            permissions={"*:*:*"},
        )
        return service.create_token(login_user)
    finally:
        request_context.clear_request()


def _bearer(token: str, user_agent: Optional[str] = None) -> Dict[str, str]:
    """An ``Authorization`` header, optionally with the ``User-Agent`` the caller sends.

    The UA matters for the audit trail: ``AsyncFactory.recordLogininfor`` reads it off the
    *current* request, so a logout call is stamped with the UA of the logout request and not
    with the one that minted the token.
    """
    headers = {"Authorization": f"Bearer {token}"}
    if user_agent is not None:
        headers["User-Agent"] = user_agent
    return headers


# --------------------------------------------------------------------------- rule table


class TestAuthorizationRuleTable:
    """Java: ``SecurityConfig#configure(HttpSecurity)`` -> first match wins."""

    def test_login_and_captcha_are_open(self) -> None:
        assert resolve_access("GET", "/login") is AccessMode.PERMIT_ALL
        assert resolve_access("POST", "/login") is AccessMode.PERMIT_ALL
        assert resolve_access("GET", "/captchaImage") is AccessMode.PERMIT_ALL

    def test_static_rules_cover_get_only(self) -> None:
        """``antMatchers(HttpMethod.GET, ...)`` -- a POST to ``/`` is not permitAll."""
        assert resolve_access("GET", "/") is AccessMode.PERMIT_ALL
        assert resolve_access("GET", "/index.html") is AccessMode.PERMIT_ALL
        assert resolve_access("GET", "/a/b/index.html") is AccessMode.PERMIT_ALL
        assert resolve_access("GET", "/assets/app.js") is AccessMode.PERMIT_ALL
        assert resolve_access("GET", "/assets/app.css") is AccessMode.PERMIT_ALL
        assert resolve_access("GET", "/profile/avatar.png") is AccessMode.PERMIT_ALL
        # Every other verb falls through to anyRequest().authenticated().
        assert resolve_access("POST", "/") is AccessMode.AUTHENTICATED
        assert resolve_access("HEAD", "/") is AccessMode.AUTHENTICATED

    def test_trailing_slash_is_significant(self) -> None:
        """``AntPathMatcher`` stage 2: ``/login`` does not match ``/login/``."""
        assert resolve_access("GET", "/login/") is AccessMode.AUTHENTICATED

    def test_download_rules_follow_declaration_order(self) -> None:
        """``/common/download**`` cannot cross a ``/``, so the second rule is reachable."""
        assert resolve_access("GET", "/common/download") is AccessMode.ANONYMOUS
        assert resolve_access("GET", "/common/download/resource") is AccessMode.AUTHENTICATED

    def test_preview_endpoints_are_anonymous_not_permit_all(self) -> None:
        assert resolve_access("GET", "/system/file/view/a.jpg") is AccessMode.ANONYMOUS
        assert resolve_access("GET", "/system/notice/view/a.jpg") is AccessMode.ANONYMOUS

    def test_static_resource_rules_shadow_the_deny_all_rules(self) -> None:
        """RuoYi wart: the static-resource ``permitAll`` block is declared *first*, so it wins.

        ``antMatchers(HttpMethod.GET, "/*.html", "/**/*.html", "/**/*.js", "/**/*.css")``
        precedes the swagger/druid ``denyAll()`` block, and Spring's matcher list is
        first-match-wins -- so ``denyAll`` is dead for these GET paths. The Java build behaves
        exactly the same way; this is mirrored, not repaired (see ``COMPATIBILITY.md``).
        """
        assert resolve_access("GET", "/swagger-ui.html") is AccessMode.PERMIT_ALL
        assert resolve_access("GET", "/druid/index.html") is AccessMode.PERMIT_ALL
        assert resolve_access("GET", "/webjars/springfox.js") is AccessMode.PERMIT_ALL

    def test_management_endpoints_are_deny_all(self) -> None:
        """The parts of the ``denyAll`` block that no earlier rule can reach."""
        assert resolve_access("GET", "/swagger-resources/configuration/ui") is AccessMode.DENY_ALL
        # ``/*/api-docs`` is one segment plus "api-docs" -- it swallows /v3/api-docs too.
        assert resolve_access("GET", "/v3/api-docs") is AccessMode.DENY_ALL
        assert resolve_access("GET", "/druid/api/list") is AccessMode.DENY_ALL
        # .json is not in the static-resource list, so this one really is denied.
        assert resolve_access("GET", "/webjars/lib/data.json") is AccessMode.DENY_ALL
        # Non-GET verbs skip the GET-only static rules and still hit denyAll.
        assert resolve_access("POST", "/swagger-ui.html") is AccessMode.DENY_ALL

    def test_unmatched_path_falls_through_to_authenticated(self) -> None:
        assert resolve_access("GET", "/system/user/list") is AccessMode.AUTHENTICATED
        assert resolve_access("GET", "/definitely-not-a-route") is AccessMode.AUTHENTICATED

    def test_health_is_open(self) -> None:
        """ADDED rule -- ``/health`` has no Java counterpart. See ``COMPATIBILITY.md``."""
        assert resolve_access("GET", "/health") is AccessMode.PERMIT_ALL


class TestAccessExpressions:
    """Java: ``PermitAllExpression`` / ``AnonymousExpression`` / ``AuthenticatedExpression``."""

    @staticmethod
    def _anonymous() -> AnonymousAuthenticationToken:
        return AnonymousAuthenticationToken()

    @staticmethod
    def _authenticated(authorities: Optional[List[Any]] = None) -> UsernamePasswordAuthenticationToken:
        return UsernamePasswordAuthenticationToken("admin", None, authorities)

    def test_permit_all_ignores_the_caller(self) -> None:
        assert is_allowed(AccessMode.PERMIT_ALL, self._anonymous())
        assert is_allowed(AccessMode.PERMIT_ALL, self._authenticated())

    def test_authenticated_rejects_anonymous(self) -> None:
        assert not is_allowed(AccessMode.AUTHENTICATED, self._anonymous())
        assert is_allowed(AccessMode.AUTHENTICATED, self._authenticated())

    def test_anonymous_rejects_authenticated(self) -> None:
        """The RuoYi wart: ``anonymous()`` is a requirement, not a permission."""
        assert is_allowed(AccessMode.ANONYMOUS, self._anonymous())
        assert not is_allowed(AccessMode.ANONYMOUS, self._authenticated())

    def test_deny_all_rejects_everybody(self) -> None:
        assert not is_allowed(AccessMode.DENY_ALL, self._anonymous())
        assert not is_allowed(AccessMode.DENY_ALL, self._authenticated())

    def test_three_argument_token_is_authenticated_even_with_null_authorities(self) -> None:
        """Spring's 3-arg constructor sets ``authenticated = true`` regardless of the list.

        ``JwtAuthenticationTokenFilter`` passes ``loginUser.getAuthorities()``, which is
        hard-coded ``null`` -- if the arity were ignored, every request would be anonymous.
        """
        token = UsernamePasswordAuthenticationToken("admin", None, None)
        assert token.is_authenticated() is True
        assert token.get_authorities() is None

    def test_two_argument_token_is_not_authenticated(self) -> None:
        assert UsernamePasswordAuthenticationToken("admin", "secret").is_authenticated() is False


# --------------------------------------------------------------------------- HTTP surface


class TestEntryPoint:
    """Java: ``AuthenticationEntryPointImpl`` + ``ServletUtils.renderString``."""

    def test_protected_path_without_token(self, client: TestClient) -> None:
        response = client.get(PROTECTED_UNMAPPED_PATH)
        # HTTP 200 -- renderString hard-codes setStatus(200); the real code is in the body.
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        # Java: ``AjaxResult`` 是 ``HashMap`` -> 桶序 msg(0) -> code(3)。
        assert response.text == (
            f'{{"msg":"请求访问：{PROTECTED_UNMAPPED_PATH}，认证失败，无法访问系统资源","code":401}}'
        )

    def test_deny_all_answers_401_not_403_for_anonymous_callers(self, client: TestClient) -> None:
        """``ExceptionTranslationFilter``: denied + anonymous -> entry point, not 403."""
        # /druid/index.html would be permitAll via the shadowing ``/*.html`` rule, so pick a
        # path that the denyAll block actually governs.
        response = client.get("/druid/api/list")
        assert response.status_code == 200
        assert response.json()["code"] == 401
        assert "认证失败" in response.json()["msg"]

    def test_logout_is_not_reachable_without_being_a_logout_request(self, client: TestClient) -> None:
        """A GET on a protected path still goes through the rule table (sanity for the above)."""
        response = client.get("/logout/extra")
        assert response.status_code == 200
        assert response.json()["code"] == 401


class TestAuthenticatedCaller:
    """Java: ``JwtAuthenticationTokenFilter`` -> ``FilterSecurityInterceptor``."""

    def test_valid_token_passes_an_authenticated_rule(
        self, client: TestClient, authenticated_token: str
    ) -> None:
        # No controller is mapped at the probe path, so "allowed" shows up as a 404 from the
        # router rather than a 401 from the filter chain. The 401 case above stays valid
        # either way.
        response = client.get(PROTECTED_UNMAPPED_PATH, headers=_bearer(authenticated_token))
        assert response.status_code == 404
        assert response.json()["error"] == "Not Found"

    def test_valid_token_is_forbidden_by_an_anonymous_rule(
        self, client: TestClient, authenticated_token: str
    ) -> None:
        """A logged-in user is refused where ``anonymous()`` is required -- real 403."""
        response = client.get("/system/file/view/a.jpg", headers=_bearer(authenticated_token))
        assert response.status_code == 403
        body = response.json()
        # Spring's BasicErrorController body, *not* an AjaxResult.
        assert set(body.keys()) == {"timestamp", "status", "error", "path"}
        assert body["error"] == "Forbidden"
        assert body["path"] == "/system/file/view/a.jpg"

    def test_anonymous_caller_passes_an_anonymous_rule(
        self, client: TestClient
    ) -> None:
        # ``SysFileController`` now exists, so "allowed" shows up as a 200 from the
        # controller rather than a 404 from the router. Two segments after the prefix
        # means ``/{bucket}/{fileName}`` catches it with ``bucket = "view"`` -- the same
        # match Spring's ``AntPathMatcher`` makes. ``getFile`` swallows every OSS error,
        # so the body is empty and the status is 200 no matter whether boto3 is installed.
        response = client.get("/system/file/view/a.jpg")
        assert response.status_code == 200
        assert response.content == b""

    def test_malformed_token_answers_401_not_500(self, client: TestClient) -> None:
        """A bad signature throws out of the filter, and the container re-dispatches to /error.

        ``/error`` is not in the permit-all list, so that second pass is refused by
        ``AuthenticationEntryPointImpl``: HTTP 200, ``code`` 401, and the path in the message
        is ``/error`` -- not the path that was requested. Measured on the running Java build;
        answering the container's 500 error page here was wrong.
        """
        response = client.get(PROTECTED_UNMAPPED_PATH, headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 200
        body = response.json()
        assert body == {"msg": "请求访问：/error，认证失败，无法访问系统资源", "code": 401}

    def test_malformed_token_on_logout_answers_401_not_500(self, client: TestClient) -> None:
        """``LogoutSuccessHandlerImpl`` parses the token too, so /logout fails the same way."""
        response = client.post("/logout", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 200
        assert response.json() == {"msg": "请求访问：/error，认证失败，无法访问系统资源", "code": 401}

    def test_token_is_still_honoured_through_the_prefix_quirk(
        self, client: TestClient, authenticated_token: str
    ) -> None:
        """``String.replace("Bearer ", "")`` removes every occurrence, not just the first."""
        response = client.get(
            PROTECTED_UNMAPPED_PATH,
            headers={"Authorization": f"Bearer Bearer {authenticated_token}"},
        )
        assert response.status_code == 404


class TestCorsBeforeSecurity:
    """Java: ``CorsFilter`` is registered *before* the logout and JWT filters."""

    def test_preflight_needs_no_token(self, client: TestClient) -> None:
        response = client.options(
            PROTECTED_UNMAPPED_PATH,
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        # CorsFilter answers preflights itself and never calls the chain (no 401 envelope).
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://example.com"


class TestLogout:
    """Java: ``LogoutFilter`` + ``LogoutSuccessHandlerImpl``."""

    def test_logout_without_a_token_still_succeeds(self, client: TestClient, audit_rows: list) -> None:
        response = client.post("/logout")
        assert response.status_code == 200
        assert response.text == '{"msg":"退出成功","code":200}'
        # Nothing was authenticated, so there is no session to delete and no audit row.
        assert audit_rows == []

    def test_logout_deletes_the_session_and_writes_the_audit_row(
        self,
        client: TestClient,
        authenticated_token: str,
        session_store: FakeRedis,
        audit_rows: List[SysLogininfor],
    ) -> None:
        key = LOGIN_TOKEN_KEY + _session_key(session_store)
        assert key in session_store.store

        response = client.post("/logout", headers=_bearer(authenticated_token, WINDOWS_CHROME_UA))
        assert response.status_code == 200
        assert response.json() == {"code": 200, "msg": "退出成功"}

        # 1) the Redis entry is gone -- the only thing that invalidates a token
        assert session_store.store == {}

        # 2) the audit row mirrors AsyncFactory.recordLogininfor
        assert len(audit_rows) == 1
        row = audit_rows[0]
        assert row.user_name == "admin"
        assert row.status == "0"  # Constants.SUCCESS, not Constants.LOGOUT
        assert row.msg == "退出成功"
        assert row.browser == "Chrome"
        assert row.os == "Windows 10"
        assert row.login_location == "内网IP"
        # login_time is written by the INSERT (sysdate()), never set by Java code.
        assert row.login_time is None

    def test_second_logout_with_the_same_token_has_nothing_left_to_delete(
        self,
        client: TestClient,
        authenticated_token: str,
        session_store: FakeRedis,
        audit_rows: List[SysLogininfor],
    ) -> None:
        client.post("/logout", headers=_bearer(authenticated_token, WINDOWS_CHROME_UA))
        rows_after_first = len(audit_rows)

        response = client.post("/logout", headers=_bearer(authenticated_token, WINDOWS_CHROME_UA))
        assert response.status_code == 200
        assert response.json() == {"code": 200, "msg": "退出成功"}
        # The session is already gone -> getLoginUser returns null -> no second audit row.
        assert len(audit_rows) == rows_after_first
        assert session_store.store == {}


def _session_key(session_store: FakeRedis) -> str:
    """The single ``login_tokens:`` suffix currently cached."""
    keys = [key for key in session_store.store if key.startswith(LOGIN_TOKEN_KEY)]
    assert len(keys) == 1, keys
    return keys[0][len(LOGIN_TOKEN_KEY):]


@pytest.fixture(autouse=True)
def _reset_security_singletons() -> Any:
    """Hand every test a pristine set of Spring-style singletons.

    In Java ``TokenService``, the entry point and the logout handler are singletons that hold
    their collaborators (``RedisCache`` above all) for the life of the JVM. Here the same
    references are cached on first use -- so if a test swaps ``get_redis_cache``, the next test
    would still be talking to the previous test's fake Redis. Dropping the singletons on both
    sides of each test is the equivalent of a fresh container.
    """
    _reset_security_beans()
    yield
    _reset_security_beans()


def _reset_security_beans() -> None:
    jwt_filter_module.reset_jwt_authentication_token_filter()
    reset_authentication_entry_point()
    reset_logout_success_handler()
    reset_token_service()
