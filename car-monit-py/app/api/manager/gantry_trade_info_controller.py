"""门架交易查询 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryTradeInfoController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:gantrytrade:list``
``export``                GET ``/export``             ``manager:gantrytrade:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:gantrytrade:add``
``edit``                  PUT ``""``                  ``manager:gantrytrade:edit``
``remove``                DELETE ``/{ids}``           ``manager:gantrytrade:remove``
========================  ==========================  ==============================

``export`` 与 :mod:`app.api.manager.gantry_car_controller` 逐字同构，只有模板
文件名（``gantryTrade.xlsx``）和实体/权限不同：``createTimeStr`` 在 ``if`` 里，
``carType`` / ``carVehicle`` 的字典翻译在 ``if`` 外。
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
from app.manager.domain.gantry_trade_info import GantryTradeInfo
from app.manager.service.gantry_trade_info_service import (
    GantryTradeInfoService,
    get_gantry_trade_info_service,
)
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.gantry_trade_info_controller")

router = APIRouter(prefix="/manager/gantrytrade", tags=["manager-gantry-trade"])

#: Java: ``com.ruoyi.web.controller.manager.GantryTradeInfoController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.GantryTradeInfoController"

#: Java: ``String url = "templates/export/gantryTrade.xlsx";``
EXPORT_TEMPLATE = "templates/export/gantryTrade.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: Java: ``sysDictDataService.selectDictDataMap("car_type")``
CAR_TYPE_DICT = "car_type"

#: Java: ``sysDictDataService.selectDictDataMap("car_vehicle")``
CAR_VEHICLE_DICT = "car_vehicle"

_SERVICE: Optional[GantryTradeInfoService] = None


def _service() -> GantryTradeInfoService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_gantry_trade_info_service()
    return _SERVICE


def reset_gantry_trade_info_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> GantryTradeInfo:
    """Java: 形参 ``GantryTradeInfo gantryTradeInfo``（**没有** ``@RequestBody``）."""
    return bind_query_params(GantryTradeInfo, request.query_params)


GantryTradeInfoParam = Annotated[GantryTradeInfo, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:gantrytrade:list")
def list_gantry_trade_infos(query: GantryTradeInfoParam) -> TableDataInfo:
    """查询门架交易查询列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的** —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:gantrytrade:export")
@log(title="门架交易查询", business_type=BusinessType.EXPORT, java_method="export")
def export(query: GantryTradeInfoParam) -> Response:
    """导出门架交易查询列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[GantryTradeInfo] = _service().select_list(query)
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
        logger.error("导出门架交易查询失败", exc_info=True)
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
    """获取门架交易查询详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:gantrytrade:add")
@log(title="门架交易查询", business_type=BusinessType.INSERT, java_method="add")
def add(entity: GantryTradeInfo) -> AjaxResult:
    """新增门架交易查询. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:gantrytrade:edit")
@log(title="门架交易查询", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: GantryTradeInfo) -> AjaxResult:
    """修改门架交易查询. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:gantrytrade:remove")
@log(title="门架交易查询", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除门架交易查询. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
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
    "list_gantry_trade_infos",
    "remove",
    "reset_gantry_trade_info_controller",
]
