"""登录校验方法 / the login use case: captcha -> authentication -> JWT.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysLoginService.java

The whole method is one screen of Java, but four behaviours in it are easy to "clean up" and
break:

1. ``getCacheObject`` then ``deleteObject`` **then** compare.
   The captcha is consumed before the comparison, so a wrong code also burns it. A user who
   mistypes must click refresh -- matching ``captchaEnabled: true`` clients that fetch a new
   image on every failed attempt. Deleting only on success would allow unlimited guessing of a
   single 2-minute challenge.

2. The captcha is **optional**.
   ``if (CommonUtil.isNotBlank(code))`` -- when the client sends no ``code``, verification is
   skipped entirely, no Redis key is touched, and no ``sys_logininfor`` row is written. The
   check is driven by the *request*, not by ``ruoyi.captchaEnabled``: a client that omits the
   field bypasses the captcha even though ``GET /captchaImage`` still serves one. That is the
   Java behaviour and it is preserved.

3. ``BadCredentialsException`` and everything else answer differently.
   ====================================  =========================================
   provider threw                        ``sys_logininfor`` message / response
   ====================================  =========================================
   ``BadCredentialsException``           ``user.password.not.match`` -> ``用户不存在/密码错误``
   anything else (e.g. wrapped          ``e.getMessage()`` -> ``对不起，您的账号：xxx 已停用``
   ``BaseException`` for disabled)
   ====================================  =========================================
   Both end up as ``{"code":500,"msg":...}`` with HTTP 200, because RuoYi's
   ``GlobalExceptionHandler`` has no handler that maps ``UserException`` to 401 -- the
   *captcha* exceptions (``CaptchaExpireException``/``CaptchaException``) go through the very
   same ``RuntimeException`` fallback.

4. ``e.getMessage()`` is passed through **verbatim**, including ``null``.
   A ``NullPointerException`` reaching this branch logs the literal text ``null``; Python's
   ``str(ex)`` would produce ``""``. :func:`_exception_message` keeps the Java spelling.

What is *not* here
------------------
No password-retry counter, no lockout, no blacklist. ``UserPasswordRetryLimitExceedException``
and ``BlackListException`` exist in the codebase but nothing throws them, so the login path is
stateless apart from Redis.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.common.constant.constants import CAPTCHA_CODE_KEY, LOGIN_FAIL, LOGIN_SUCCESS
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.exception.exceptions import CustomException
from app.common.exception.user import (
    CaptchaException,
    CaptchaExpireException,
    UserPasswordNotMatchException,
)
from app.common.utils.message_utils import message
from app.common.utils.string_utils import is_not_blank
from app.framework.manager.async_manager import AsyncManager
from app.framework.manager.factory.async_factory import record_logininfor
from app.framework.security.authentication.authentication_manager import AuthenticationManager
from app.framework.security.authentication.exceptions import BadCredentialsException
from app.framework.security.authentication.provider_manager import get_authentication_manager
from app.framework.security.context.security_context import UsernamePasswordAuthenticationToken
from app.framework.web.service.token_service import TokenService, get_token_service

logger = logging.getLogger("app.framework.web.service.sys_login")


def _exception_message(ex: BaseException) -> Optional[str]:
    """Java: ``e.getMessage()`` -- ``null`` stays ``null``, never ``""``.

    A Python exception with no arguments stringifies to ``""``, which Java would report as
    ``null``. Both the audit row and the client message consume this value, so the distinction
    is preserved by inspecting ``args`` instead of trusting ``str()``::

        RuntimeError()        -> Java getMessage() == null  -> None
        RuntimeError(None)    -> Java getMessage() == null  -> None
        RuntimeError("")      -> Java getMessage() == ""    -> ""
    """
    if not ex.args or ex.args[0] is None:
        return None
    return str(ex)


class SysLoginService:
    """Java: ``@Component SysLoginService``."""

    def __init__(
        self,
        token_service: Optional[TokenService] = None,
        authentication_manager: Optional[AuthenticationManager] = None,
        redis_cache: Optional[RedisCache] = None,
    ) -> None:
        self._token_service = token_service
        self._authentication_manager = authentication_manager
        self._redis_cache = redis_cache

    # Java: @Autowired private TokenService tokenService
    @property
    def token_service(self) -> TokenService:
        if self._token_service is None:
            self._token_service = get_token_service()
        return self._token_service

    # Java: @Resource private AuthenticationManager authenticationManager
    @property
    def authentication_manager(self) -> AuthenticationManager:
        if self._authentication_manager is None:
            self._authentication_manager = get_authentication_manager()
        return self._authentication_manager

    # Java: @Autowired private RedisCache redisCache
    @property
    def redis_cache(self) -> RedisCache:
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    # Java: public String login(String username, String password, String code, String uuid)
    def login(
        self,
        username: str,
        password: str,
        code: Optional[str] = None,
        uuid: Optional[str] = None,
    ) -> str:
        """Validate the credentials and return the JWT.

        Raises (never returns ``None``) on failure -- the caller, ``SysLoginController``,
        does not branch on the result:
        ``CaptchaExpireException`` / ``CaptchaException`` / ``UserPasswordNotMatchException``
        / ``CustomException``.
        """
        self.validate_captcha(username, code, uuid)

        # 用户验证
        try:
            authentication = self.authentication_manager.authenticate(
                # Two-argument constructor -> authenticated = false (pre-authentication token).
                UsernamePasswordAuthenticationToken(username, password)
            )
        except Exception as ex:  # noqa: BLE001 - Java catches Exception and re-classifies it
            if isinstance(ex, BadCredentialsException):
                self._record(username, LOGIN_FAIL, message("user.password.not.match"))
                raise UserPasswordNotMatchException() from ex
            self._record(username, LOGIN_FAIL, _exception_message(ex))
            # Java discards the original exception type; the message is all that survives.
            raise CustomException(_exception_message(ex)) from ex

        self._record(username, LOGIN_SUCCESS, message("user.login.success"))
        login_user: LoginUser = authentication.get_principal()
        # 生成token
        return self.token_service.create_token(login_user)

    # Java: the ``if (CommonUtil.isNotBlank(code)) { ... }`` block
    def validate_captcha(
        self, username: str, code: Optional[str], uuid: Optional[str]
    ) -> None:
        """Verify and **consume** the captcha; no-op when ``code`` is blank.

        ``CommonUtil.isNotBlank`` delegates to ``StringUtils.isNotBlank``, i.e. ``None`` and
        whitespace-only are both "absent".
        """
        if not is_not_blank(code):
            return

        # Java concatenates unguarded: a null ``uuid`` yields the literal text "null", so
        # the key becomes ``captcha_codes:null`` -- a key that never exists, hence "expired".
        verify_key = CAPTCHA_CODE_KEY + (uuid if uuid is not None else "null")
        captcha = self.redis_cache.get_cache_object(verify_key)
        # Consumed on every attempt, matching or not -- see the module docstring.
        self.redis_cache.delete_object(verify_key)
        if captcha is None:
            self._record(username, LOGIN_FAIL, message("user.jcaptcha.expire"))
            raise CaptchaExpireException()
        # Java: !code.equalsIgnoreCase(captcha)
        if code.lower() != str(captcha).lower():
            self._record(username, LOGIN_FAIL, message("user.jcaptcha.error"))
            raise CaptchaException()

    # Java: AsyncManager.me().execute(AsyncFactory.recordLogininfor(...))
    @staticmethod
    def _record(username: Optional[str], status: str, text: Optional[str]) -> None:
        """Fire-and-forget audit write; a failed insert never fails the login."""
        AsyncManager.me().execute(record_logininfor(username, status, text))


_SERVICE: Optional[SysLoginService] = None


def get_login_service() -> SysLoginService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysLoginService()
    return _SERVICE


def reset_login_service() -> None:
    """Test helper: drop the singleton so fakes can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["SysLoginService", "get_login_service", "reset_login_service"]
