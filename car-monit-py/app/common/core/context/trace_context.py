"""Request trace identifier propagation.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/common/core/context/TraceContext.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/common/core/filter/TraceIdFilter.java

Java original
-------------
``TraceContext`` stores the correlation id in a ``ThreadLocal<String>`` populated by
``TraceIdFilter`` and consumed by ``TraceAspect`` and the logback ``%X{traceId}`` pattern.

Python equivalent
-----------------
``contextvars.ContextVar`` -- the Python analogue of ``ThreadLocal`` that also survives
``async``/threadpool boundaries. Because every endpoint runs as a sync ``def`` inside
FastAPI's threadpool, one request == one context; the middleware resets the variable in
``finally`` exactly like ``TraceIdFilter.doFilter`` removes it.
"""

from __future__ import annotations

import contextvars
import uuid
from typing import Optional

# Java: private static final ThreadLocal<String> TRACE_ID = new ThreadLocal<>();
_trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)


def get_trace_id() -> Optional[str]:
    """Java: TraceContext.getTraceId()."""
    return _trace_id.get()


def set_trace_id(trace_id: Optional[str]) -> None:
    """Java: TraceContext.setTraceId(String)."""
    _trace_id.set(trace_id)


def remove_trace_id() -> None:
    """Java: TraceContext.remove()."""
    _trace_id.set(None)


def generate_trace_id() -> str:
    """32-char hex, matching the id shape produced by the Java filter."""
    return uuid.uuid4().hex
