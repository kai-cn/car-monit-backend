"""门架拍识查询 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryCarController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:gantrycar:list``
``export``                GET ``/export``             ``manager:gantrycar:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:gantrycar:add``
``edit``                  PUT ``""``                  ``manager:gantrycar:edit``
``remove``                DELETE ``/{ids}``           ``manager:gantrycar:remove``
========================  ==========================  ==============================

``export`` 的三个细节
---------------------
1. 数据源是数据库（``selectGantryCarList``），Java 没有 ``startPage()`` —— 导出全量。
2. ``createTimeStr`` **只在** ``createTime != null`` 时赋值（模板里那一列靠它）；
   ``carType`` / ``carVehicle`` 的字典翻译**不在** ``if`` 里面，所以对每一行都执行
   （字典查不到时 ``CommonUtil.isNull`` 返回 ``null``）。
3. 模板 ``templates/export/gantryCar.xlsx`` 渲染完把字节写进响应，Java ``return null``。
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
from app.manager.domain.gantry_car import GantryCar
from app.manager.service.gantry_car_service import GantryCarService, get_gantry_car_service
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.gantry_car_controller")

router = APIRouter(prefix="/manager/gantrycar", tags=["manager-gantry-car"])

#: Java: ``com.ruoyi.web.controller.manager.GantryCarController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.GantryCarController"

#: Java: ``String url = "templates/export/gantryCar.xlsx";``
EXPORT_TEMPLATE = "templates/export/gantryCar.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: Java: ``sysDictDataService.selectDictDataMap("car_type")``
CAR_TYPE_DICT = "car_type"

#: Java: ``sysDictDataService.selectDictDataMap("car_vehicle")``
CAR_VEHICLE_DICT = "car_vehicle"

_SERVICE: Optional[GantryCarService] = None


def _service() -> GantryCarService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_gantry_car_service()
    return _SERVICE


def reset_gantry_car_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> GantryCar:
    """Java: 形参 ``GantryCar gantryCar``（**没有** ``@RequestBody``）."""
    return bind_query_params(GantryCar, request.query_params)


GantryCarParam = Annotated[GantryCar, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:gantrycar:list")
def list_gantry_cars(query: GantryCarParam) -> TableDataInfo:
    """查询门架拍识查询列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的**，
    所以跨租户可见 —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:gantrycar:export")
@log(title="门架拍识查询", business_type=BusinessType.EXPORT, java_method="export")
def export(query: GantryCarParam) -> Response:
    """导出门架拍识查询列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[GantryCar] = _service().select_list(query)
    dict_service = get_dict_data_service()
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(CAR_TYPE_DICT)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(CAR_VEHICLE_DICT)
    for item in rows:
        if item.create_time is not None:
            item.create_time_str = parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.create_time)
        item.car_type = is_null(car_type_map.get(item.car_type))
        item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出门架拍识查询失败", exc_info=True)
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
    """获取门架拍识查询详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:gantrycar:add")
@log(title="门架拍识查询", business_type=BusinessType.INSERT, java_method="add")
def add(entity: GantryCar) -> AjaxResult:
    """新增门架拍识查询. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:gantrycar:edit")
@log(title="门架拍识查询", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: GantryCar) -> AjaxResult:
    """修改门架拍识查询. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:gantrycar:remove")
@log(title="门架拍识查询", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除门架拍识查询. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "CAR_TYPE_DICT",
    "CAR_VEHICLE_DICT",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "OCTET_STREAM_CONTENT_TYPE",
    "add",
    "edit",
    "export",
    "get_info",
    "list_gantry_cars",
    "remove",
    "reset_gantry_car_controller",
]
