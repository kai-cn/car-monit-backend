"""The Spring Security filter chain, expressed as one ASGI middleware.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/SecurityConfig.java

Not a RuoYi file (the chain itself)
-----------------------------------
``SecurityConfig`` never writes a filter -- it declares a ``FilterChainProxy`` from builder
calls and Spring instantiates the chain. Python has no filter chain to configure, so the
ordering that Spring assembles implicitly is written out explicitly here, and this module is
the single place where "which answer does an unauthenticated request get" is decided.

The Java order, and which part of this module owns each step
------------------------------------------------------------
======  ===================================  ==========================================
step    Spring component                      Python
======  ===================================  ==========================================
1       ``CorsFilter`` (added before both       ``CORSMiddleware``, wired *outside* this
        ``LogoutFilter`` and the JWT filter)    middleware in ``app/main.py``
2       ``LogoutFilter``                        ``is_logout_request`` -> logout handler
3       ``JwtAuthenticationTokenFilter``        ``JwtAuthenticationTokenFilter``
4       ``AnonymousAuthenticationFilter``        the fallback below
5       ``ExceptionTranslationFilter`` +        ``resolve_access`` + the denial branch
        ``FilterSecurityInterceptor``
======  ===================================  ==========================================

Two ordering facts are load-bearing:

* **CORS runs first and can short-circuit.** ``CorsFilter`` answers a preflight ``OPTIONS``
  with 200 and returns without calling the chain, so a preflight never needs a token. The
  Python ``CORSMiddleware`` does the same, which is why it must be registered *outside* this
  middleware -- otherwise preflights would be rejected with 401 and every browser request
  would fail.
* **Logout runs before authentication.** ``POST /logout`` is answered by step 2, so it returns
  200 even without a token, and a token is never parsed for it.

Why an ASGI middleware (and not a FastAPI dependency)
-----------------------------------------------------
Java authorises *before* dispatching to a controller, so an unmapped path still answers
401 rather than 404. A FastAPI ``Depends`` runs after routing, which would produce 404 first
and change observable behaviour. A middleware sees the request before routing, exactly like
``FilterSecurityInterceptor``.

The blocking work (Redis ``GET``, JWT verification, the ``sys_logininfor`` insert) runs in a
worker thread so the event loop is not blocked, which is the counterpart of Tomcat's 800
request threads. The authentication resolved there is handed back to this coroutine and
installed in the context before the endpoint runs, because ``to_thread`` copies the context
inbound only.

Filter-phase exceptions
-----------------------
A servlet filter sits **outside** ``@ControllerAdvice``, so an exception thrown there never
reaches ``GlobalExceptionHandler``. What the client sees is nevertheless **not** a 500: the
container answers with an ERROR dispatch to ``/error``, that path is not in the permit-all
list, and ``AuthenticationEntryPointImpl`` denies it -- so the wire format is the usual
HTTP-200 ``AjaxResult`` with ``code`` 401 and the *path* ``/error``::

    {"code":401,"msg":"请求访问：/error，认证失败，无法访问系统资源"}

``OncePerRequestFilter`` skips an error dispatch, so the JWT filter does not run a second
time and does not throw again. Verified against the running Java backend for both
``GET /getInfo`` and ``POST /logout`` with a malformed token; the ``try`` below reproduces
that outcome instead of an error page. It covers **only** the filter chain -- wrapping
``call_next`` too would swallow endpoint exceptions that must keep reaching
``ServerErrorMiddleware`` (they are the ones that produce the HTTP-500 ``AjaxResult``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import anyio.to_thread
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.common.constant.http_status import HttpStatus
from app.config.exception_handlers import spring_error_response
from app.framework.config.security_config import AccessMode, is_logout_request, resolve_access
from app.framework.security.context.security_context import (
    AnonymousAuthenticationToken,
    Authentication,
    SecurityContextHolder,
)
from app.framework.security.filter.jwt_authentication_token_filter import (
    JwtAuthenticationTokenFilter,
    get_jwt_authentication_token_filter,
)
from app.framework.security.handle.authentication_entry_point_impl import (
    AuthenticationEntryPointImpl,
    get_authentication_entry_point,
)
from app.framework.security.handle.logout_success_handler_impl import (
    LogoutSuccessHandlerImpl,
    get_logout_success_handler,
)

logger = logging.getLogger("app.middleware.security")

#: The path a servlet container re-dispatches to when a filter throws. Java reports it (not
#: the original path) in the 401 body; see the module docstring.
ERROR_DISPATCH_URI = "/error"


@dataclass
class _FilterChainResult:
    """What the filter chain leaves behind for the endpoint and for the response.

    ``authentication`` is installed into ``SecurityContextHolder`` before the endpoint runs;
    ``response`` is set when a filter short-circuited (logout) or refused the request.
    """

    authentication: Optional[Authentication] = None
    response: Optional[Response] = None


def _is_anonymous(authentication: Optional[Authentication]) -> bool:
    """Java: ``AuthenticationTrustResolverImpl.isAnonymous(Authentication)``."""
    return isinstance(authentication, AnonymousAuthenticationToken)


def is_allowed(access: AccessMode, authentication: Optional[Authentication]) -> bool:
    """Java: the ``access`` expression evaluated by ``FilterSecurityInterceptor``.

    See :mod:`app.framework.config.security_config` for the truth table. The only non-obvious
    line is ``anonymous``: it is a *requirement*, not a permission -- an authenticated caller
    is **denied**, which is what ``AnonymousExpression`` does.
    """
    if access is AccessMode.PERMIT_ALL:
        # PermitAllExpression: true for every authentication, including anonymous.
        return True
    if access is AccessMode.DENY_ALL:
        return False
    if access is AccessMode.ANONYMOUS:
        return _is_anonymous(authentication)
    # AuthenticatedExpression: authenticated, and not the anonymous token.
    if authentication is None or not authentication.is_authenticated():
        return False
    return not _is_anonymous(authentication)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Java: ``FilterChainProxy`` for the single ``SecurityFilterChain`` of this project."""

    def __init__(
        self,
        app,  # noqa: ANN001 - ASGI callable
        jwt_filter: Optional[JwtAuthenticationTokenFilter] = None,
        entry_point: Optional[AuthenticationEntryPointImpl] = None,
        logout_handler: Optional[LogoutSuccessHandlerImpl] = None,
    ) -> None:
        super().__init__(app)
        self._jwt_filter = jwt_filter
        self._entry_point = entry_point
        self._logout_handler = logout_handler

    # ---- dependencies resolved per request, like an @Autowired bean lookup ------
    #
    # These deliberately do **not** cache on ``self``. Spring's ``FilterChainProxy`` holds a
    # reference to the singleton bean, so a lookup on every request is the closest analogue;
    # caching here would also pin a ``TokenService`` whose Redis client was replaced after the
    # middleware was constructed (which is what tests do).

    @property
    def jwt_filter(self) -> JwtAuthenticationTokenFilter:
        if self._jwt_filter is not None:
            return self._jwt_filter
        return get_jwt_authentication_token_filter()

    @property
    def entry_point(self) -> AuthenticationEntryPointImpl:
        if self._entry_point is not None:
            return self._entry_point
        return get_authentication_entry_point()

    @property
    def logout_handler(self) -> LogoutSuccessHandlerImpl:
        if self._logout_handler is not None:
            return self._logout_handler
        return get_logout_success_handler()

    # ---- request handling -------------------------------------------------------

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Java: SecurityContextPersistenceFilter always starts a request with a clean context
        # and clears it in ``finally``. ``ContextVar`` is copied per task, but uvicorn may
        # reuse the same task for several keep-alive requests, so both ends are cleared.
        SecurityContextHolder.clear_context()
        try:
            # The filter chain performs blocking I/O (Redis, JDBC); keep the loop free.
            result = await anyio.to_thread.run_sync(self._run_filter_chain, request)
        except Exception:
            # Java: 过滤器抛出的异常不会被 ControllerAdvice 处理，容器转而把请求 ERROR 派发到
            # /error；/error 不在放行名单里，于是又走一遍链子，由 AuthenticationEntryPointImpl
            # 拦下 —— 客户端看到的是 HTTP 200 + code 401，且 msg 里的路径是 /error。
            # OncePerRequestFilter 会跳过 error 派发，所以 JWT 过滤器不会二次抛异常。
            logger.error(
                "[安全过滤器异常] Path=%s, Method=%s", request.url.path, request.method, exc_info=True
            )
            return self.entry_point.commence_for_uri(ERROR_DISPATCH_URI)

        if result.response is not None:
            return result.response

        # Hand the authentication to the endpoint. ``BaseHTTPMiddleware`` copies the context
        # into the downstream task, and anyio copies it again into the sync endpoint's thread,
        # so setting it here is what makes ``SecurityUtils.getLoginUser()`` work.
        context = SecurityContextHolder.get_context()
        context.set_authentication(result.authentication)

        try:
            return await call_next(request)
        finally:
            SecurityContextHolder.clear_context()

    def _run_filter_chain(self, request: Request) -> _FilterChainResult:
        """Synchronous body of the chain; runs in a worker thread.

        Java equivalent, in order: ``LogoutFilter`` -> ``JwtAuthenticationTokenFilter`` ->
        ``AnonymousAuthenticationFilter`` -> ``ExceptionTranslationFilter`` +
        ``FilterSecurityInterceptor``.
        """
        # -- 1) LogoutFilter ------------------------------------------------------
        # Handles the request itself and never calls the rest of the chain, so no token is
        # parsed, no rule is consulted, and a token-less logout still answers 200.
        if is_logout_request(request.method, request.url.path):
            return _FilterChainResult(
                authentication=None,
                response=self.logout_handler.on_logout_success(request),
            )

        # -- 2) JwtAuthenticationTokenFilter --------------------------------------
        self.jwt_filter.do_filter_internal(request)

        # -- 3) AnonymousAuthenticationFilter -------------------------------------
        # Install the anonymous token when nothing authenticated the caller. It is a real
        # authentication object, which is what makes ``anonymous()`` rules work at all.
        context = SecurityContextHolder.get_context()
        if context.get_authentication() is None:
            context.set_authentication(AnonymousAuthenticationToken())
        authentication = context.get_authentication()

        # -- 4) ExceptionTranslationFilter + FilterSecurityInterceptor ------------
        access = resolve_access(request.method, request.url.path)
        if is_allowed(access, authentication):
            return _FilterChainResult(authentication=authentication, response=None)
        return _FilterChainResult(
            authentication=authentication,
            response=self._handle_access_denied(request, authentication),
        )

    def _handle_access_denied(
        self, request: Request, authentication: Optional[Authentication]
    ) -> Response:
        """Java: ``ExceptionTranslationFilter.handleAccessDeniedException``.

        An anonymous caller is sent to the ``AuthenticationEntryPoint`` (HTTP 200 + ``code``
        401) because "denied while not logged in" means "log in first". An authenticated
        caller is sent to ``AccessDeniedHandlerImpl``, which calls ``response.sendError(403)``
        -- a **real** 403 with ``BasicErrorController``'s body.
        """
        if _is_anonymous(authentication) or authentication is None:
            return self.entry_point.commence(request)
        logger.warning(
            "[访问拒绝] Path=%s, Method=%s, principal=%s",
            request.url.path,
            request.method,
            authentication.get_name(),
        )
        return spring_error_response(request, HttpStatus.FORBIDDEN, "Forbidden")


__all__ = ["SecurityMiddleware", "is_allowed", "_FilterChainResult"]
