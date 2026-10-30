"""拆分记录 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSplitRecordController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:splitrecord:list``
``export``                GET ``/export``             ``manager:splitrecord:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:splitrecord:add``
``edit``                  PUT ``""``                  ``manager:splitrecord:edit``
``remove``                DELETE ``/{ids}``           ``manager:splitrecord:remove``
========================  ==========================  ==============================

``export`` 里有一个**照抄不改**的疑似 bug
-----------------------------------------
Java 原文是::

    dp.setPassType(CommonUtil.isNull(passTypeMap.get(dp.getCarVehicle())));

—— 用 ``carVehicle`` 的值去查 ``pass_type`` 字典（不是 ``passType``）。翻译后的
``passType`` 因此几乎总是 ``null``。这是现网行为，修掉会改变导出结果，所以保留，
只在注释里标注。
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
from app.common.utils.common_util import is_null
from app.common.utils.date_utils import YYYY_MM_DD_HH_MM_SS, parse_date_to_str
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_split_record import CarSplitRecord
from app.manager.service.car_split_record_service import (
    CarSplitRecordService,
    get_car_split_record_service,
)
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.car_split_record_controller")

router = APIRouter(prefix="/manager/splitrecord", tags=["manager-split-record"])

#: Java: ``com.ruoyi.web.controller.manager.CarSplitRecordController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarSplitRecordController"

#: Java: ``String url = "templates/export/carSplitRecord.xlsx";``
EXPORT_TEMPLATE = "templates/export/carSplitRecord.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: Java: ``sysDictDataService.selectDictDataMap("car_type")``
CAR_TYPE_DICT = "car_type"

#: Java: ``sysDictDataService.selectDictDataMap("car_vehicle")``
CAR_VEHICLE_DICT = "car_vehicle"

#: Java: ``sysDictDataService.selectDictDataMap("pass_type")``
PASS_TYPE_DICT = "pass_type"

_SERVICE: Optional[CarSplitRecordService] = None


def _service() -> CarSplitRecordService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_split_record_service()
    return _SERVICE


def reset_split_record_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarSplitRecord:
    """Java: 形参 ``CarSplitRecord carSplitRecord``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarSplitRecord, request.query_params)


CarSplitRecordParam = Annotated[CarSplitRecord, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:splitrecord:list")
def list_split_records(query: CarSplitRecordParam) -> TableDataInfo:
    """查询拆分记录列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的** —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:splitrecord:export")
@log(title="拆分流水", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarSplitRecordParam) -> Response:
    """导出拆分记录列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[CarSplitRecord] = _service().select_list(query)
    dict_service = get_dict_data_service()
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(CAR_TYPE_DICT)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(CAR_VEHICLE_DICT)
    pass_type_map: Dict[str, str] = dict_service.select_dict_data_map(PASS_TYPE_DICT)
    for item in rows:
        if item.create_time is not None:
            item.create_time_str = parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.create_time)
        item.car_type = is_null(car_type_map.get(item.car_type))
        item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))
        # Java 原文用 carVehicle 的值查 pass_type 字典 —— 照抄，不要"修正"
        item.pass_type = is_null(pass_type_map.get(item.car_vehicle))

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出拆分记录失败", exc_info=True)
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
    """获取拆分记录详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:splitrecord:add")
@log(title="拆分流水", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarSplitRecord) -> AjaxResult:
    """新增拆分记录. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:splitrecord:edit")
@log(title="拆分流水", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarSplitRecord) -> AjaxResult:
    """修改拆分记录. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:splitrecord:remove")
@log(title="拆分流水", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除拆分记录. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "CAR_TYPE_DICT",
    "CAR_VEHICLE_DICT",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "OCTET_STREAM_CONTENT_TYPE",
    "PASS_TYPE_DICT",
    "add",
    "edit",
    "export",
    "get_info",
    "list_split_records",
    "remove",
    "reset_split_record_controller",
]
