"""Request trace middleware.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/common/core/filter/TraceIdFilter.java

Java original
-------------
``TraceIdFilter`` (registered as a servlet filter) runs before Spring Security:
  1. reads ``X-Trace-Id`` from the request (upstream propagation) or generates one
  2. ``TraceContext.init(traceId)`` and ``TraceContext.setRequestPath(uri)``
  3. echoes the id back in the ``X-Trace-Id`` response header
  4. logs request enter / response exit with the elapsed time
  5. warns when ``cost >= 3000`` ms  (threshold is hard-coded, not read from config)
  6. ``TraceContext.clear()`` in ``finally`` so pooled threads never leak context

Python equivalent
-----------------
An ASGI middleware. ``BaseHTTPMiddleware`` runs in the event loop, and anyio copies the
current :mod:`contextvars` context into ``run_in_threadpool``, so a sync ``def`` endpoint
observes the same trace id the middleware set.
"""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.common.core.context.trace_context import (
    generate_trace_id,
    get_trace_id,
    remove_trace_id,
    set_trace_id,
)
from app.common.utils.servlet_utils import get_client_ip
from app.settings import AppSettings, get_settings

logger = logging.getLogger("app.middleware.trace_id")

#: Java: ``private static final String TRACE_ID_HEADER = "X-Trace-Id";``
TRACE_ID_HEADER = "X-Trace-Id"

#: Java: ``if (cost >= 3000)`` inside TraceIdFilter -- deliberately not configurable.
SLOW_REQUEST_THRESHOLD_MS = 3000


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Populate / clear the trace context around every request."""

    def __init__(self, app, settings: AppSettings | None = None) -> None:  # noqa: ANN001
        super().__init__(app)
        self._settings = settings or get_settings()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        header_name = self._settings.monitor.trace_id_header or TRACE_ID_HEADER
        incoming = request.headers.get(header_name)

        # Java: TraceContext.init(traceId) -- generated when the header is absent.
        trace_id = incoming or generate_trace_id()
        set_trace_id(trace_id)

        start = time.perf_counter()
        client_ip = get_client_ip(request)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "[请求进入] Method=%s, Path=%s, IP=%s, ContentType=%s, TraceId=%s",
                request.method,
                request.url.path,
                client_ip,
                request.headers.get("content-type"),
                trace_id,
            )

        try:
            response = await call_next(request)
        finally:
            # Java: finally { ... TraceContext.clear(); }
            remove_trace_id()

        cost_ms = (time.perf_counter() - start) * 1000.0
        status = response.status_code

        # Java: httpResponse.setHeader(TRACE_ID_HEADER, TraceContext.getTraceId())
        response.headers[TRACE_ID_HEADER] = trace_id

        if status >= 500:
            logger.error("[服务器错误响应] Path=%s, Status=%s, 耗时=%.0fms, TraceId=%s, IP=%s", request.url.path, status, cost_ms, trace_id, client_ip)
        elif status >= 400:
            logger.warning("[客户端错误响应] Path=%s, Status=%s, 耗时=%.0fms, TraceId=%s, IP=%s", request.url.path, status, cost_ms, trace_id, client_ip)
        else:
            logger.info("[请求完成] Path=%s, Status=%s, 耗时=%.0fms, TraceId=%s", request.url.path, status, cost_ms, trace_id)

        if cost_ms >= SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "[慢请求告警] Path=%s, 耗时=%.0fms, Method=%s, IP=%s, TraceId=%s",
                request.url.path,
                cost_ms,
                request.method,
                client_ip,
                trace_id,
            )

        return response


__all__ = ["TraceIdMiddleware", "TRACE_ID_HEADER", "SLOW_REQUEST_THRESHOLD_MS", "get_trace_id"]
