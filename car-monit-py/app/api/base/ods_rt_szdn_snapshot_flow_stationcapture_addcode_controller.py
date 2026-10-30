"""收费站抓拍 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeController.java

2 个映射，全部迁移
------------------
=========  ==================  ==========
Java        Method / Path       权限点
=========  ==================  ==========
``list``   GET ``/list``       **无**
``getInfo`` GET ``/{bigId}``    **无**
=========  ==================  ==========

前缀 ``/base/stationcapture``；``/{bigId}`` 是 ``Long``（非数字 -> ``code 500``）。
``setTenantId`` 那行在 Java 里是注释掉的，照抄。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_rt_szdn_snapshot_flow_stationcapture_addcode import (
    OdsRtSzdnSnapshotFlowStationcaptureAddcode,
)
from app.base.service.ods_rt_szdn_snapshot_flow_stationcapture_addcode_service import (
    OdsRtSzdnSnapshotFlowStationcaptureAddcodeService,
    get_ods_rt_szdn_snapshot_flow_stationcapture_addcode_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/stationcapture", tags=["base-station-capture"])

_SERVICE: Optional[OdsRtSzdnSnapshotFlowStationcaptureAddcodeService] = None


def _service() -> OdsRtSzdnSnapshotFlowStationcaptureAddcodeService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_rt_szdn_snapshot_flow_stationcapture_addcode_service()
    return _SERVICE


def reset_station_capture_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> OdsRtSzdnSnapshotFlowStationcaptureAddcode:
    """Java: 形参 ``OdsRtSzdnSnapshotFlowStationcaptureAddcode x``（**没有** ``@RequestBody``）。"""
    return bind_query_params(
        OdsRtSzdnSnapshotFlowStationcaptureAddcode, request.query_params
    )


#: 查询条件实体.
StationCaptureParam = Annotated[
    OdsRtSzdnSnapshotFlowStationcaptureAddcode, Depends(_query)
]


@router.get("/list", response_model=None)
def list_station_captures(query: StationCaptureParam) -> TableDataInfo:
    """查询收费站抓拍列表. Java: ``@GetMapping("/list")``."""
    start_page()
    rows = _service().select_list(query)
    return get_data_table(rows)


@router.get("/{bigId}", response_model=None)
def get_info(bigId: int) -> AjaxResult:
    """获取收费站抓拍详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    return AjaxResult.success_data(_service().select_by_id(bigId))


__all__ = [
    "StationCaptureParam",
    "get_info",
    "list_station_captures",
    "reset_station_capture_controller",
    "router",
]
