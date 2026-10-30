"""车俩白名单 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWhiteInfoController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``manager:whiteinfo:list``
``export``                GET ``/export``             ``manager:whiteinfo:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:whiteinfo:add``
``edit``                  PUT ``""``                  ``manager:whiteinfo:edit``
``remove``                DELETE ``/{ids}``           ``manager:whiteinfo:remove``
========================  ==========================  ==============================

``export`` 用 ``CommonUtil.isNull(map.get(x))`` 翻译三个字典列 —— 查不到映射时写
**空串**（不是 ``null``、也不是原值）。模板 ``templates/export/carWhiteInfo.xlsx``。
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
from app.manager.domain.car_white_info import CarWhiteInfo
from app.manager.service.car_white_info_service import (
    CarWhiteInfoService,
    get_car_white_info_service,
)
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.car_white_info_controller")

router = APIRouter(prefix="/manager/whiteinfo", tags=["manager-white-info"])

#: Java: ``com.ruoyi.web.controller.manager.CarWhiteInfoController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarWhiteInfoController"

#: Java: ``String url = "templates/export/carWhiteInfo.xlsx";``
EXPORT_TEMPLATE = "templates/export/carWhiteInfo.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: 三个字典类型 —— 顺序与 Java 一致。
PLATE_COLOR_DICT = "plate_color"
CAR_TYPE_DICT = "car_type"
CAR_VEHICLE_DICT = "car_vehicle"

_SERVICE: Optional[CarWhiteInfoService] = None


def _service() -> CarWhiteInfoService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_white_info_service()
    return _SERVICE


def reset_white_info_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarWhiteInfo:
    """Java: 形参 ``CarWhiteInfo carWhiteInfo``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarWhiteInfo, request.query_params)


WhiteInfoParam = Annotated[CarWhiteInfo, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:whiteinfo:list")
def list_white_infos(query: WhiteInfoParam) -> TableDataInfo:
    """查询车俩白名单列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:whiteinfo:export")
@log(title="车俩白名单", business_type=BusinessType.EXPORT, java_method="export")
def export(query: WhiteInfoParam) -> Response:
    """导出车俩白名单列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[CarWhiteInfo] = _service().select_list(query)
    dict_service = get_dict_data_service()
    plate_color_map: Dict[str, str] = dict_service.select_dict_data_map(PLATE_COLOR_DICT)
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(CAR_TYPE_DICT)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(CAR_VEHICLE_DICT)

    for item in rows:
        if item.create_time is not None:
            item.create_time_str = parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.create_time)
        # Java: dp.setPlateColor(CommonUtil.isNull(plateColorMap.get(...)))
        item.plate_color = is_null(plate_color_map.get(item.plate_color))
        item.car_type = is_null(car_type_map.get(item.car_type))
        item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出车俩白名单失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            "Content-Disposition": "attachment",
        },
    )


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002
    """获取车俩白名单详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("manager:whiteinfo:add")
@log(title="车俩白名单", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarWhiteInfo) -> AjaxResult:
    """新增车俩白名单. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:whiteinfo:edit")
@log(title="车俩白名单", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarWhiteInfo) -> AjaxResult:
    """修改车俩白名单. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:whiteinfo:remove")
@log(title="车俩白名单", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除车俩白名单. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
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
    "list_white_infos",
    "remove",
    "reset_white_info_controller",
]
