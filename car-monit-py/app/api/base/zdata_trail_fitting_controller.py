"""车辆出入口拟合轨迹 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailFittingController.java

2 个映射，全部迁移
------------------
==========  =================  =============================
Java         Method / Path      权限点
==========  =================  =============================
``list``     GET ``/list``      **无**（登录即可）
``getInfo``  GET ``/{cid}``     **无**
==========  =================  =============================

只读控制器；主键列是 ``cid``（``String``）。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.zdata_trail_fitting import ZdataTrailFitting
from app.base.service.zdata_trail_fitting_service import (
    ZdataTrailFittingService,
    get_zdata_trail_fitting_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/fitting", tags=["base-fitting"])

_SERVICE: Optional[ZdataTrailFittingService] = None


def _service() -> ZdataTrailFittingService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_zdata_trail_fitting_service()
    return _SERVICE


def reset_fitting_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> ZdataTrailFitting:
    """Java: 形参 ``ZdataTrailFitting x``（无 ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(ZdataTrailFitting, request.query_params)


#: 查询条件实体。
TrailFittingParam = Annotated[ZdataTrailFitting, Depends(_query)]


@router.get("/list", response_model=None)
def list_trail_fittings(query: TrailFittingParam) -> TableDataInfo:
    """查询车辆出入口拟合轨迹列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/{cid}", response_model=None)
def get_info(cid: str) -> AjaxResult:
    """获取车辆出入口拟合轨迹详细信息. Java: ``@GetMapping(value = "/{cid}")``."""
    result = AjaxResult.success_data(_service().select_by_id(cid))
    # Java 基准在详情信封上追加来源与实时性标记；键顺序无关，结构必须一致。
    result.put_chain("dataSource", "LOCAL_DB")
    result.put_chain("realtime", False)
    result.put_chain("message", "数据来自 backend 本地表，可能陈旧，无实时保证")
    return result


__all__ = [
    "router",
    "TrailFittingParam",
    "list_trail_fittings",
    "get_info",
    "reset_fitting_controller",
]
