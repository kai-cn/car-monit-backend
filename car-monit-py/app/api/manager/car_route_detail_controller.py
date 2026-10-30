"""常用路线明细 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarRouteDetailController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:routedetail:list``
``export``                GET ``/export``             ``manager:routedetail:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:routedetail:add``
``edit``                  PUT ``""``                  ``manager:routedetail:edit``
``remove``                DELETE ``/{ids}``           ``manager:routedetail:remove``
========================  ==========================  ==============================

导出走 ``ExcelUtil<CarRouteDetail>(CarRouteDetail.class).exportExcel(list, "常用路线明细数据")``
—— 列由 ``@Excel`` 注解决定，返回体里的 ``msg`` 是文件名（没有 ``data`` 键）。

``list`` 里那行 ``// carRouteDetail.setTenantId(SecurityUtils.getTenantId())``
在 Java 里是**注释掉的**，所以查询不按租户过滤 —— 照抄，不要"补上"。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_route_detail import CarRouteDetail
from app.manager.service.car_route_detail_service import (
    CarRouteDetailService,
    get_car_route_detail_service,
)

router = APIRouter(prefix="/manager/routedetail", tags=["manager-route-detail"])

#: Java: ``com.ruoyi.web.controller.manager.CarRouteDetailController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarRouteDetailController"

#: Java: ``util.exportExcel(list, "常用路线明细数据")`` —— sheet 名与文件名前缀。
EXPORT_SHEET_NAME = "常用路线明细数据"

_SERVICE: Optional[CarRouteDetailService] = None


def _service() -> CarRouteDetailService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_route_detail_service()
    return _SERVICE


def reset_route_detail_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarRouteDetail:
    """Java: 形参 ``CarRouteDetail carRouteDetail``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarRouteDetail, request.query_params)


RouteDetailParam = Annotated[CarRouteDetail, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:routedetail:list")
def list_route_details(query: RouteDetailParam) -> TableDataInfo:
    """查询常用路线明细列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:routedetail:export")
@log(title="常用路线明细", business_type=BusinessType.EXPORT, java_method="export")
def export(query: RouteDetailParam) -> AjaxResult:
    """导出常用路线明细列表. Java: ``@GetMapping("/export")``."""
    rows = _service().select_list(query)
    return ExcelUtil(CarRouteDetail).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002
    """获取常用路线明细详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:routedetail:add")
@log(title="常用路线明细", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarRouteDetail) -> AjaxResult:
    """新增常用路线明细. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:routedetail:edit")
@log(title="常用路线明细", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarRouteDetail) -> AjaxResult:
    """修改常用路线明细. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:routedetail:remove")
@log(title="常用路线明细", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除常用路线明细. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "get_info",
    "list_route_details",
    "remove",
    "reset_route_detail_controller",
]
