"""Binds the current request for code that cannot take a ``Request`` parameter.

Not a RuoYi file
----------------
Spring Boot registers ``RequestContextFilter`` (order ``-105``), which populates
``RequestContextHolder`` so ``((ServletRequestAttributes)
RequestContextHolder.getRequestAttributes()).getRequest()`` -- wrapped by RuoYi as
``ServletUtils.getRequest()`` -- works anywhere in the call stack.

Python has no implicit request object, and threading one through would change the signature of
every service method. This middleware is the equivalent: it stores the request in a
``ContextVar`` (:mod:`app.common.core.context.request_context`) that
:func:`app.common.utils.servlet_utils.get_request` reads.

Two callers depend on it and neither has a ``request`` parameter in Java either:

* ``TokenService.setUserAgent`` -- called from ``createToken`` during login.
* ``AsyncFactory.recordLogininfor`` -- called from the login / logout / register paths.

Ordering
--------
This middleware must sit **outside** :class:`app.middleware.security.SecurityMiddleware`,
because the logout handler runs the audit task factory while it is still inside the security
layer. In the Java chain the ordering is the reverse (``RequestContextFilter`` runs before
Spring Security), but the constraint is the same: the holder must be populated before anything
security-related touches it.

``BaseHTTPMiddleware`` copies the context into the downstream task, so a value set here is
visible to the endpoint but not modifiable by it -- which is exactly the lifetime we want.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.common.core.context import request_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Java: ``RequestContextFilter`` -- bind / unbind the current request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Java: RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(request))
        request_context.set_request(request)
        try:
            return await call_next(request)
        finally:
            # Spring clears the ThreadLocal per request (``RequestContextFilter`` ->
            # ``ServletRequestAttributes.requestCompleted``); without this a reused event-loop
            # task would keep the previous request alive -- and its body stream with it.
            request_context.clear_request()


__all__ = ["RequestContextMiddleware"]
