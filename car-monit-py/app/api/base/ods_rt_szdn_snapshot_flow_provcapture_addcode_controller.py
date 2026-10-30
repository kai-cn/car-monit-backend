"""省界抓拍 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeController.java

2 个映射，全部迁移
------------------
=========  ==================  ==========
Java        Method / Path       权限点
=========  ==================  ==========
``list``   GET ``/list``       **无**
``getInfo`` GET ``/{bigId}``    **无**
=========  ==================  ==========

前缀 ``/base/provcapture``；``/{bigId}`` 是 ``Long``（非数字 -> ``code 500``）。
``setTenantId`` 那行在 Java 里是注释掉的，照抄。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_rt_szdn_snapshot_flow_provcapture_addcode import (
    OdsRtSzdnSnapshotFlowProvcaptureAddcode,
)
from app.base.service.ods_rt_szdn_snapshot_flow_provcapture_addcode_service import (
    OdsRtSzdnSnapshotFlowProvcaptureAddcodeService,
    get_ods_rt_szdn_snapshot_flow_provcapture_addcode_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/provcapture", tags=["base-prov-capture"])

_SERVICE: Optional[OdsRtSzdnSnapshotFlowProvcaptureAddcodeService] = None


def _service() -> OdsRtSzdnSnapshotFlowProvcaptureAddcodeService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_rt_szdn_snapshot_flow_provcapture_addcode_service()
    return _SERVICE


def reset_prov_capture_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> OdsRtSzdnSnapshotFlowProvcaptureAddcode:
    """Java: 形参 ``OdsRtSzdnSnapshotFlowProvcaptureAddcode x``（**没有** ``@RequestBody``）。"""
    return bind_query_params(
        OdsRtSzdnSnapshotFlowProvcaptureAddcode, request.query_params
    )


#: 查询条件实体.
ProvCaptureParam = Annotated[OdsRtSzdnSnapshotFlowProvcaptureAddcode, Depends(_query)]


@router.get("/list", response_model=None)
def list_prov_captures(query: ProvCaptureParam) -> TableDataInfo:
    """查询省界抓拍列表. Java: ``@GetMapping("/list")``."""
    start_page()
    rows = _service().select_list(query)
    return get_data_table(rows)


@router.get("/{bigId}", response_model=None)
def get_info(bigId: int) -> AjaxResult:
    """获取省界抓拍详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    return AjaxResult.success_data(_service().select_by_id(bigId))


__all__ = [
    "ProvCaptureParam",
    "get_info",
    "list_prov_captures",
    "reset_prov_capture_controller",
    "router",
]
