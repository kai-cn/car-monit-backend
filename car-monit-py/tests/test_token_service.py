"""``TokenService`` tests -- JWT issuing, Redis session cache and the UA stamp.

# Migrated from: (no Java equivalent -- TokenService has no unit test in the Java project)

What is actually being pinned down here
---------------------------------------
1. **Key material.** jjwt 0.9.1 base64-decodes the String secret, and it decodes whole
   4-character quanta **only** -- a trailing remainder is dropped. The 26-character secret
   therefore yields an 18-byte HMAC key, not 26 and not 19. If this test ever fails, every
   token minted by the Java build stops verifying on cut-over day.
2. **The token carries only ``login_user_key``.** No ``exp``/``sub``/authorities: an
   "improvement" that adds them changes the wire format.
3. **Expiry lives in Redis.** ``refreshToken`` writes both the bean fields and a TTL of
   ``expireTime`` minutes; ``verifyToken`` slides it when fewer than 20 minutes remain.
4. **Error surface.** A bad signature escapes as an exception (Java: unchecked
   ``JwtException`` -> container -> ``/error`` re-dispatch -> ``HTTP 200`` with ``code``
   401), while a *missing* Redis entry is merely anonymous.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import jwt
import pytest
from starlette.requests import Request

from app.common.constant.constants import LOGIN_TOKEN_KEY
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.redis.redis_cache import RedisCache
from app.common.core.context import request_context
from app.common.utils.date_utils import current_time_millis
from app.framework.web.service.token_service import (
    ALGORITHM,
    LOGIN_USER_KEY,
    MILLIS_MINUTE,
    MILLIS_MINUTE_TEN,
    TokenService,
    _decode_secret,
)

WINDOWS_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAC_SAFARI_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)


# --------------------------------------------------------------------------- fakes


class FakeRedis:
    """The handful of commands ``RedisCache`` issues, backed by a dict.

    Mirrors the parts of the Redis protocol that matter here: ``SET key value PX ms``,
    ``GET``, ``DEL`` and ``EXISTS``.
    """

    def __init__(self) -> None:
        self.store: Dict[str, str] = {}
        self.ttls: Dict[str, Optional[int]] = {}
        self.set_calls: List[Tuple[str, Optional[int]]] = []

    def set(self, key: str, value: str, px: Optional[int] = None, nx: bool = False) -> Optional[bool]:
        if nx and key in self.store:
            return None
        self.set_calls.append((key, px))
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


def make_request(headers: Optional[Dict[str, str]] = None) -> Request:
    """Build a Starlette ``Request`` without going through a server."""
    raw_headers = [(name.lower().encode("latin-1"), value.encode("latin-1")) for name, value in (headers or {}).items()]
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


@pytest.fixture()
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture()
def service(fake_redis: FakeRedis) -> TokenService:
    return TokenService(redis_cache=RedisCache(client=fake_redis))  # type: ignore[arg-type]


def make_login_user(user_name: str = "admin") -> LoginUser:
    return LoginUser(
        user=SysUser(user_id=1, user_name=user_name, nick_name="若依", password="$2a$10$hash"),
        permissions={"*:*:*"},
    )


# --------------------------------------------------------------------------- secret


class TestSecretKey:
    def test_configured_secret_decodes_the_way_jjwt_does(self, service: TokenService) -> None:
        """jjwt's ``TextCodec.BASE64`` yields **18** bytes for the 26-character secret.

        The expected hex was produced by running ``TextCodec.BASE64.decode`` from the
        ``jjwt-0.9.1.jar`` this project actually ships, not derived by hand.
        """
        assert len(service.secret_key) == 18
        assert service.secret_key.hex() == "69b71d79f8218a39259a7a29aabb2dbafc31"
        assert service.secret_key != service.secret.encode()

    def test_empty_secret_is_rejected(self) -> None:
        """Java: ``Assert.hasText`` -> IllegalArgumentException -> startup failure."""
        with pytest.raises(ValueError):
            _decode_secret("")

    def test_trailing_partial_quantum_is_dropped(self) -> None:
        """26 chars and the same string cut to 24 decode identically; jjwt drops the rest.

        Padding the secret up to a multiple of four instead yields one extra byte and a key
        Java never uses, which is why Python-minted tokens used to fail in the Java build
        (and vice versa) even though both read the same ``token.secret``.
        """
        assert _decode_secret("abcdefghijklmnopqrstuvwxyz") == _decode_secret(
            "abcdefghijklmnopqrstuvwx"
        )
        assert len(_decode_secret("abcdefghijklmnopqrstuvwxyz")) == 18
        assert len(_decode_secret("abcdefghijklmnopqrstuvwxyz0")) == 18  # 27 字符，余 3
        assert _decode_secret("ab") == b""


# --------------------------------------------------------------------------- java interop


class TestJavaInterop:
    """A token minted by the running Java backend has to verify here.

    Captured from ``POST /login`` on the Java build during the two-frontend comparison. It
    carries no ``exp`` (expiry lives in Redis), so it stays parseable forever and no clock
    is involved. This is the end-to-end counterpart of the hex assertion above: it fails if
    the key material ever drifts again, however subtle the cause.
    """

    JAVA_TOKEN = (
        "eyJhbGciOiJIUzUxMiJ9."
        "eyJsb2dpbl91c2VyX2tleSI6IjJiZDczZGU1LWZjYWQtNGRiOS05OWJjLWIxM2JhYTQ5NzE3NSJ9."
        "hAsLeaHIrb_fN6QkzvlimK92oAVQw9E-v-vQ8oppcwkWR4ENSJ1VXSzOPfFgMm3Kz7w2qPpDfizY2cnEXY38uQ"
    )

    def test_java_signed_token_verifies(self, service: TokenService) -> None:
        claims = service.parse_token(self.JAVA_TOKEN)
        assert claims[LOGIN_USER_KEY] == "2bd73de5-fcad-4db9-99bc-b13baa497175"


# --------------------------------------------------------------------------- issuing


class TestCreateToken:
    def test_token_carries_only_login_user_key(self, service: TokenService) -> None:
        login_user = make_login_user()
        request_context.set_request(make_request({"User-Agent": WINDOWS_CHROME_UA}))
        try:
            token = service.create_token(login_user)
        finally:
            request_context.clear_request()

        claims = jwt.decode(token, service.secret_key, algorithms=[ALGORITHM])
        assert claims == {"login_user_key": login_user.token}
        assert jwt.get_unverified_header(token)["alg"] == "HS512"
        # No exp/iat/sub: expiry lives in Redis, not in the JWT.
        assert "exp" not in claims

    def test_token_is_the_uuid_stored_in_redis(self, service: TokenService, fake_redis: FakeRedis) -> None:
        login_user = make_login_user()
        request_context.set_request(make_request({"User-Agent": WINDOWS_CHROME_UA}))
        try:
            service.create_token(login_user)
        finally:
            request_context.clear_request()

        assert list(fake_redis.store) == [LOGIN_TOKEN_KEY + login_user.token]
        # TTL is expireTime minutes, expressed in milliseconds by the serializer path.
        assert fake_redis.ttls[LOGIN_TOKEN_KEY + login_user.token] == service.expire_time * MILLIS_MINUTE

    def test_does_not_respect_a_preexisting_uuid(self, service: TokenService) -> None:
        login_user = make_login_user()
        login_user.token = "stale-uuid"
        request_context.set_request(make_request({"User-Agent": WINDOWS_CHROME_UA}))
        try:
            service.create_token(login_user)
        finally:
            request_context.clear_request()
        assert login_user.token != "stale-uuid"


class TestRefreshToken:
    def test_sets_login_and_expire_time_from_now(self, service: TokenService) -> None:
        login_user = make_login_user()
        login_user.token = "uuid-1"
        before = current_time_millis()
        service.refresh_token(login_user)
        after = current_time_millis()

        assert before <= login_user.login_time <= after
        assert login_user.expire_time == login_user.login_time + service.expire_time * MILLIS_MINUTE

    def test_caches_the_principal_not_the_token(self, service: TokenService, fake_redis: FakeRedis) -> None:
        login_user = make_login_user()
        login_user.token = "uuid-1"
        service.refresh_token(login_user)

        payload = fake_redis.store[LOGIN_TOKEN_KEY + "uuid-1"]
        # fastjson2 WriteClassName -> "@type" + camelCase keys, exactly what Java writes.
        assert '"@type":"com.ruoyi.common.core.domain.model.LoginUser"' in payload
        assert '"userName":"admin"' in payload
        # fastjson2 ignores Jackson's @JsonIgnore, so the hash is in Redis too.
        assert '"password":"$2a$10$hash"' in payload


class TestVerifyToken:
    def test_refreshes_when_less_than_20_minutes_remain(self, service: TokenService) -> None:
        login_user = make_login_user()
        login_user.token = "uuid-1"
        login_user.expire_time = current_time_millis() + MILLIS_MINUTE_TEN - 1000

        service.verify_token(login_user)

        assert login_user.expire_time > current_time_millis() + MILLIS_MINUTE_TEN

    def test_does_not_refresh_when_window_is_wide(self, service: TokenService, fake_redis: FakeRedis) -> None:
        login_user = make_login_user()
        login_user.token = "uuid-1"
        original = current_time_millis() + 60 * MILLIS_MINUTE
        login_user.expire_time = original

        service.verify_token(login_user)

        assert login_user.expire_time == original
        assert fake_redis.set_calls == []


# --------------------------------------------------------------------------- lookup


class TestGetLoginUser:
    def _issue(self, service: TokenService, login_user: LoginUser) -> str:
        request_context.set_request(make_request({"User-Agent": WINDOWS_CHROME_UA}))
        try:
            return service.create_token(login_user)
        finally:
            request_context.clear_request()

    def test_bearer_prefix_is_stripped(self, service: TokenService) -> None:
        token = self._issue(service, make_login_user())
        found = service.get_login_user(make_request({"Authorization": f"Bearer {token}"}))
        assert found is not None
        assert found.user.user_name == "admin"

    def test_token_without_prefix_also_works(self, service: TokenService) -> None:
        """Java only strips the prefix when present, so a bare JWT is accepted."""
        token = self._issue(service, make_login_user())
        found = service.get_login_user(make_request({"Authorization": token}))
        assert found is not None
        assert found.user.user_name == "admin"

    def test_repeated_prefix_is_removed_everywhere(self, service: TokenService) -> None:
        """``String.replace`` (not ``replaceFirst``): "Bearer Bearer x" -> "x"."""
        token = self._issue(service, make_login_user())
        found = service.get_login_user(make_request({"Authorization": f"Bearer Bearer {token}"}))
        assert found is not None

    def test_missing_header_is_anonymous(self, service: TokenService) -> None:
        assert service.get_login_user(make_request()) is None

    def test_empty_header_is_anonymous(self, service: TokenService) -> None:
        assert service.get_login_user(make_request({"Authorization": ""})) is None

    def test_prefix_only_is_anonymous(self, service: TokenService) -> None:
        assert service.get_login_user(make_request({"Authorization": "Bearer "})) is None

    def test_expired_redis_entry_is_anonymous(self, service: TokenService, fake_redis: FakeRedis) -> None:
        token = self._issue(service, make_login_user())
        fake_redis.store.clear()
        assert service.get_login_user(make_request({"Authorization": f"Bearer {token}"})) is None

    def test_token_without_claim_looks_up_login_tokens_null(self, service: TokenService) -> None:
        """Java: ``getTokenKey(null)`` -> "login_tokens:null", a guaranteed miss."""
        token = jwt.encode({}, service.secret_key, algorithm=ALGORITHM)
        assert service.get_login_user(make_request({"Authorization": f"Bearer {token}"})) is None

    def test_non_string_claim_raises(self, service: TokenService) -> None:
        """Java: ``(String) claims.get(...)`` -> ClassCastException."""
        token = jwt.encode({"login_user_key": 42}, service.secret_key, algorithm=ALGORITHM)
        with pytest.raises(TypeError):
            service.get_login_user(make_request({"Authorization": f"Bearer {token}"}))

    def test_bad_signature_escapes(self, service: TokenService) -> None:
        """Java: ``SignatureException`` (unchecked) leaves the filter -> ``/error`` dispatch."""
        token = jwt.encode({"login_user_key": "u"}, b"a-different-key-entirely", algorithm=ALGORITHM)
        with pytest.raises(jwt.InvalidSignatureError):
            service.get_login_user(make_request({"Authorization": f"Bearer {token}"}))

    def test_malformed_token_escapes(self, service: TokenService) -> None:
        with pytest.raises(jwt.DecodeError):
            service.get_login_user(make_request({"Authorization": "Bearer not-a-jwt"}))

    def test_alien_algorithm_is_rejected(self, service: TokenService) -> None:
        """Only HS512 is accepted, so an ``alg: none`` token cannot slip through."""
        token = jwt.encode({"login_user_key": "u"}, None, algorithm="none")
        with pytest.raises(jwt.InvalidAlgorithmError):
            service.get_login_user(make_request({"Authorization": f"Bearer {token}"}))


# --------------------------------------------------------------------------- cache ops


class TestSessionCacheOps:
    def test_del_login_user_removes_the_key(self, service: TokenService, fake_redis: FakeRedis) -> None:
        fake_redis.store[LOGIN_TOKEN_KEY + "uuid-1"] = "{}"
        service.del_login_user("uuid-1")
        assert fake_redis.store == {}

    def test_del_login_user_ignores_empty_token(self, service: TokenService, fake_redis: FakeRedis) -> None:
        fake_redis.store[LOGIN_TOKEN_KEY + "null"] = "{}"
        service.del_login_user("")
        service.del_login_user(None)
        assert fake_redis.store == {LOGIN_TOKEN_KEY + "null": "{}"}

    def test_set_login_user_without_token_is_a_noop(self, service: TokenService, fake_redis: FakeRedis) -> None:
        service.set_login_user(None)
        service.set_login_user(LoginUser(token=None))
        assert fake_redis.set_calls == []

    def test_set_login_user_re_caches(self, service: TokenService, fake_redis: FakeRedis) -> None:
        login_user = make_login_user()
        login_user.token = "uuid-1"
        service.set_login_user(login_user)
        assert LOGIN_TOKEN_KEY + "uuid-1" in fake_redis.store


# --------------------------------------------------------------------------- user agent


class TestSetUserAgent:
    def _stamp(self, service: TokenService, headers: Dict[str, str]) -> LoginUser:
        login_user = make_login_user()
        request = make_request(headers)
        request_context.set_request(request)
        try:
            service.set_user_agent(login_user)
        finally:
            request_context.clear_request()
        return login_user

    def test_windows_chrome(self, service: TokenService) -> None:
        login_user = self._stamp(service, {"User-Agent": WINDOWS_CHROME_UA})
        assert login_user.browser == "Chrome"
        # useragentutils names Windows by release; so do we.
        assert login_user.os == "Windows 10"

    def test_mac_safari_uses_bare_family(self, service: TokenService) -> None:
        login_user = self._stamp(service, {"User-Agent": MAC_SAFARI_UA})
        assert login_user.browser == "Safari"
        assert login_user.os == "Mac OS X"

    def test_unknown_user_agent(self, service: TokenService) -> None:
        """An agent neither library knows: both fall back to "Unknown" on every field."""
        login_user = self._stamp(service, {"User-Agent": "SomeAgent/1.0"})
        assert login_user.browser == "Unknown"
        assert login_user.os == "Unknown"

    def test_non_browser_client_diverges_by_library(self, service: TokenService) -> None:
        """Pinned divergence: useragentutils has no ``curl`` pattern and would say "Unknown".

        ``user-agents`` detects HTTP clients as browsers. Kept as reported (display-only
        field) and recorded in COMPATIBILITY.md rather than papered over with a denylist.
        """
        login_user = self._stamp(service, {"User-Agent": "curl/8.0.1"})
        assert login_user.browser == "curl"
        # The OS side still matches Java: no match -> UNKNOWN.
        assert login_user.os == "Unknown"

    def test_missing_user_agent_header(self, service: TokenService) -> None:
        login_user = self._stamp(service, {})
        assert login_user.browser == "Unknown"
        assert login_user.os == "Unknown"

    def test_loopback_is_reported_as_intranet(self, service: TokenService) -> None:
        login_user = self._stamp(service, {"User-Agent": WINDOWS_CHROME_UA})
        assert login_user.ipaddr == "127.0.0.1"
        # addressEnabled=false in application.yml; 127.0.0.1 short-circuits earlier anyway.
        assert login_user.login_location == "内网IP"

    def test_missing_request_raises(self, service: TokenService) -> None:
        """Java: ``ServletUtils.getRequest()`` returns null -> NullPointerException."""
        request_context.clear_request()
        with pytest.raises(RuntimeError):
            service.set_user_agent(make_login_user())

    def test_session_id_is_memoised_per_request(self, service: TokenService) -> None:
        """Two ``getSession()`` calls in one request return the same id."""
        request = make_request({"User-Agent": WINDOWS_CHROME_UA})
        request_context.set_request(request)
        try:
            first = make_login_user()
            second = make_login_user()
            service.set_user_agent(first)
            service.set_user_agent(second)
        finally:
            request_context.clear_request()

        assert first.session_id == second.session_id
        # Tomcat renders 16 random bytes as 32 upper-case hex characters.
        assert len(first.session_id) == 32
        assert first.session_id == first.session_id.upper()
        int(first.session_id, 16)  # hex, would raise otherwise


# --------------------------------------------------------------------------- claims


class TestParseToken:
    def test_audience_is_not_validated(self, service: TokenService) -> None:
        """jjwt 0.9.1 ignores ``aud`` unless ``requireAudience`` was called."""
        token = jwt.encode(
            {"login_user_key": "u", "aud": "someone-else"}, service.secret_key, algorithm=ALGORITHM
        )
        assert service.parse_token(token)["login_user_key"] == "u"

    def test_exp_is_validated(self, service: TokenService) -> None:
        """jjwt *does* enforce ``exp`` when the claim is present."""
        token = jwt.encode(
            {
                "login_user_key": "u",
                "exp": datetime(2020, 1, 1, tzinfo=timezone.utc),
            },
            service.secret_key,
            algorithm=ALGORITHM,
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            service.parse_token(token)

    def test_get_username_from_token_has_no_subject(self, service: TokenService) -> None:
        """RuoYi never sets ``sub``, so this dead method always returns None."""
        token = jwt.encode({"login_user_key": "u"}, service.secret_key, algorithm=ALGORITHM)
        assert service.get_username_from_token(token) is None
