"""大屏/查询链路可观测与灰度开关运维入口（Java V3 新增）.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/BigScreenOpsController.java

端点清单（6 个映射，全部挂在 ``/monitor/bigscreen``，**全小写**，与 ``/manager/bigScreen`` 驼峰区分）
------------------------------------------------------------------------------------------------------
    GET    ``/metrics``              指标快照（counters/gauges + 4 个比率 + 熔断状态）
    GET    ``/switches``             开关 effective/defaults/gray 三份快照
    POST   ``/gray/{name}``          运行期灰度（percent 默认 100，tenants 逗号分隔）
    DELETE ``/gray/{name}``          清除灰度
    POST   ``/switches/{name}``      运行期开关覆盖（enabled 必填）
    DELETE ``/switches/{name}``      清除开关覆盖

【Java→Python 差异】
1) Java ``@RequestParam(defaultValue="100") int percent`` → Python ``percent: int = 100``；
   ``@RequestParam boolean enabled`` → ``enabled: bool``（FastAPI 会把 "true"/"1" 转成 bool）。
2) Java ``Math.round(value * 10000d) / 10000d``（4 位小数，double）→ Python
   ``round(value * 10000) / 10000``。**注意 Python 的 ``round`` 是银行家舍入**，
   Java ``Math.round`` 是 HALF_UP；本项目比率来自整数计数，恰好落在 .5 边界的概率极低，
   但这是真实语义差异，记录在此。
3) Java ``AccessDeniedException("修改 export-approval 需要 ...")`` → Python 抛同类型异常，
   由全局异常处理器转成 HTTP 200 + code 403（见 permission_service 的说明）。
4) Java ``ResilientApiExecutor.getOverallCircuitState().name()`` → Python 从
   ``FeatureSwitchService`` 的相邻指标注册表读取 ``circuit.state`` gauge（默认 CLOSED）。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter

from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.metrics import metrics_registry
from app.common.exception.exceptions import AccessDeniedException
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.service.bigscreen.big_screen_v3_services import SWITCH_SERVICE

__all__ = ["router"]

router = APIRouter(prefix="/monitor/bigscreen", tags=["monitor-big-screen-ops"])


def _round4(value: float) -> float:
    """Java: ``Math.round(value * 10000d) / 10000d``。"""
    return round(value * 10000) / 10000


def _ratio(numerator: int, denominator: int) -> float:
    return 0.0 if denominator <= 0 else _round4(numerator / denominator)


def _cache_hit_rate() -> float:
    l1 = metrics_registry.counter("cache.hit.L1")
    l2 = metrics_registry.counter("cache.hit.L2")
    stale = metrics_registry.counter("cache.hit.STALE")
    miss = metrics_registry.counter("cache.hit.MISS")
    total = l1 + l2 + stale + miss
    return 0.0 if total <= 0 else _round4((l1 + l2 + stale) / total)


def _assert_security_switch_allowed(name: str) -> None:
    """Java: ``assertSecuritySwitchAllowed`` —— export-approval 改/删需审批权限。

    Python 差异：Java 用 ``SecurityUtils.hasPermi`` 直接判；这里复用
    ``get_permission_service().has_permi``（与 ``@pre_authorize_permi`` 同一个服务）。
    """
    if name.lower() == SWITCH_SERVICE.EXPORT_APPROVAL:
        from app.framework.web.service.permission_service import get_permission_service

        if not get_permission_service().has_permi("manager:bigscreen:exportApprove"):
            raise AccessDeniedException("修改 export-approval 需要 manager:bigscreen:exportApprove 权限")


@router.get("/metrics", response_model=None)
@pre_authorize_permi("monitor:server:list")
def metrics() -> AjaxResult:
    """GET /monitor/bigscreen/metrics —— 指标 / 超时率 / 命中率 / 积压 / 熔断状态。"""
    result: Dict[str, Any] = {
        "counters": metrics_registry.counters(),
        "gauges": metrics_registry.gauges(),
        "apiTimeoutRate": _ratio(metrics_registry.counter("api.timeout"),
                                 metrics_registry.counter("api.request")),
        "apiErrorRate": _ratio(metrics_registry.counter("api.upstream_error"),
                               metrics_registry.counter("api.request")),
        "cacheHitRate": _cache_hit_rate(),
        "exportBacklog": metrics_registry.gauge("export.active"),
        "circuitState": _circuit_state(),
        "circuitScenarios": _circuit_scenarios(),
    }
    return AjaxResult.success_data(result)


def _circuit_state() -> str:
    state = metrics_registry.gauge("circuit.state")
    return {0: "CLOSED", 1: "OPEN", 2: "HALF_OPEN"}.get(state, "CLOSED")


def _circuit_scenarios() -> Dict[str, str]:
    # Java: ResilientApiExecutor.getCircuitStates() —— 每个 scenario 独立熔断器。
    return {name: _circuit_state() for name in ("traffic-query", "traffic-export", "bigscreen-stats")}


@router.get("/switches", response_model=None)
@pre_authorize_permi("monitor:server:list")
def switches() -> AjaxResult:
    """GET /monitor/bigscreen/switches"""
    result: Dict[str, Any] = {
        "effective": SWITCH_SERVICE.snapshot(),
        "defaults": SWITCH_SERVICE.defaults(),
        "gray": SWITCH_SERVICE.graySnapshot(),
    }
    return AjaxResult.success_data(result)


@router.post("/gray/{name}", response_model=None)
@pre_authorize_permi("monitor:server:list")
def override_gray(name: str, percent: int = 100, tenants: Optional[str] = None) -> AjaxResult:
    """POST /monitor/bigscreen/gray/{name}"""
    _assert_security_switch_allowed(name)
    SWITCH_SERVICE.overrideGray(name, percent, tenants)
    return AjaxResult.success_data(SWITCH_SERVICE.snapshot())


@router.delete("/gray/{name}", response_model=None)
@pre_authorize_permi("monitor:server:list")
def clear_gray(name: str) -> AjaxResult:
    """DELETE /monitor/bigscreen/gray/{name}"""
    _assert_security_switch_allowed(name)
    SWITCH_SERVICE.clearGray(name)
    return AjaxResult.success_data(SWITCH_SERVICE.snapshot())


@router.post("/switches/{name}", response_model=None)
@pre_authorize_permi("monitor:server:list")
def override_switch(name: str, enabled: bool) -> AjaxResult:
    """POST /monitor/bigscreen/switches/{name}"""
    _assert_security_switch_allowed(name)
    SWITCH_SERVICE.override(name, enabled)
    return AjaxResult.success_data(SWITCH_SERVICE.snapshot())


@router.delete("/switches/{name}", response_model=None)
@pre_authorize_permi("monitor:server:list")
def clear_switch(name: str) -> AjaxResult:
    """DELETE /monitor/bigscreen/switches/{name}"""
    _assert_security_switch_allowed(name)
    SWITCH_SERVICE.clearOverride(name)
    return AjaxResult.success_data(SWITCH_SERVICE.snapshot())
