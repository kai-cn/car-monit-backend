"""Current HTTP request, reachable from code that has no request parameter.

Not a RuoYi file
----------------
Spring exposes the current request through ``RequestContextHolder`` (a ``ThreadLocal``
populated by ``RequestContextFilter``); RuoYi wraps it as
``ServletUtils.getRequest()``. Several service-layer methods rely on it because Spring can
inject nothing else there -- ``TokenService.setUserAgent`` and ``AsyncFactory`` both call
``ServletUtils.getRequest()`` with no request in scope.

Python's equivalent is a ``ContextVar`` set by a small middleware
(:class:`app.middleware.request_context.RequestContextMiddleware`), so no service method
has to grow a ``request: Request`` parameter that its Java counterpart does not have.

Outside a request (startup tasks, scheduler jobs, tests) :func:`get_request` returns
``None`` -- exactly what Spring does, and Java would then throw an NPE at the first
attribute access. Callers that can run outside a request must check.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

from starlette.requests import Request

_REQUEST: ContextVar[Optional[Request]] = ContextVar("current_request", default=None)


def set_request(request: Optional[Request]) -> None:
    """Bind the request for the current task (called by the middleware)."""
    _REQUEST.set(request)


def get_request() -> Optional[Request]:
    """Java: ``ServletUtils.getRequest()`` -- ``None`` outside a request context."""
    return _REQUEST.get()


def clear_request() -> None:
    """Unbind; the middleware calls this in ``finally`` so pooled threads stay clean."""
    _REQUEST.set(None)


__all__ = ["set_request", "get_request", "clear_request"]
