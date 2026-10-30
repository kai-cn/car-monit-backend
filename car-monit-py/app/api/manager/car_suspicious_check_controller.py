"""可疑车辆核查 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousCheckController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:suspiciouscheck:list``
``export``                GET ``/export``             ``manager:suspiciouscheck:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:suspiciouscheck:add``
``edit``                  PUT ``""``                  ``manager:suspiciouscheck:edit``
``remove``                DELETE ``/{ids}``           ``manager:suspiciouscheck:remove``
========================  ==========================  ==============================

``export`` 只补 ``createTimeStr``（**没有**字典翻译），其余照模板导出
``templates/export/carSuspiciousCheck.xlsx``。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.date_utils import YYYY_MM_DD_HH_MM_SS, parse_date_to_str
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_suspicious_check import CarSuspiciousCheck
from app.manager.service.car_suspicious_check_service import (
    CarSuspiciousCheckService,
    get_car_suspicious_check_service,
)

logger = logging.getLogger("app.api.manager.car_suspicious_check_controller")

router = APIRouter(prefix="/manager/suspiciouscheck", tags=["manager-suspicious-check"])

#: Java: ``com.ruoyi.web.controller.manager.CarSuspiciousCheckController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarSuspiciousCheckController"

#: Java: ``String url = "templates/export/carSuspiciousCheck.xlsx";``
EXPORT_TEMPLATE = "templates/export/carSuspiciousCheck.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

_SERVICE: Optional[CarSuspiciousCheckService] = None


def _service() -> CarSuspiciousCheckService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_suspicious_check_service()
    return _SERVICE


def reset_suspicious_check_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarSuspiciousCheck:
    """Java: 形参 ``CarSuspiciousCheck carSuspiciousCheck``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarSuspiciousCheck, request.query_params)


CarSuspiciousCheckParam = Annotated[CarSuspiciousCheck, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:suspiciouscheck:list")
def list_suspicious_checks(query: CarSuspiciousCheckParam) -> TableDataInfo:
    """查询可疑车辆核查列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的** —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:suspiciouscheck:export")
@log(title="可疑车辆人工核实", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarSuspiciousCheckParam) -> Response:
    """导出可疑车辆核查列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[CarSuspiciousCheck] = _service().select_list(query)
    for item in rows:
        if item.create_time is not None:
            item.create_time_str = parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.create_time)

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出可疑车辆核查失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取可疑车辆核查详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:suspiciouscheck:add")
@log(title="可疑车辆人工核实", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarSuspiciousCheck) -> AjaxResult:
    """新增可疑车辆核查. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:suspiciouscheck:edit")
@log(title="可疑车辆人工核实", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarSuspiciousCheck) -> AjaxResult:
    """修改可疑车辆核查. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:suspiciouscheck:remove")
@log(title="可疑车辆人工核实", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除可疑车辆核查. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "OCTET_STREAM_CONTENT_TYPE",
    "add",
    "edit",
    "export",
    "get_info",
    "list_suspicious_checks",
    "remove",
    "reset_suspicious_check_controller",
]
