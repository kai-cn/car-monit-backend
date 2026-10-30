"""Servlet-style request helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/ServletUtils.java

Only the helpers that the migrated code actually calls are ported. ``renderString`` uses
``HTTP 200`` on purpose -- that is what the Java method does, and several handlers depend
on it (see ``app/config/exception_handlers.py``).

``getRequest()`` is the one method with no direct Python counterpart: Spring binds the
current request to a ``ThreadLocal`` (``RequestContextHolder``) whereas FastAPI passes it as
a parameter. The value therefore comes from
:mod:`app.common.core.context.request_context`, which a middleware populates. Same empty
result outside a request, same null pointer at the first attribute access.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request, Response

from app.common.constant.http_status import HttpStatus
from app.common.core.context import request_context

#: Header precedence copied verbatim from ``ServletUtils.getClientIP``.
_IP_HEADERS = (
    "X-Forwarded-For",
    "X-Real-IP",
    "Proxy-Client-IP",
    "WL-Proxy-Client-IP",
    "HTTP_CLIENT_IP",
    "HTTP_X_FORWARDED_FOR",
)

_UNKNOWN = "unknown"


def get_client_ip(request: Request) -> str:
    """Resolve the real client IP.

    Java: ``ServletUtils.getClientIP(HttpServletRequest)`` -- reads the same headers in the
    same order and keeps only the first entry of a comma-separated ``X-Forwarded-For``.
    """
    ip: Optional[str] = None
    for header in _IP_HEADERS:
        candidate = request.headers.get(header)
        if candidate and candidate.lower() != _UNKNOWN:
            ip = candidate
            break
    if not ip:
        ip = request.client.host if request.client else ""
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    return ip or ""


def render_string(payload: str) -> Response:
    """Java: ``ServletUtils.renderString(response, json)`` -- always HTTP 200.

    The Java implementation sets ``response.setStatus(200)`` unconditionally, which is why
    RuoYi answers 200 even for 401/403 outcomes. Kept identical on purpose.

    The body is written **verbatim**: ``payload`` is a string that has already been
    serialised by the caller (``JSON.toJSONString(...)`` in Java). Handing it to
    ``JSONResponse`` would serialise it a second time and produce a quoted JSON string, so a
    plain ``Response`` is used instead.
    """
    # Java: response.setContentType("application/json"); response.setCharacterEncoding("utf-8");
    return Response(
        content=payload,
        status_code=HttpStatus.SUCCESS,
        media_type="application/json;charset=UTF-8",
    )


def is_ajax_request(request: Request) -> bool:
    """Java: ``ServletUtils.isAjaxRequest`` -- ``X-Requested-With: XMLHttpRequest``."""
    return request.headers.get("X-Requested-With", "").lower() == "xmlhttprequest"


def get_request() -> Optional[Request]:
    """Java: ``ServletUtils.getRequest()``.

    Returns the request bound to the current execution context, or ``None`` when called
    outside one (startup task, scheduler job, unit test) -- exactly when Spring would throw
    ``IllegalStateException``/return null depending on the holder variant. Callers that can
    run outside a request must check, as ``TokenService.setUserAgent`` does.
    """
    return request_context.get_request()
