"""收费流水 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarFeeRecordController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:feerecord:list``
``export``                GET ``/export``             ``manager:feerecord:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:feerecord:add``
``edit``                  PUT ``""``                  ``manager:feerecord:edit``
``remove``                DELETE ``/{ids}``           ``manager:feerecord:remove``
========================  ==========================  ==============================

与 ``CarWarningRule`` 的差别只在导出方式：这里走
``ExcelUtil<CarFeeRecord>(CarFeeRecord.class).exportExcel(list, "收费流水数据")``
—— **列由 ``@Excel`` 注解决定**，文件写到 ``{ruoyi.profile}/download/``，
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
from app.manager.domain.car_fee_record import CarFeeRecord
from app.manager.service.car_fee_record_service import (
    CarFeeRecordService,
    get_car_fee_record_service,
)

router = APIRouter(prefix="/manager/feerecord", tags=["manager-fee-record"])

#: Java: ``com.ruoyi.web.controller.manager.CarFeeRecordController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarFeeRecordController"

#: Java: ``util.exportExcel(list, "收费流水数据")`` —— sheet 名与文件名前缀。
EXPORT_SHEET_NAME = "收费流水数据"

_SERVICE: Optional[CarFeeRecordService] = None


def _service() -> CarFeeRecordService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_fee_record_service()
    return _SERVICE


def reset_fee_record_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarFeeRecord:
    """Java: 形参 ``CarFeeRecord carFeeRecord``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarFeeRecord, request.query_params)


FeeRecordParam = Annotated[CarFeeRecord, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:feerecord:list")
def list_fee_records(query: FeeRecordParam) -> TableDataInfo:
    """查询收费流水列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:feerecord:export")
@log(title="收费流水", business_type=BusinessType.EXPORT, java_method="export")
def export(query: FeeRecordParam) -> AjaxResult:
    """导出收费流水列表. Java: ``@GetMapping("/export")``."""
    rows = _service().select_list(query)
    return ExcelUtil(CarFeeRecord).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002
    """获取收费流水详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:feerecord:add")
@log(title="收费流水", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarFeeRecord) -> AjaxResult:
    """新增收费流水. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:feerecord:edit")
@log(title="收费流水", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarFeeRecord) -> AjaxResult:
    """修改收费流水. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:feerecord:remove")
@log(title="收费流水", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除收费流水. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "get_info",
    "list_fee_records",
    "remove",
    "reset_fee_record_controller",
]
