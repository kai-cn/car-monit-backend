"""可疑车辆备份 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousBackController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:carsuspiciousback:list``
``export``                GET ``/export``             ``manager:carsuspiciousback:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:carsuspiciousback:add``
``edit``                  PUT ``""``                  ``manager:carsuspiciousback:edit``
``remove``                DELETE ``/{ids}``           ``manager:carsuspiciousback:remove``
========================  ==========================  ==============================

导出走 ``ExcelUtil<CarSuspiciousBack>(CarSuspiciousBack.class).exportExcel(list, "可疑车辆备份数据")``
—— 列由 ``@Excel`` 注解决定（见 ``CarSuspiciousBack.EXCEL_FIELDS``），
返回体里的 ``msg`` 是文件名（没有 ``data`` 键）。
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
from app.manager.domain.car_suspicious_back import CarSuspiciousBack
from app.manager.service.car_suspicious_back_service import (
    CarSuspiciousBackService,
    get_car_suspicious_back_service,
)

router = APIRouter(prefix="/manager/carsuspiciousback", tags=["manager-suspicious-back"])

#: Java: ``com.ruoyi.web.controller.manager.CarSuspiciousBackController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarSuspiciousBackController"

#: Java: ``util.exportExcel(list, "可疑车辆备份数据")`` —— sheet 名与文件名前缀。
EXPORT_SHEET_NAME = "可疑车辆备份数据"

_SERVICE: Optional[CarSuspiciousBackService] = None


def _service() -> CarSuspiciousBackService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_suspicious_back_service()
    return _SERVICE


def reset_suspicious_back_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarSuspiciousBack:
    """Java: 形参 ``CarSuspiciousBack carSuspiciousBack``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarSuspiciousBack, request.query_params)


CarSuspiciousBackParam = Annotated[CarSuspiciousBack, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:carsuspiciousback:list")
def list_suspicious_backs(query: CarSuspiciousBackParam) -> TableDataInfo:
    """查询可疑车辆备份列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的** —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:carsuspiciousback:export")
@log(title="可疑车辆备份", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarSuspiciousBackParam) -> AjaxResult:
    """导出可疑车辆备份列表. Java: ``@GetMapping("/export")``."""
    rows = _service().select_list(query)
    return ExcelUtil(CarSuspiciousBack).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取可疑车辆备份详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:carsuspiciousback:add")
@log(title="可疑车辆备份", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarSuspiciousBack) -> AjaxResult:
    """新增可疑车辆备份. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:carsuspiciousback:edit")
@log(title="可疑车辆备份", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarSuspiciousBack) -> AjaxResult:
    """修改可疑车辆备份. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:carsuspiciousback:remove")
@log(title="可疑车辆备份", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除可疑车辆备份. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "get_info",
    "list_suspicious_backs",
    "remove",
    "reset_suspicious_back_controller",
]
