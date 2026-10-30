"""车辆位置 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataLocationDictController.java

2 个映射，全部迁移
------------------
==========  =================  =============================
Java         Method / Path      权限点
==========  =================  =============================
``list``     GET ``/list``      **无**（登录即可）
``getInfo``  GET ``/{id}``      **无**
==========  =================  =============================

只读控制器：没有 ``export`` / ``add`` / ``edit`` / ``remove``。
路径变量是 ``Long``（不是 ``String``），所以走 ``int`` 类型注解；非数字段会落到
FastAPI 的 422，而 Java 侧是 ``MethodArgumentTypeMismatchException`` -> 500 ——
这个差异已登记在 ``COMPATIBILITY.md``。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.zdata_location_dict import ZdataLocationDict
from app.base.service.zdata_location_dict_service import (
    ZdataLocationDictService,
    get_zdata_location_dict_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/location", tags=["base-location"])

_SERVICE: Optional[ZdataLocationDictService] = None


def _service() -> ZdataLocationDictService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_zdata_location_dict_service()
    return _SERVICE


def reset_location_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> ZdataLocationDict:
    """Java: 形参 ``ZdataLocationDict x``（无 ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(ZdataLocationDict, request.query_params)


#: 查询条件实体。
LocationParam = Annotated[ZdataLocationDict, Depends(_query)]


@router.get("/list", response_model=None)
def list_locations(query: LocationParam) -> TableDataInfo:
    """查询车辆位置列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/{id}", response_model=None)
def get_info(id: int) -> AjaxResult:
    """获取车辆位置详细信息. Java: ``@GetMapping(value = "/{id}") @PathVariable("id") Long id``."""
    return AjaxResult.success_data(_service().select_by_id(id))


__all__ = [
    "router",
    "LocationParam",
    "list_locations",
    "get_info",
    "reset_location_controller",
]
