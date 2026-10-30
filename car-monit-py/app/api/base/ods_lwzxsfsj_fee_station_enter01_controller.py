"""收费站入口数据 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationEnter01Controller.java

2 个映射，全部迁移
------------------
=========  ==================  ==========
Java        Method / Path       权限点
=========  ==================  ==========
``list``   GET ``/list``       **无**
``getInfo`` GET ``/{bigId}``    **无**
=========  ==================  ==========

与 ``OdsCxztFwqcllsController`` 的区别
--------------------------------------
1. 前缀是 ``/base/feeStationEnter``（驼峰，**不是** snake_case）。
2. ``/list`` **没有** ``@PreAuthorize`` —— 登录即可访问。
3. ``/{bigId}`` 是 ``Long``，传非数字 -> ``code 500``。

``setTenantId`` 那行在 Java 里是**注释掉的**，照抄（列表跨租户可见）。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_lwzxsfsj_fee_station_enter01 import (
    OdsLwzxsfsjFeeStationEnter01,
)
from app.base.service.ods_lwzxsfsj_fee_station_enter01_service import (
    OdsLwzxsfsjFeeStationEnter01Service,
    get_ods_lwzxsfsj_fee_station_enter01_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/feeStationEnter", tags=["base-fee-station-enter"])

_SERVICE: Optional[OdsLwzxsfsjFeeStationEnter01Service] = None


def _service() -> OdsLwzxsfsjFeeStationEnter01Service:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_lwzxsfsj_fee_station_enter01_service()
    return _SERVICE


def reset_fee_station_enter_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> OdsLwzxsfsjFeeStationEnter01:
    """Java: 形参 ``OdsLwzxsfsjFeeStationEnter01 x``（**没有** ``@RequestBody``）。"""
    return bind_query_params(OdsLwzxsfsjFeeStationEnter01, request.query_params)


#: 查询条件实体.
FeeStationEnterParam = Annotated[OdsLwzxsfsjFeeStationEnter01, Depends(_query)]


@router.get("/list", response_model=None)
def list_fee_station_enters(query: FeeStationEnterParam) -> TableDataInfo:
    """查询收费站入口数据列表. Java: ``@GetMapping("/list")``."""
    start_page()
    rows = _service().select_list(query)
    return get_data_table(rows)


@router.get("/{bigId}", response_model=None)
def get_info(bigId: int) -> AjaxResult:
    """获取收费站入口数据详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    return AjaxResult.success_data(_service().select_by_id(bigId))


__all__ = [
    "FeeStationEnterParam",
    "get_info",
    "list_fee_station_enters",
    "reset_fee_station_enter_controller",
    "router",
]
