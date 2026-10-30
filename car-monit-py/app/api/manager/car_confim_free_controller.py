"""确认补缴 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarConfimFreeController.java

**13** 个映射
------------
==========================  ====================================  ==========
Java                        Method / Path                         权限点
==========================  ====================================  ==========
``list``                    GET ``/list``                        **无**
``listCarNo``               GET ``/listCarNo``                   **无**
``listCount``               GET ``/listCount``                   **无**
``export``                  GET ``/export``                      **无**
``getInfo``                 GET ``/{id}``                        **无**
``add``                     POST ``""``                          **无**
``edit``                    PUT ``""``                           **无**
``remove``                  DELETE ``/{ids}``                    **无**
``getExceptIds``            GET ``/except/{exceptIds}``          **无**
``concernedList``           GET ``/concernedList``               **无**
``exportConcernedList``     GET ``/exportConcernedList``         **无**
``getCarStatics``           GET ``/carStatics``                  **无**
``exportCarStatics``        GET ``/exportCarStatics``            **无**
==========================  ====================================  ==========

（Java 引了 ``@PreAuthorize`` 但**一个都没用** —— 照抄，全部只要登录。）

三处必须照抄的地方
------------------
1. ``listCarNo`` / ``listCount`` 在车牌为空时把查询条件改成 ``"-1"``（查不到数据），
   而不是"不过滤"；
2. ``export`` 只翻 ``carType`` / ``carVehicle`` 两个字典，``escapedType`` **不动**；
   ``exportConcernedList`` 额外把逗号分隔的 ``escapedType`` 逐个翻成标签
   （未命中字典的值**丢弃**），再 ``deleteEnd`` 掉尾逗号；
3. 三个导出都是 Java 的 ``return null`` 风格：先渲染再设响应头，渲染抛异常时回
   **空 body + 无响应头**。

路由声明顺序与 Java **不同**：``GET /{id}`` 必须排在所有静态 ``GET`` 之后
（FastAPI 按声明顺序匹配，Spring 是精确路径优先）。
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
from app.common.utils.common_util import delete_end, is_blank, is_not_blank, is_null
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.common.utils.string_utils import split_regex
from app.framework.aspectj.log_aspect import log
from app.manager.domain.car_confim_free import CarConfimFree
from app.manager.domain.vo.car_confim_free_query_ro import CarConfimFreeQueryRo
from app.manager.service.car_confim_free_service import (
    CarConfimFreeService,
    get_car_confim_free_service,
)
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.car_confim_free_controller")

router = APIRouter(prefix="/manager/confimfree", tags=["manager-confim-free"])

#: Java: ``com.ruoyi.web.controller.manager.CarConfimFreeController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarConfimFreeController"

#: Java: ``String url = "templates/export/carConfirm.xlsx";``
EXPORT_TEMPLATE = "templates/export/carConfirm.xlsx"
#: Java: ``String url = "templates/export/concernedList.xlsx";``
EXPORT_CONCERNED_TEMPLATE = "templates/export/concernedList.xlsx"
#: Java: ``String url = "templates/export/carStatistics.xlsx";``
EXPORT_STATICS_TEMPLATE = "templates/export/carStatistics.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"
#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: ``listCarNo`` / ``listCount`` 在车牌为空时替换成的魔数
EMPTY_CAR_NO_PLACEHOLDER = "-1"

DICT_CAR_TYPE = "car_type"
DICT_CAR_VEHICLE = "car_vehicle"
DICT_ESCAPED_TYPE = "escaped_type"

_SERVICE: Optional[CarConfimFreeService] = None


def _service() -> CarConfimFreeService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_confim_free_service()
    return _SERVICE


def reset_car_confim_free_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarConfimFree:
    """Java: 形参 ``CarConfimFree carConfimFree``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarConfimFree, request.query_params)


CarConfimFreeParam = Annotated[CarConfimFree, Depends(_query)]


def _statistics_query(request: Request) -> CarConfimFreeQueryRo:
    """Java: 形参 ``CarConfimFreeQueryRo queryRo``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarConfimFreeQueryRo, request.query_params)


CarConfimFreeQueryRoParam = Annotated[CarConfimFreeQueryRo, Depends(_statistics_query)]


# --------------------------------------------------------------------------- 列表


@router.get("/list", response_model=None)
def list_confim_frees(query: CarConfimFreeParam) -> TableDataInfo:
    """查询确认补缴列表. Java: ``@GetMapping("/list")``.

    ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是**注释掉的** —— 照抄。
    """
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/listCarNo", response_model=None)
def list_car_no(query: CarConfimFreeParam) -> TableDataInfo:
    """根据车牌号查询确认补缴列表. Java: ``@GetMapping("/listCarNo")``."""
    start_page()
    if is_blank(query.car_no):
        query.car_no = EMPTY_CAR_NO_PLACEHOLDER
    return get_data_table(_service().select_list(query))


@router.get("/listCount", response_model=None)
def list_count(query: CarConfimFreeParam) -> AjaxResult:
    """按车牌汇总补缴次数与金额. Java: ``@GetMapping("/listCount")`` —— **不分页**."""
    if is_blank(query.car_no):
        query.car_no = EMPTY_CAR_NO_PLACEHOLDER
    return AjaxResult.success_data(_service().list_count(query))


# --------------------------------------------------------------------------- 导出


@router.get("/export", response_model=None)
@log(title="确认补缴", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarConfimFreeParam) -> Response:
    """导出确认补缴列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    rows: List[CarConfimFree] = _service().select_list(query)
    dict_service = get_dict_data_service()
    # 车型
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_TYPE)
    # 车种
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_VEHICLE)

    for item in rows:
        item.car_type = is_null(car_type_map.get(item.car_type))
        item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))

    return _export_excel(EXPORT_TEMPLATE, rows)


@router.get("/exportConcernedList", response_model=None)
def export_concerned_list(query: CarConfimFreeParam) -> Response:
    """待关注车辆导出. Java: ``@GetMapping(value = "/exportConcernedList")``."""
    rows: List[CarConfimFree] = _service().select_concerned_list(query)
    dict_service = get_dict_data_service()
    # 车型 / 车种 / 逃费类型
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_TYPE)
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_CAR_VEHICLE)
    escaped_type_map: Dict[str, str] = dict_service.select_dict_data_map(DICT_ESCAPED_TYPE)

    for item in rows:
        item.car_type = is_null(car_type_map.get(item.car_type))
        item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))
        # 需要循环 : 逃费类型（未命中字典的值丢弃）
        buss_name = ""
        buss_type = delete_end(item.escaped_type)
        if is_not_blank(buss_type):
            for buss_type_str in split_regex(buss_type, ","):
                if buss_type_str in escaped_type_map:
                    buss_name = buss_name + escaped_type_map[buss_type_str] + ","
        item.escaped_type = delete_end(buss_name)

    return _export_excel(EXPORT_CONCERNED_TEMPLATE, rows)


# --------------------------------------------------------------------------- 待关注


@router.get("/concernedList", response_model=None)
def concerned_list(query: CarConfimFreeParam) -> TableDataInfo:
    """待关注车辆. Java: ``@GetMapping("/concernedList")``."""
    start_page()
    return get_data_table(_service().select_concerned_list(query))


# --------------------------------------------------------------------------- 选择异常查询


@router.get("/except/{except_ids}", response_model=None)
def get_except_ids(except_ids: str) -> AjaxResult:
    """选择异常流水后回显补缴单. Java: ``@GetMapping(value = "/except/{exceptIds}")``.

    路径变量的名字改成 ``snake_case``（URL 不变），与本项目其它控制器一致。
    """
    return _service().select_by_except_ids(except_ids)


# --------------------------------------------------------------------------- PC 统计


@router.get("/carStatics", response_model=None)
def get_car_statics(query_ro: CarConfimFreeQueryRoParam) -> TableDataInfo:
    """pc 统计. Java: ``@GetMapping(value = "/carStatics")``."""
    start_page()
    return get_data_table(_service().get_pc_car_statistics(query_ro))


@router.get("/exportCarStatics", response_model=None)
def export_car_statics(query_ro: CarConfimFreeQueryRoParam) -> Response:
    """pc 统计导出. Java: ``@GetMapping(value = "/exportCarStatics")``."""
    rows = _service().get_pc_car_statistics(query_ro)
    return _export_excel(EXPORT_STATICS_TEMPLATE, rows)


# --------------------------------------------------------------------------- 详情 / 增删改


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取确认补缴详细信息. Java: ``@GetMapping(value = "/{id}")``.

    **必须**声明在所有静态 ``GET`` 路径之后（见模块 docstring）。
    """
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@log(title="确认补缴", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarConfimFree) -> AjaxResult:
    """新增确认补缴. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@log(title="确认补缴", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarConfimFree) -> AjaxResult:
    """修改确认补缴. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@log(title="确认补缴", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除确认补缴. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


def _export_excel(template: str, rows: Any) -> Response:
    """三处导出共用的 easypoi 模板渲染（失败时回空 body、无响应头）。"""
    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(template)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出确认补缴失败: %s", template, exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


__all__ = [
    "router",
    "EXPORT_TEMPLATE",
    "EXPORT_CONCERNED_TEMPLATE",
    "EXPORT_STATICS_TEMPLATE",
    "add",
    "concerned_list",
    "edit",
    "export",
    "export_car_statics",
    "export_concerned_list",
    "get_car_statics",
    "get_except_ids",
    "get_info",
    "list_car_no",
    "list_confim_frees",
    "list_count",
    "remove",
    "reset_car_confim_free_controller",
]
