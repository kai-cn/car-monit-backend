"""token验证处理 / JWT issuing, parsing and the Redis-backed session record.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/TokenService.java

Mental model for a Java developer
---------------------------------
The JWT is **not** the session. It is a signed envelope whose only claim is
``login_user_key``, a random UUID. The real ``LoginUser`` lives in Redis under
``login_tokens:<uuid>`` with a TTL of ``token.expireTime`` minutes. Consequences that
must not be "optimised away":

* The token carries **no ``exp``, ``iat``, ``sub`` or authorities**. Revocation is done by
  deleting the Redis key (``delLoginUser``), which is why a stolen token dies the moment the
  user logs out. Moving the expiry into the JWT would remove that property.
* Logging out therefore requires a Redis round-trip, and every authenticated request is one
  ``GET`` (`getLoginUser`) plus -- when fewer than 20 minutes remain -- one ``SET`` that
  slides the window forward (`verifyToken` -> `refreshToken`).
* Two separate clocks: the JWT never expires, the Redis key does. A token whose Redis key
  has expired yields ``null`` (anonymous), **not** an error.

Secret handling -- the classic jjwt 0.9.x trap
----------------------------------------------
``signWith(SignatureAlgorithm.HS512, secret)`` takes a **String**, and jjwt 0.9.1 runs it
through ``TextCodec.BASE64`` before using it as key material. The configured secret
``abcdefghijklmnopqrstuvwxyz`` is therefore *not* 26 ASCII bytes: it decodes to **19 bytes**
(6 base64 quads = 18 bytes, plus the 2 leftover characters = 1 more byte). PyJWT is handed
those same 19 bytes, so a token minted by the Java build verifies here and vice versa. Using
``secret.encode()`` instead would produce a different key and rejected every existing token.
(Verified: PyJWT 2.10.1 accepts a 19-byte HS512 key without complaint.)

jjwt 0.9.1 does **not** validate ``aud``/``iss``/``iat`` unless the builder explicitly calls
``requireAudience``/``requireIssuer``; it only checks the signature plus ``exp``/``nbf``.
PyJWT 2.10 validates all of them by default, so those three checks are switched off below.

``getToken`` quirk
------------------
``token.replace(Constants.TOKEN_PREFIX, "")`` is ``String.replace``, i.e. **replace every
occurrence**, not ``replaceFirst``. A header value of ``"Bearer Bearer abc"`` becomes
``"abc"``. Python's ``str.replace`` has the same semantics; ``removeprefix`` would not.
"""

from __future__ import annotations

import base64
import binascii
import logging
import uuid
from typing import Any, Dict, Optional

import jwt
from starlette.requests import Request

from app.common.constant.constants import JWT_USERNAME, LOGIN_TOKEN_KEY, LOGIN_USER_KEY, TOKEN_PREFIX
from app.common.core.context.request_context import get_request
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.address_utils import get_real_address_by_ip
from app.common.utils.date_utils import current_time_millis
from app.common.utils.ip_utils import get_ip_addr
from app.common.utils.string_utils import is_not_empty
from app.common.utils.time_unit import TimeUnit
from app.common.utils.user_agent_utils import UNKNOWN_AGENT, browser_name, operating_system_name
from app.common.utils.uuid_utils import fast_uuid
from app.settings import get_settings

logger = logging.getLogger("app.framework.web.service.token")

# --------------------------------------------------------------------------- 常量
#: Java: ``TokenService.MILLIS_SECOND``
MILLIS_SECOND = 1000
#: Java: ``TokenService.MILLIS_MINUTE``
MILLIS_MINUTE = 60 * MILLIS_SECOND
#: Java: ``TokenService.MILLIS_MINUTE_TEN`` -- 20 minutes. The name says "ten", the value is
#: twenty; the constant is private and the literal is what the code uses, so the value wins.
MILLIS_MINUTE_TEN = 20 * 60 * 1000

#: Java: ``SignatureAlgorithm.HS512`` -> JCA name ``HmacSHA512``.
ALGORITHM = "HS512"

# ``UNKNOWN_AGENT`` is re-exported from ``app.common.utils.user_agent_utils``; the mapping
# lives there because ``AsyncFactory.recordLogininfor`` parses the same header.

#: Header read by ``setUserAgent``; case-insensitive in both servlet and ASGI land.
USER_AGENT_HEADER = "User-Agent"


class TokenService:
    """Java: ``@Component TokenService``.

    Spring injects ``RedisCache`` and three ``@Value`` properties. Here the properties come
    from :class:`app.settings.AppSettings` (same YAML keys) and the cache is injected through
    the constructor, defaulting to the process-wide singleton exactly like Symfony's
    default bean scope.
    """

    def __init__(self, redis_cache: Optional[RedisCache] = None) -> None:
        section = get_settings().token
        #: 令牌自定义标识 -- ``token.header`` in application.yml
        self.header: str = section.header
        #: 令牌秘钥 -- ``token.secret`` (base64, see the module docstring)
        self.secret: str = section.secret
        #: 令牌有效期（分钟） -- ``token.expireTime``, 120 in this project
        self.expire_time: int = section.expire_time
        self._redis_cache = redis_cache
        self._secret_key: Optional[bytes] = None

    # ------------------------------------------------------------------ dependencies

    @property
    def redis_cache(self) -> RedisCache:
        """Java: ``@Autowired private RedisCache redisCache`` (resolved lazily)."""
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    @property
    def secret_key(self) -> bytes:
        """The HMAC key, i.e. ``TextCodec.BASE64.decode(secret)``."""
        if self._secret_key is None:
            self._secret_key = _decode_secret(self.secret)
        return self._secret_key

    # ------------------------------------------------------------------ session cache

    def get_login_user(self, request: Request) -> Optional[LoginUser]:
        """Java: ``getLoginUser(HttpServletRequest)``.

        Returns ``None`` -- meaning "anonymous" -- when no token is present, when the token
        carries no ``login_user_key``, or when the Redis entry has expired. A **malformed or
        badly signed** token is *not* in that list: ``parseToken`` throws and the exception
        escapes the filter, which is why the caller must not wrap this in ``try``/``except``.
        What the client then sees is described on :meth:`parse_token`.
        """
        # 获取请求携带的令牌
        token = self._get_token(request)
        if is_not_empty(token):
            claims = self.parse_token(token)
            # 解析对应的权限以及用户信息
            user_key = self._get_token_key(_claim_uuid(claims))
            return self.redis_cache.get_cache_object(user_key)
        return None

    def set_login_user(self, login_user: Optional[LoginUser]) -> None:
        """Java: ``setLoginUser(LoginUser)`` -- re-cache after the profile was edited.

        Used by ``SysProfileController`` after changing nickname/sex/avatar/password. Note it
        refreshes the TTL as a side effect, so editing the profile extends the session.
        """
        if login_user is not None and is_not_empty(login_user.token):
            self.refresh_token(login_user)

    def del_login_user(self, token: Optional[str]) -> None:
        """Java: ``delLoginUser(String)`` -- the logout primitive."""
        if is_not_empty(token):
            self.redis_cache.delete_object(self._get_token_key(token))

    # ------------------------------------------------------------------ issuing

    def create_token(self, login_user: LoginUser) -> str:
        """Java: ``createToken(LoginUser)`` -- mint the UUID, cache the principal, sign."""
        # 生成token
        token = fast_uuid()
        login_user.token = token
        self.set_user_agent(login_user)
        self.refresh_token(login_user)

        claims: Dict[str, Any] = {LOGIN_USER_KEY: token}
        return self._create_token_with_claims(claims)

    def verify_token(self, login_user: LoginUser) -> None:
        """Java: ``verifyToken(LoginUser)`` -- slide the window when under 20 minutes remain.

        Called on every authenticated request by ``JwtAuthenticationTokenFilter``. Note the
        local variable shadows the ``expireTime`` *field* inside the Java method; only the
        ``LoginUser`` value participates in the comparison.
        """
        expire_time = login_user.expire_time
        current_time = current_time_millis()
        # Java: Long arithmetic on a possibly-null field -> NullPointerException. A cached
        # LoginUser always has it set (refreshToken writes both fields together), so a null
        # here means the Redis payload was hand-edited; letting the subtraction fail is the
        # closest equivalent to the NPE.
        if expire_time - current_time <= MILLIS_MINUTE_TEN:  # type: ignore[operator]
            self.refresh_token(login_user)

    def refresh_token(self, login_user: LoginUser) -> None:
        """Java: ``refreshToken(LoginUser)`` -- rewrite ``loginTime``/``expireTime`` and re-cache.

        The Redis TTL is ``expireTime`` **minutes**; ``expireTime`` on the bean is the same
        span expressed in epoch milliseconds. Both are recomputed from "now", which is what
        makes a session slide forward on activity.
        """
        login_time = current_time_millis()
        login_user.login_time = login_time
        login_user.expire_time = login_time + self.expire_time * MILLIS_MINUTE
        # 根据uuid将loginUser缓存
        user_key = self._get_token_key(login_user.token)
        self.redis_cache.set_cache_object_with_timeout(
            user_key, login_user, self.expire_time, TimeUnit.MINUTES
        )

    def set_user_agent(self, login_user: LoginUser) -> None:
        """Java: ``setUserAgent(LoginUser)`` -- stamp ip / location / browser / os / sessionId.

        Reaches for the current request through ``ServletUtils.getRequest()`` because Spring
        can inject nothing else into a service. Here the request comes from the context
        :mod:`app.common.core.context.request_context`; outside a request the Java code
        throws ``NullPointerException`` and so does this.
        """
        request = get_request()
        if request is None:
            # Java: request is null -> NPE on request.getHeader("User-Agent").
            raise RuntimeError(
                "setUserAgent requires a bound request (Java: NullPointerException in "
                "TokenService.setUserAgent)"
            )

        user_agent_string = request.headers.get(USER_AGENT_HEADER)
        ip = get_ip_addr(request)
        login_user.session_id = _current_session_id(request)
        login_user.ipaddr = ip
        login_user.login_location = get_real_address_by_ip(ip)
        login_user.browser = browser_name(user_agent_string)
        login_user.os = operating_system_name(user_agent_string)

    # ------------------------------------------------------------------ parsing

    def get_username_from_token(self, token: str) -> Optional[str]:
        """Java: ``getUsernameFromToken(String)``.

        Reads the ``sub`` claim. **Dead code in the Java project** (no caller), kept because
        the migration rule is "port it, do not delete it". RuoYi never puts a subject in the
        token, so this returns ``None`` for every token this service issues.
        """
        claims = self.parse_token(token)
        return claims.get(JWT_USERNAME)

    def parse_token(self, token: str) -> Dict[str, Any]:
        """Java: ``parseToken(String)`` -- ``Jwts.parser().setSigningKey(secret).parseClaimsJws``.

        Raises ``jwt.InvalidTokenError`` (signature mismatch, malformed string, wrong ``alg``)
        or ``jwt.ExpiredSignatureError``/``jwt.ImmatureSignatureError``. jjwt throws the
        unchecked ``JwtException`` family at the same points, and neither implementation
        catches it.

        The exception escaping the filter does **not** become an HTTP 500: the container
        answers it with an ERROR dispatch to ``/error``, that path is not in
        ``SecurityConfig``'s permit-all list, so the chain runs again (minus this filter,
        which ``OncePerRequestFilter`` skips on an error dispatch), the caller is anonymous,
        and ``AuthenticationEntryPointImpl`` answers ``HTTP 200`` with
        ``{"code":401,"msg":"请求访问：/error，认证失败，无法访问系统资源"}``. Verified
        against the running Java backend; ``/getInfo`` and ``/logout`` both behave this way.
        """
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[ALGORITHM],
            options={
                # jjwt 0.9.1 validates the signature and exp/nbf only; aud/iss/iat are
                # ignored unless the builder asked for them explicitly.
                "verify_aud": False,
                "verify_iss": False,
                "verify_iat": False,
            },
        )

    # ------------------------------------------------------------------ private

    def _create_token_with_claims(self, claims: Dict[str, Any]) -> str:
        """Java: ``private String createToken(Map<String, Object> claims)``.

        ``Jwts.builder().setClaims(claims).signWith(...)`` adds no timestamps, so the payload
        is exactly the claim map. PyJWT adds ``"typ":"JWT"`` to the header where jjwt emits
        only ``"alg":"HS512"``; both parsers ignore ``typ``, so the tokens interoperate.
        """
        return jwt.encode(claims, self.secret_key, algorithm=ALGORITHM)

    def _get_token(self, request: Request) -> Optional[str]:
        """Java: ``private String getToken(HttpServletRequest)``.

        ``request.getHeader`` is case-insensitive, as is Starlette's ``headers.get``.
        """
        token = request.headers.get(self.header)
        if is_not_empty(token) and token.startswith(TOKEN_PREFIX):
            token = token.replace(TOKEN_PREFIX, "")
        return token

    def _get_token_key(self, token: Optional[str]) -> str:
        """Java: ``private String getTokenKey(String uuid)``.

        Java concatenates ``Constants.LOGIN_TOKEN_KEY + uuid``; a null uuid therefore yields
        the literal key ``login_tokens:null`` rather than throwing. Kept so that a token
        without the claim behaves identically (miss in Redis -> anonymous).
        """
        return LOGIN_TOKEN_KEY + ("null" if token is None else token)


# --------------------------------------------------------------------------- helpers


def _decode_secret(secret: str) -> bytes:
    """Java: jjwt 0.9.1's ``TextCodec.BASE64.decode(base64EncodedSecretKey)``.

    jjwt 0.9.1 decodes **whole 4-character quanta only** and silently drops a trailing
    1-3 character remainder; it does not restore the missing ``=`` padding. Measured against
    the jar this project ships (``BOOT-INF/lib/jjwt-0.9.1.jar``, see ``COMPATIBILITY.md``
    §44.7): 26 chars -> 18 bytes, 27 -> 18, 19 -> 12, 2 -> 0.

    Padding the secret up to a multiple of four is the intuitive reading of "tolerates a
    missing pad", but it produces a **different HMAC key** than Java for any secret whose
    length is not a multiple of four -- 19 bytes instead of 18 for this project's
    26-character secret -- so tokens minted by one backend fail signature verification in
    the other. The truncation is the behaviour that has to be copied.
    """
    if not secret:
        # Java: Assert.hasText -> IllegalArgumentException("base64-encoded secret key cannot be null or empty.")
        raise ValueError("base64-encoded secret key cannot be null or empty.")
    chunk = secret[: len(secret) // 4 * 4]
    try:
        return base64.b64decode(chunk, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"Secret is not valid base64: {exc}") from exc


def _claim_uuid(claims: Dict[str, Any]) -> Optional[str]:
    """Java: ``(String) claims.get(Constants.LOGIN_USER_KEY)``.

    A missing claim stays ``None``; a claim of the wrong type throws ``ClassCastException``
    in Java, reproduced here as ``TypeError``.
    """
    value = claims.get(LOGIN_USER_KEY)
    if value is not None and not isinstance(value, str):
        raise TypeError(
            f"login_user_key must be a string, got {type(value).__name__} "
            "(Java: ClassCastException)"
        )
    return value


def _current_session_id(request: Request) -> str:
    """Java: ``request.getSession().getId()``.

    There is no server-side ``HttpSession`` in the Python port -- the session state lives in
    Redis, keyed by the token UUID. Tomcat lazily creates a session here and returns its
    id: **32 uppercase hex characters** (``SessionIdGenerator`` renders 16 random bytes as
    upper-case hex). The same shape is synthesised and memoised on ``request.state`` so two
    calls within one request return the same value, as ``getSession()`` does.

    Only ``LoginUser.sessionId`` consumes it; the ``monitor/online`` views identify sessions
    by ``tokenId`` (the UUID), never by this field. So the value is informational, but it is
    persisted and displayed, which is why the format is mirrored.
    """
    existing = getattr(request.state, "session_id", None)
    if existing is None:
        existing = uuid.uuid4().hex.upper()
        request.state.session_id = existing
    return existing


_TOKEN_SERVICE: Optional[TokenService] = None


def get_token_service() -> TokenService:
    """Process-wide ``TokenService`` (Spring's default singleton scope)."""
    global _TOKEN_SERVICE
    if _TOKEN_SERVICE is None:
        _TOKEN_SERVICE = TokenService()
    return _TOKEN_SERVICE


def reset_token_service() -> None:
    """Test helper: drop the singleton so settings/Redis fakes can be swapped in."""
    global _TOKEN_SERVICE
    _TOKEN_SERVICE = None


__all__ = [
    "MILLIS_SECOND",
    "MILLIS_MINUTE",
    "MILLIS_MINUTE_TEN",
    "ALGORITHM",
    "UNKNOWN_AGENT",
    "TokenService",
    "get_token_service",
    "reset_token_service",
]
