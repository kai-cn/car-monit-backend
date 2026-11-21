"""Login use case -- captcha, ``UserDetailsService``, ``DaoAuthenticationProvider``, JWT.

# Migrated from: (no Java test) -- behaviour copied from
#   SysLoginService, UserDetailsServiceImpl, SysPermissionService, DaoAuthenticationProvider,
#   ProviderManager, KaptchaTextCreator, CaptchaController

Why this file exists
--------------------
The Java project has no login test, yet the login path is where four of its quirks collide.
Each is pinned here with the class that produces it:

* the captcha is **consumed before it is compared**, so a typo burns the challenge;
* a request with **no** ``code`` skips the captcha entirely, whatever ``captchaType`` says;
* an unknown user and a wrong password answer the *same* message (``用户不存在/密码错误``),
  while a disabled account leaks its own sentence (``对不起，您的账号：xxx 已停用``);
* every failure is HTTP 200 with the real code in the body -- nothing here raises a 4xx.

The double the tests use for Redis is a plain dict, so what is asserted is the exact key
(``captcha_codes:<uuid>``, ``login_tokens:<uuid>``) and the exact TTL that production writes.
"""

from __future__ import annotations

import base64
import io
import random
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set

import pytest
from starlette.requests import Request
from PIL import Image

from app.api.common import captcha_controller as captcha_controller_module
from app.api.common.captcha_controller import get_code, reset_captcha_controller
from app.common.constant.constants import (
    CAPTCHA_CODE_KEY,
    CAPTCHA_EXPIRATION,
    LOGIN_FAIL,
    LOGIN_SUCCESS,
)
from app.common.core.context import request_context
from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.redis.redis_cache import RedisCache
from app.common.exception.exceptions import CustomException
from app.common.exception.user import (
    CaptchaException,
    CaptchaExpireException,
    UserPasswordNotMatchException,
)
from app.framework.config.captcha_config import (
    get_captcha_producer,
    get_captcha_producer_math,
    reset_captcha_producers,
)
from app.framework.config.kaptcha_text_creator import (
    CNUMBERS,
    KaptchaTextCreator,
    DefaultTextCreator,
)
from app.framework.manager.async_manager import AsyncManager
from app.framework.manager.factory import async_factory as async_factory_module
from app.framework.security.authentication.dao_authentication_provider import (
    BAD_CREDENTIALS,
    DaoAuthenticationProvider,
)
from app.framework.security.authentication.exceptions import (
    BadCredentialsException,
    InternalAuthenticationServiceException,
    ProviderNotFoundException,
    UsernameNotFoundException,
)
from app.framework.security.authentication.provider_manager import (
    ProviderManager,
    get_authentication_manager,
    reset_authentication_manager,
)
from app.framework.security.context.security_context import (
    AnonymousAuthenticationToken,
    UsernamePasswordAuthenticationToken,
)
from app.framework.security.crypto.bcrypt_password_encoder import BCryptPasswordEncoder
from app.framework.web.service import token_service as token_service_module
from app.framework.web.service.sys_login_service import SysLoginService, reset_login_service
from app.framework.web.service.sys_permission_service import SysPermissionService
from app.framework.web.service.token_service import TokenService, reset_token_service
from app.framework.web.service.user_details_service_impl import UserDetailsServiceImpl
from app.system.domain.sys_logininfor import SysLogininfor
from app.system.service.sys_menu_service import SysMenuService
from app.system.service.sys_role_service import SysRoleService

WINDOWS_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

#: ``BCryptPasswordEncoder`` at strength 10 costs ~60 ms per call, so the hash is computed
#: once per session instead of once per test.
_RAW_PASSWORD = "admin123"
_PASSWORD_HASH: Optional[str] = None


def _password_hash() -> str:
    global _PASSWORD_HASH
    if _PASSWORD_HASH is None:
        _PASSWORD_HASH = BCryptPasswordEncoder().encode(_RAW_PASSWORD)
    return _PASSWORD_HASH


# --------------------------------------------------------------------------- fakes


class FakeRedis:
    """Minimal ``redis.Redis`` stand-in (same shape as in ``test_security_filter``)."""

    def __init__(self) -> None:
        self.store: Dict[str, Any] = {}
        self.ttls: Dict[str, Optional[int]] = {}

    def set(self, key: str, value: Any, px: Optional[int] = None, nx: bool = False) -> Optional[bool]:
        if nx and key in self.store:
            return None
        self.store[key] = value
        self.ttls[key] = px
        return True

    def get(self, key: str) -> Any:
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

    def ttl(self, key: str) -> int:
        if key not in self.store:
            return -2
        px = self.ttls.get(key)
        return -1 if px is None else px // 1000


class _RecordingLogininforService:
    """Collects the rows ``AsyncFactory.record_logininfor`` would have inserted."""

    def __init__(self, rows: List[SysLogininfor]) -> None:
        self._rows = rows

    def insert_logininfor(self, logininfor: SysLogininfor) -> int:
        self._rows.append(logininfor)
        return 1


class _StubUserService:
    """``ISysUserService.selectUserByUserName`` returning a fixed row."""

    def __init__(self, user: Optional[SysUser]) -> None:
        self._user = user
        self.calls: List[str] = []

    def select_user_by_user_name(self, user_name: str) -> Optional[SysUser]:
        self.calls.append(user_name)
        return self._user


class _StubRoleService:
    def __init__(self, role_keys: Optional[Set[str]] = None) -> None:
        self._role_keys = role_keys if role_keys is not None else set()
        self.calls: List[int] = []

    def select_role_permission_by_user_id(self, user_id: int) -> Set[str]:
        self.calls.append(user_id)
        return self._role_keys


class _StubMenuService:
    def __init__(self, perms: Optional[Set[str]] = None) -> None:
        self._perms = perms if perms is not None else set()
        self.calls: List[int] = []

    def select_menu_perms_by_user_id(self, user_id: int) -> Set[str]:
        self.calls.append(user_id)
        return self._perms


def make_request(
    path: str = "/login",
    headers: Optional[Dict[str, str]] = None,
) -> Request:
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
        "path": path,
        "root_path": "",
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 54321),
        "server": ("testserver", 80),
    }
    return Request(scope)


def make_user(
    user_id: int = 2,
    user_name: str = "ry",
    status: str = "0",
    del_flag: str = "0",
    password: Optional[str] = None,
) -> SysUser:
    return SysUser(
        user_id=user_id,
        user_name=user_name,
        nick_name=user_name,
        status=status,
        del_flag=del_flag,
        password=password if password is not None else _password_hash(),
    )


# --------------------------------------------------------------------------- fixtures


@pytest.fixture()
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    """Point every lazily-resolved ``RedisCache`` at a dict, then rebuild the singletons."""
    fake = FakeRedis()
    cache = RedisCache(client=fake)  # type: ignore[arg-type]
    monkeypatch.setattr(token_service_module, "get_redis_cache", lambda: cache)
    monkeypatch.setattr(captcha_controller_module, "_redis_cache", lambda: cache)
    reset_token_service()
    reset_login_service()
    reset_authentication_manager()
    reset_captcha_controller()
    reset_captcha_producers()
    yield fake
    reset_token_service()
    reset_login_service()
    reset_authentication_manager()
    reset_captcha_controller()
    reset_captcha_producers()


@pytest.fixture()
def audit_rows(monkeypatch: pytest.MonkeyPatch) -> List[SysLogininfor]:
    """Capture audit rows and run the "async" task inline."""
    rows: List[SysLogininfor] = []
    monkeypatch.setattr(
        async_factory_module, "get_logininfor_service", lambda: _RecordingLogininforService(rows)
    )
    monkeypatch.setattr(AsyncManager, "execute", lambda self, task: task())
    return rows


@pytest.fixture()
def bound_request() -> Any:
    """Bind a request so ``TokenService.setUserAgent`` / ``AsyncFactory`` have one."""
    request_context.set_request(make_request(headers={"User-Agent": WINDOWS_CHROME_UA}))
    yield
    request_context.clear_request()


# --------------------------------------------------------------------------- KaptchaTextCreator


class TestKaptchaTextCreator:
    """``KaptchaTextCreator`` -- the ``"a+b=?@c"`` format the controller splits on ``@``."""

    def test_the_answer_follows_the_last_at_sign(self) -> None:
        text = KaptchaTextCreator().get_text()
        assert text.count("@") == 1
        expression, answer = text.rsplit("@", 1)
        assert expression.endswith("=?")
        assert answer.lstrip("-").isdigit()

    def test_the_expression_is_arithmetically_correct(self) -> None:
        creator = KaptchaTextCreator()
        for _ in range(200):
            expression, answer = creator.get_text().rsplit("@", 1)
            assert _evaluate(expression[:-2]) == int(answer)  # strip "=?"

    def test_multiplication_branch_uses_a_star(self) -> None:
        creator = KaptchaTextCreator()
        # nextInt(3) == 0 -> multiplication; x=2, y=7
        assert creator.get_text(_sequence_random([2, 7, 0])) == "2*7=?@14"

    def test_division_branch_is_exact(self) -> None:
        creator = KaptchaTextCreator()
        # x=5, y=10, operands=1 -> 10 % 5 == 0 -> "10/5"
        assert creator.get_text(_sequence_random([5, 10, 1])) == "10/5=?@2"

    def test_division_falls_back_to_addition_when_not_exact(self) -> None:
        creator = KaptchaTextCreator()
        # x=3, y=10 -> 10 % 3 != 0 -> "3+10"
        assert creator.get_text(_sequence_random([3, 10, 1])) == "3+10=?@13"

    def test_division_by_zero_falls_back_to_addition(self) -> None:
        creator = KaptchaTextCreator()
        # x=0 would make ``y % x`` raise; the guard must fire first.
        assert creator.get_text(_sequence_random([0, 4, 1])) == "0+4=?@4"

    def test_subtraction_swaps_operands_to_stay_non_negative(self) -> None:
        creator = KaptchaTextCreator()
        assert creator.get_text(_sequence_random([2, 9, 2])) == "9-2=?@7"
        assert creator.get_text(_sequence_random([9, 2, 2])) == "9-2=?@7"

    def test_the_operands_never_reach_the_tenth_element(self) -> None:
        """``nextInt(10)`` yields 0..9, so ``CNUMBERS[10] == "10"`` is unreachable."""
        assert len(CNUMBERS) == 11
        seen: Set[str] = set()
        creator = KaptchaTextCreator()
        for _ in range(500):
            expression = creator.get_text().rsplit("@", 1)[0][:-2]
            seen.update(expression.replace("*", " ").replace("/", " ").replace("+", " ").replace("-", " ").split())
        assert "10" not in seen


class TestDefaultTextCreator:
    """The ``char`` producer's text source -- 4 characters from kaptcha's alphabet."""

    def test_four_characters_from_the_configured_alphabet(self) -> None:
        creator = DefaultTextCreator(char_length=4)
        text = creator.get_text()
        assert len(text) == 4
        assert set(text) <= set(creator.char_string)


def _evaluate(expression: str) -> int:
    """Evaluate ``"a op b"`` for op in ``* / + -`` -- no ``eval`` in a test."""
    for operator in "*/+-":
        if operator in expression:
            left, right = expression.split(operator, 1)
            a, b = int(left), int(right)
            if operator == "*":
                return a * b
            if operator == "/":
                return a // b
            if operator == "+":
                return a + b
            return a - b
    raise AssertionError(f"no operator in {expression!r}")


def _sequence_random(values: List[int]) -> random.Random:
    """A ``random.Random`` whose ``randrange`` replays ``values`` in order.

    ``KaptchaTextCreator`` calls ``randrange`` three times (x, y, operator), so a fixed
    sequence makes each branch reachable without touching the generator itself.
    """
    rng = random.Random(0)
    queue = list(values)
    rng.randrange = lambda _stop, _queue=queue: _queue.pop(0)  # type: ignore[method-assign]
    return rng


# --------------------------------------------------------------------------- SysPermissionService


class TestSysPermissionService:
    """``SysPermissionService`` -- the ``admin`` shortcut and its two magic strings."""

    def test_admin_gets_the_admin_role_without_querying(self) -> None:
        roles = _StubRoleService({"should-not-be-used"})
        service = SysPermissionService(role_service=roles, menu_service=_StubMenuService())

        assert service.get_role_permission(make_user(user_id=1, user_name="admin")) == {"admin"}
        assert roles.calls == []

    def test_admin_gets_the_star_permission_without_querying(self) -> None:
        menus = _StubMenuService({"should-not-be-used"})
        service = SysPermissionService(role_service=_StubRoleService(), menu_service=menus)

        assert service.get_menu_permission(make_user(user_id=1, user_name="admin")) == {"*:*:*"}
        assert menus.calls == []

    def test_a_regular_user_delegates_to_the_role_service(self) -> None:
        roles = _StubRoleService({"common", "auditor"})
        service = SysPermissionService(role_service=roles, menu_service=_StubMenuService())

        assert service.get_role_permission(make_user(user_id=2)) == {"common", "auditor"}
        assert roles.calls == [2]

    def test_a_regular_user_delegates_to_the_menu_service(self) -> None:
        menus = _StubMenuService({"system:user:list", "system:user:edit"})
        service = SysPermissionService(role_service=_StubRoleService(), menu_service=menus)

        assert service.get_menu_permission(make_user(user_id=2)) == {
            "system:user:list",
            "system:user:edit",
        }
        assert menus.calls == [2]

    def test_a_user_without_roles_gets_an_empty_set_not_an_error(self) -> None:
        service = SysPermissionService(role_service=_StubRoleService(), menu_service=_StubMenuService())

        assert service.get_role_permission(make_user(user_id=2)) == set()
        assert service.get_menu_permission(make_user(user_id=2)) == set()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("system:user:list", {"system:user:list"}),
        ("system:user:list,system:user:edit", {"system:user:list", "system:user:edit"}),
        # ``trim()`` then ``split(",")``: the parts are **not** trimmed individually.
        ("  a,b  ", {"a", "b"}),
        ("a,,b", {"a", "", "b"}),
    ],
)
def test_menu_perms_are_trimmed_then_split(raw: str, expected: Set[str]) -> None:
    """``SysMenuServiceImpl.selectMenuPermsByUserId`` -- ``perm.trim().split(",")``."""
    service = SysMenuService(mapper=_MenuRowMapper([raw]))
    assert service.select_menu_perms_by_user_id(7) == expected


def test_blank_menu_perms_are_dropped() -> None:
    """``StringUtils.isNotEmpty`` trims first, so ``"   "`` never reaches ``split``."""
    service = SysMenuService(mapper=_MenuRowMapper(["   ", ""]))
    assert service.select_menu_perms_by_user_id(7) == set()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("admin", {"admin"}),
        ("common,auditor", {"common", "auditor"}),
    ],
)
def test_role_keys_are_trimmed_then_split(raw: str, expected: Set[str]) -> None:
    """``SysRoleServiceImpl.selectRolePermissionByUserId``."""
    service = SysRoleService(mapper=_RoleRowMapper([raw]))
    assert service.select_role_permission_by_user_id(7) == expected


class _MenuRowMapper:
    def __init__(self, rows: List[Optional[str]]) -> None:
        self._rows = rows

    def select_menu_perms_by_user_id(self, _user_id: int) -> List[Optional[str]]:
        return self._rows


class _RoleRowMapper:
    def __init__(self, role_keys: List[str]) -> None:
        self._rows = [SysRole(role_id=9, role_key=key) for key in role_keys]

    def select_role_permission_by_user_id(self, _user_id: int) -> List[SysRole]:
        return self._rows


# --------------------------------------------------------------------------- UserDetailsServiceImpl


class TestUserDetailsService:
    """``UserDetailsServiceImpl`` -- three branches, two exception types."""

    def test_an_unknown_user_raises_username_not_found_with_the_java_message(self) -> None:
        service = UserDetailsServiceImpl(
            user_service=_StubUserService(None),
            permission_service=SysPermissionService(_StubRoleService(), _StubMenuService()),
        )
        with pytest.raises(UsernameNotFoundException) as caught:
            service.load_user_by_username("ghost")
        assert str(caught.value) == "登录用户：ghost 不存在"

    def test_a_deleted_account_is_rejected_before_its_status_is_checked(self) -> None:
        """``del_flag == "2"`` wins over ``status == "1"`` -- the branches are ordered."""
        user = make_user(user_name="gone", status="1", del_flag="2")
        service = UserDetailsServiceImpl(
            user_service=_StubUserService(user),
            permission_service=SysPermissionService(_StubRoleService(), _StubMenuService()),
        )
        with pytest.raises(Exception) as caught:
            service.load_user_by_username("gone")
        assert str(caught.value) == "对不起，您的账号：gone 已被删除"

    def test_a_disabled_account_is_rejected(self) -> None:
        user = make_user(user_name="frozen", status="1")
        service = UserDetailsServiceImpl(
            user_service=_StubUserService(user),
            permission_service=SysPermissionService(_StubRoleService(), _StubMenuService()),
        )
        with pytest.raises(Exception) as caught:
            service.load_user_by_username("frozen")
        assert str(caught.value) == "对不起，您的账号：frozen 已停用"

    def test_a_valid_account_becomes_a_login_user_with_menu_permissions(self) -> None:
        user = make_user(user_name="ry")
        service = UserDetailsServiceImpl(
            user_service=_StubUserService(user),
            permission_service=SysPermissionService(
                _StubRoleService(), _StubMenuService({"system:user:list"})
            ),
        )
        login_user = service.load_user_by_username("ry")

        assert login_user.user is user
        assert login_user.permissions == {"system:user:list"}
        # ``createLoginUser`` does **not** pass roles -- ``LoginUser`` has no such field.
        assert not hasattr(login_user, "roles")
        assert login_user.token is None  # set later by ``TokenService.createToken``

    def test_the_lookup_uses_the_name_verbatim(self) -> None:
        stub = _StubUserService(make_user())
        service = UserDetailsServiceImpl(
            user_service=stub,
            permission_service=SysPermissionService(_StubRoleService(), _StubMenuService()),
        )
        service.load_user_by_username("  Ry  ")
        assert stub.calls == ["  Ry  "]


# --------------------------------------------------------------------------- DaoAuthenticationProvider


def _provider_with(user: Optional[SysUser]) -> DaoAuthenticationProvider:
    return DaoAuthenticationProvider(user_details_service=UserDetailsServiceImpl(
        user_service=_StubUserService(user),
        permission_service=SysPermissionService(_StubRoleService(), _StubMenuService()),
    ))


class TestDaoAuthenticationProvider:
    """``DaoAuthenticationProvider`` -- where a login failure acquires its type."""

    def test_it_supports_the_username_password_token_only(self) -> None:
        provider = _provider_with(None)
        assert provider.supports(UsernamePasswordAuthenticationToken)
        assert not provider.supports(AnonymousAuthenticationToken)

    def test_an_unknown_user_is_reported_as_bad_credentials(self) -> None:
        """``hideUserNotFoundExceptions`` must not leak "no such account"."""
        with pytest.raises(BadCredentialsException) as caught:
            _provider_with(None).authenticate(
                UsernamePasswordAuthenticationToken("ghost", "whatever")
            )
        assert str(caught.value) == BAD_CREDENTIALS

    def test_a_wrong_password_is_reported_as_bad_credentials(self) -> None:
        with pytest.raises(BadCredentialsException):
            _provider_with(make_user()).authenticate(
                UsernamePasswordAuthenticationToken("ry", "wrong-password")
            )

    def test_a_disabled_account_surfaces_as_an_internal_failure_with_its_message(self) -> None:
        with pytest.raises(InternalAuthenticationServiceException) as caught:
            _provider_with(make_user(user_name="frozen", status="1")).authenticate(
                UsernamePasswordAuthenticationToken("frozen", _RAW_PASSWORD)
            )
        assert str(caught.value) == "对不起，您的账号：frozen 已停用"

    def test_a_deleted_account_surfaces_as_an_internal_failure_with_its_message(self) -> None:
        with pytest.raises(InternalAuthenticationServiceException) as caught:
            _provider_with(make_user(user_name="gone", del_flag="2")).authenticate(
                UsernamePasswordAuthenticationToken("gone", _RAW_PASSWORD)
            )
        assert str(caught.value) == "对不起，您的账号：gone 已被删除"

    def test_a_null_password_never_reaches_bcrypt(self) -> None:
        with pytest.raises(BadCredentialsException) as caught:
            _provider_with(make_user()).authenticate(
                UsernamePasswordAuthenticationToken("ry", None)
            )
        assert str(caught.value) == "Credentials cannot be null"

    def test_success_returns_an_authenticated_token_holding_the_login_user(self) -> None:
        result = _provider_with(make_user(user_name="ry")).authenticate(
            UsernamePasswordAuthenticationToken("ry", _RAW_PASSWORD)
        )
        assert result.is_authenticated()
        assert isinstance(result.get_principal(), LoginUser)
        assert result.get_principal().user.user_name == "ry"


class TestProviderManager:
    """``ProviderManager`` -- the one ``AuthenticationManager`` bean."""

    def test_it_delegates_to_the_matching_provider_and_erases_credentials(self) -> None:
        manager = ProviderManager([_provider_with(make_user(user_name="ry"))])
        result = manager.authenticate(UsernamePasswordAuthenticationToken("ry", _RAW_PASSWORD))

        assert result.is_authenticated()
        # ``eraseCredentialsAfterAuthentication`` defaults to true -> no plaintext survives.
        assert result.get_credentials() is None

    def test_erasing_can_be_switched_off(self) -> None:
        manager = ProviderManager(
            [_provider_with(make_user(user_name="ry"))],
            erase_credentials_after_authentication=False,
        )
        result = manager.authenticate(UsernamePasswordAuthenticationToken("ry", _RAW_PASSWORD))
        assert result.get_credentials() == _RAW_PASSWORD

    def test_an_unsupported_token_type_raises_provider_not_found(self) -> None:
        manager = ProviderManager([_provider_with(make_user())])
        with pytest.raises(ProviderNotFoundException):
            manager.authenticate(AnonymousAuthenticationToken())

    def test_the_bean_is_a_singleton(self) -> None:
        manager = get_authentication_manager()
        assert manager is get_authentication_manager()
        assert isinstance(manager, ProviderManager)


# --------------------------------------------------------------------------- SysLoginService


def _login_service(user: Optional[SysUser], fake_redis: FakeRedis) -> SysLoginService:
    return SysLoginService(
        token_service=TokenService(redis_cache=RedisCache(client=fake_redis)),  # type: ignore[arg-type]
        authentication_manager=ProviderManager([_provider_with(user)]),
        redis_cache=RedisCache(client=fake_redis),  # type: ignore[arg-type]
    )


class TestLoginCaptcha:
    """The captcha block -- optional, single-use, case-insensitive."""

    def test_a_blank_code_skips_verification_entirely(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        """``isNotBlank(code)`` is false -> no Redis read, no audit row, login proceeds."""
        token = _login_service(make_user(user_name="ry"), fake_redis).login("ry", _RAW_PASSWORD, code="")

        assert token
        assert [row for row in audit_rows if row.status == "1"] == []

    def test_a_whitespace_only_code_counts_as_absent(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        token = _login_service(make_user(user_name="ry"), fake_redis).login("ry", _RAW_PASSWORD, code="   ")
        assert token

    def test_an_expired_code_raises_captcha_expire(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        with pytest.raises(CaptchaExpireException):
            _login_service(make_user(), fake_redis).login("ry", _RAW_PASSWORD, "1234", "uuid-1")

        assert audit_rows[-1].status == "1"
        assert audit_rows[-1].msg == "验证码已失效"

    def test_a_wrong_code_raises_captcha_error(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        fake_redis.store[CAPTCHA_CODE_KEY + "uuid-1"] = '"15"'

        with pytest.raises(CaptchaException):
            _login_service(make_user(), fake_redis).login("ry", _RAW_PASSWORD, "99", "uuid-1")

        assert audit_rows[-1].msg == "验证码错误"

    def test_the_code_is_consumed_even_when_it_does_not_match(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        fake_redis.store[CAPTCHA_CODE_KEY + "uuid-1"] = '"15"'

        with pytest.raises(CaptchaException):
            _login_service(make_user(), fake_redis).login("ry", _RAW_PASSWORD, "99", "uuid-1")

        assert CAPTCHA_CODE_KEY + "uuid-1" not in fake_redis.store

    def test_the_code_comparison_ignores_case(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        """``String.equalsIgnoreCase`` -- the ``char`` producer emits letters."""
        fake_redis.store[CAPTCHA_CODE_KEY + "uuid-1"] = '"AbCd"'

        token = _login_service(make_user(user_name="ry"), fake_redis).login(
            "ry", _RAW_PASSWORD, "abcd", "uuid-1"
        )

        assert token

    def test_a_correct_code_is_consumed_too(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        fake_redis.store[CAPTCHA_CODE_KEY + "uuid-1"] = '"15"'

        _login_service(make_user(user_name="ry"), fake_redis).login("ry", _RAW_PASSWORD, "15", "uuid-1")

        assert CAPTCHA_CODE_KEY + "uuid-1" not in fake_redis.store

    def test_a_null_uuid_produces_the_literal_null_key(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        """Java's ``"..." + null`` yields ``"null"``, so the key can never exist."""
        with pytest.raises(CaptchaExpireException):
            _login_service(make_user(), fake_redis).login("ry", _RAW_PASSWORD, "15", None)

        assert audit_rows[-1].msg == "验证码已失效"


class TestLoginAuthentication:
    """Everything after the captcha -- who gets a token and what the failures say."""

    def test_a_wrong_password_answers_user_password_not_match(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        with pytest.raises(UserPasswordNotMatchException) as caught:
            _login_service(make_user(), fake_redis).login("ry", "wrong-password")

        assert str(caught.value) == "用户不存在/密码错误"
        assert audit_rows[-1].status == "1"
        assert audit_rows[-1].msg == "用户不存在/密码错误"

    def test_an_unknown_user_answers_the_same_message_as_a_wrong_password(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        with pytest.raises(UserPasswordNotMatchException):
            _login_service(None, fake_redis).login("ghost", "whatever")

        assert audit_rows[-1].msg == "用户不存在/密码错误"

    def test_a_disabled_account_answers_the_wrapped_sentence(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        """The ``else`` branch -- ``CustomException(e.getMessage())``, not a user exception."""
        with pytest.raises(CustomException) as caught:
            _login_service(make_user(user_name="frozen", status="1"), fake_redis).login(
                "frozen", _RAW_PASSWORD
            )

        assert str(caught.value) == "对不起，您的账号：frozen 已停用"
        assert audit_rows[-1].msg == "对不起，您的账号：frozen 已停用"

    def test_a_deleted_account_answers_the_wrapped_sentence(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        with pytest.raises(CustomException) as caught:
            _login_service(make_user(user_name="gone", del_flag="2"), fake_redis).login(
                "gone", _RAW_PASSWORD
            )

        assert str(caught.value) == "对不起，您的账号：gone 已被删除"

    def test_success_returns_a_jwt_and_caches_the_login_user(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        token = _login_service(make_user(user_name="ry"), fake_redis).login("ry", _RAW_PASSWORD)

        assert isinstance(token, str) and token.count(".") == 2
        assert len(fake_redis.store) == 1
        cache_key = next(iter(fake_redis.store))
        assert cache_key.startswith("login_tokens:")
        # token.expireTime = 120 minutes, expressed as a Redis PX value.
        assert fake_redis.ttls[cache_key] == 120 * 60 * 1000

    def test_success_writes_a_success_audit_row(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        _login_service(make_user(user_name="ry"), fake_redis).login("ry", _RAW_PASSWORD)

        assert audit_rows[-1].status == "0"
        assert audit_rows[-1].msg == "登录成功"
        assert audit_rows[-1].user_name == "ry"
        assert audit_rows[-1].browser  # parsed from the bound request's User-Agent

    def test_the_audit_row_for_a_failure_is_marked_failed(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        with pytest.raises(UserPasswordNotMatchException):
            _login_service(make_user(), fake_redis).login("ry", "nope")

        assert audit_rows[-1].status == "1"

    def test_the_issued_token_carries_the_login_user_key_claim(
        self, fake_redis: FakeRedis, audit_rows: List[SysLogininfor], bound_request: None
    ) -> None:
        service = _login_service(make_user(user_name="ry"), fake_redis)
        token = service.login("ry", _RAW_PASSWORD)

        claims = service.token_service.parse_token(token)
        assert list(claims.keys()) == ["login_user_key"]
        # The claim is the Redis key suffix, i.e. the row created above.
        assert "login_tokens:" + claims["login_user_key"] in fake_redis.store


def test_login_audit_status_constants_match_the_java_values() -> None:
    """``Constants.LOGIN_SUCCESS`` / ``LOGIN_FAIL`` are project-specific spellings."""
    assert LOGIN_SUCCESS == "Success"
    assert LOGIN_FAIL == "Error"


# --------------------------------------------------------------------------- CaptchaController


class TestCaptchaController:
    """``GET /captchaImage`` -- what the client receives before it has a token."""

    def test_the_response_carries_uuid_and_a_base64_jpeg(self, fake_redis: FakeRedis) -> None:
        result = get_code()

        assert result["code"] == 200
        assert len(result["uuid"]) == 32 and "-" not in result["uuid"]
        raw = base64.b64decode(result["img"])
        assert raw[:2] == b"\xff\xd8"  # JPEG SOI marker
        image = Image.open(io.BytesIO(raw))
        assert image.size == (160, 60)

    def test_the_answer_is_stored_for_two_minutes(self, fake_redis: FakeRedis) -> None:
        result = get_code()

        key = CAPTCHA_CODE_KEY + result["uuid"]
        assert key in fake_redis.store
        assert fake_redis.ttls[key] == CAPTCHA_EXPIRATION * 60 * 1000

    def test_the_math_answer_is_the_number_not_the_expression(self, fake_redis: FakeRedis) -> None:
        result = get_code()

        stored = fake_redis.store[CAPTCHA_CODE_KEY + result["uuid"]]
        assert stored.lstrip('"').rstrip('"').lstrip("-").isdigit()

    def test_the_generated_expression_holds_no_at_sign_after_the_split(
        self, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``createImage`` must receive ``"a+b=?"``; the answer stays in Redis."""
        captured: List[str] = []
        producer = get_captcha_producer_math()
        original = producer.create_image

        def spy(text: str) -> Any:
            captured.append(text)
            return original(text)

        monkeypatch.setattr(producer, "create_image", spy)
        get_code()

        assert captured and captured[0].endswith("=?")
        assert "@" not in captured[0]

    def test_the_math_producer_uses_the_configured_colours(self) -> None:
        config = get_captcha_producer_math().config
        assert (config.image_width, config.image_height) == (160, 60)
        assert config.border_color == (105, 179, 90)
        assert config.text_font_color == (0, 0, 255)
        assert config.text_font_size == 35
        assert config.noise_enabled is False  # KAPTCHA_NOISE_IMPL = NoNoise

    def test_the_char_producer_config_differs_as_in_java(self) -> None:
        config = get_captcha_producer().config
        assert config.image_width == 160 and config.image_height == 60
        assert config.text_font_size == 38
        assert config.border_color == (0, 0, 0)
        assert config.noise_enabled is True

    def test_switching_the_type_to_char_stores_the_letters_verbatim(
        self, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            captcha_controller_module,
            "get_settings",
            lambda: SimpleNamespace(ruoyi=SimpleNamespace(captcha_type="char")),
        )

        result = get_code()

        stored = fake_redis.store[CAPTCHA_CODE_KEY + result["uuid"]]
        assert len(stored.strip('"')) == 4

    def test_an_unknown_type_stores_a_null_answer(
        self, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A misconfigured ``captchaType`` writes ``null`` -- Java does the same, then 500s."""
        monkeypatch.setattr(
            captcha_controller_module,
            "get_settings",
            lambda: SimpleNamespace(ruoyi=SimpleNamespace(captcha_type="neither")),
        )

        with pytest.raises(Exception):
            get_code()

    def test_the_route_is_reachable_without_a_token(
        self, client: Any, fake_redis: FakeRedis
    ) -> None:
        """End-to-end through the security middleware: ``permitAll`` really is open."""
        response = client.get("/captchaImage")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["msg"] == "操作成功"
        assert CAPTCHA_CODE_KEY + body["uuid"] in fake_redis.store
        # Java: ``AjaxResult extends HashMap`` —— 键序是桶序 msg(0) -> img(2)
        # -> code(3) -> uuid(13)，不是 ``put`` 的先后。这里走完整序列化链路。
        assert list(body) == ["msg", "img", "code", "uuid"]
