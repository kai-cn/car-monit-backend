"""Health probe.

# Migrated from: (none) -- ADDED endpoint, see COMPATIBILITY.md §"Added endpoints"

Why this file exists
--------------------
The Java project has **no** actuator, no ``/health`` and no Spring Boot health indicator.
The only liveness signal it exposes is ``GET /`` (``SysIndexController``), which returns a
plain welcome string and touches no dependency at all.

Deployment acceptance for the Python port requires a probe that reports whether MySQL and
Redis are actually reachable, so ``/health`` is added. It is *additive*: it does not alter
any existing path, response shape or status code, and it can be removed by setting
``app.health_endpoint_enabled=false`` (or ``APP__HEALTH_ENDPOINT_ENABLED=false``).

Response shape reuses ``AjaxResult`` so that callers parse it like every other endpoint::

    {"code": 200, "msg": "操作成功",
     "data": {"status": "UP", "application": "系统", "components": {"db": "UP", "redis": "UP"}}}
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from app.common.constant.http_status import HttpStatus
from app.common.core.domain.ajax_result import AjaxResult
from app.config.database import check_connection as check_database
from app.config.redis_config import check_connection as check_redis
from app.settings import get_settings

router = APIRouter(tags=["health"])


# ``response_model=None`` is required because ``AjaxResult`` subclasses ``dict``:
# FastAPI would otherwise try to derive a Pydantic response model from the return
# annotation and fail at import time. In Java ``AjaxResult extends HashMap`` and
# Jackson serializes it verbatim -- disabling the response model is the exact analogue.
@router.get("/health", response_model=None)
def health() -> AjaxResult:
    """Report application + dependency status.

    HTTP status is always 200 (RuoYi convention). Inspect ``data.status``; ``UP`` only when
    every probed component is reachable.
    """
    settings = get_settings()
    components: Dict[str, Any] = {
        "db": "UP" if check_database() else "DOWN",
        "redis": "UP" if check_redis() else "DOWN",
    }
    overall = "UP" if all(state == "UP" for state in components.values()) else "DOWN"
    payload: Dict[str, Any] = {
        "status": overall,
        "application": settings.ruoyi.name,
        "version": settings.ruoyi.version,
        "components": components,
    }
    if overall == "UP":
        return AjaxResult._create(HttpStatus.SUCCESS, "操作成功", payload)
    return AjaxResult._create(HttpStatus.SUCCESS, "部分依赖不可用", payload)
