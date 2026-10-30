"""token过滤器 验证token有效性 / resolve the token into a SecurityContext authentication.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/security/filter/JwtAuthenticationTokenFilter.java

Java original
-------------
An ``OncePerRequestFilter`` inserted *before* ``UsernamePasswordAuthenticationFilter``::

    LoginUser loginUser = tokenService.getLoginUser(request);
    if (StringUtils.isNotNull(loginUser) && StringUtils.isNull(SecurityUtils.getAuthentication())) {
        tokenService.verifyToken(loginUser);
        UsernamePasswordAuthenticationToken authenticationToken =
                new UsernamePasswordAuthenticationToken(loginUser, null, loginUser.getAuthorities());
        authenticationToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
        SecurityContextHolder.getContext().setAuthentication(authenticationToken);
    }
    chain.doFilter(request, response);

Four things this filter does **not** do, and each one is a behaviour:

* It never rejects a request. No token, expired Redis entry, revoked session -- all leave the
  context empty and let the request continue as anonymous. Rejecting is
  ``FilterSecurityInterceptor``'s job, which is why the 401 comes from the rule table and not
  from here.
* It never overwrites an existing authentication (``isNull(getAuthentication())``) -- the
  guard against an upstream filter having already authenticated the caller.
* It does **not** catch anything. ``getLoginUser`` -> ``parseToken`` throws on a malformed or
  badly signed JWT, and the exception escapes into the container (a filter is outside
  ``@ControllerAdvice``). The client still gets ``HTTP 200`` with ``code`` 401, but the body
  names ``/error`` instead of the requested path, because the container's ERROR dispatch to
  ``/error`` is itself denied by ``AuthenticationEntryPointImpl``. Do not wrap this in
  ``try``/``except``: catching it would report the *original* path and lose that difference.
* It does not run for ``/logout``: ``LogoutFilter`` sits earlier in the chain and returns
  without calling ``doFilter``.

``verifyToken`` is called on every authenticated request and slides the Redis TTL forward
when fewer than 20 minutes remain -- that is the only reason a session stays alive while the
user keeps working.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Request

from app.common.core.domain.model.login_user import LoginUser
from app.common.utils.security_utils import get_authentication
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.framework.web.service.token_service import TokenService, get_token_service


class WebAuthenticationDetails:
    """Spring: ``WebAuthenticationDetails``.

    Carries request metadata into ``Authentication.getDetails()``. Nothing in RuoYi reads it;
    it is modelled so the context object matches what a Java developer expects to find, and
    so a future ``@PreAuthorize`` expression using ``authentication.details`` has something to
    return.
    """

    __slots__ = ("remote_address", "session_id")

    def __init__(self, remote_address: Optional[str] = None, session_id: Optional[str] = None) -> None:
        #: Java: ``request.getRemoteAddr()``
        self.remote_address = remote_address
        #: Java: ``request.getSession(false)`` -- ``null`` under ``SessionCreationPolicy.STATELESS``,
        #: which is what this project configures, so the field is always ``None`` here.
        self.session_id = session_id

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"WebAuthenticationDetails(remote_address={self.remote_address!r})"


class WebAuthenticationDetailsSource:
    """Spring: ``WebAuthenticationDetailsSource``."""

    # Java: public WebAuthenticationDetails buildDetails(HttpServletRequest context)
    def build_details(self, request: Request) -> WebAuthenticationDetails:
        """Build the details; there is no session in a stateless chain."""
        client = getattr(request, "client", None)
        return WebAuthenticationDetails(remote_address=client.host if client is not None else None)


class JwtAuthenticationTokenFilter:
    """Java: ``@Component JwtAuthenticationTokenFilter extends OncePerRequestFilter``."""

    def __init__(self, token_service: Optional[TokenService] = None) -> None:
        self._token_service = token_service

    @property
    def token_service(self) -> TokenService:
        """Java: ``@Autowired private TokenService tokenService`` (resolved lazily)."""
        if self._token_service is None:
            self._token_service = get_token_service()
        return self._token_service

    # Java: protected void doFilterInternal(HttpServletRequest, HttpServletResponse, FilterChain)
    def do_filter_internal(self, request: Request) -> None:
        """Install the authentication for this request, if a token resolves to a session.

        Returns nothing, exactly like the Java method: the outcome is observable only through
        :class:`SecurityContextHolder`, which is also how ``FilterSecurityInterceptor`` reads
        it.
        """
        login_user: Optional[LoginUser] = self.token_service.get_login_user(request)
        if login_user is not None and get_authentication() is None:
            self.token_service.verify_token(login_user)
            # Java passes ``loginUser.getAuthorities()``, which is hard-coded ``null``. The
            # three-argument constructor still marks the token authenticated -- see
            # ``UsernamePasswordAuthenticationToken``.
            authentication_token = UsernamePasswordAuthenticationToken(
                login_user, None, login_user.authorities
            )
            authentication_token.set_details(WebAuthenticationDetailsSource().build_details(request))
            SecurityContextHolder.get_context().set_authentication(authentication_token)


_JWT_FILTER: Optional[JwtAuthenticationTokenFilter] = None


def get_jwt_authentication_token_filter() -> JwtAuthenticationTokenFilter:
    """Process-wide filter instance (Java: the ``@Component`` singleton)."""
    global _JWT_FILTER
    if _JWT_FILTER is None:
        _JWT_FILTER = JwtAuthenticationTokenFilter()
    return _JWT_FILTER


def reset_jwt_authentication_token_filter() -> None:
    """Test helper: drop the singleton so a fake ``TokenService`` can be injected."""
    global _JWT_FILTER
    _JWT_FILTER = None


__all__: list[str] = [
    "WebAuthenticationDetails",
    "WebAuthenticationDetailsSource",
    "JwtAuthenticationTokenFilter",
    "get_jwt_authentication_token_filter",
    "reset_jwt_authentication_token_filter",
]
