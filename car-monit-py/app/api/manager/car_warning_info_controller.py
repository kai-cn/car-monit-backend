"""预警车辆 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningInfoController.java

**6** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               **注释掉了**（无权限校验）
``export``                GET ``/export``             ``manager:carwarning:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``manager:carwarning:add``
``edit``                  PUT ``""``                  ``manager:carwarning:edit``
``remove``                DELETE ``/{ids}``           ``manager:carwarning:remove``
========================  ==========================  ==============================

``list`` 的 ``@PreAuthorize`` 在 Java 里是**整行注释**的，所以这里也没有
``pre_authorize_permi`` —— 不要"顺手补上"。

``list`` 与 ``export`` 的查询参数规整
------------------------------------
两个方法各抄了一遍完全相同的 70 行（``flag`` / ``flagTime`` / ``sectionCode`` /
``code`` / ``type`` → ``sectionCodeList`` / ``codeList``）。这里抽成
:func:`_prepare_query`，行为逐条对齐：

* ``queryRante`` 非空即为 ``flag``，否则 ``curDate``；两个分支都写 ``flagTime =
  yyyyMMdd``。
* ``sectionCode`` 走 :func:`delete_end`（**只削一个**逗号）；含 ``"all"`` 时整段忽略，
  否则按 ``,`` 切分成 ``sectionCodeList``，然后把 ``sectionCode`` 置空串。
* ``code`` 同理切分成 ``codeList``；``code`` 为空时按 ``type`` 1/2/3 写入
  ``StationCapture`` / ``GantryCapture`` / ``ServiceAreaCapture`` 单元素列表
  （``type`` 为其它值时写入 ``""``）。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.common.constant import constants as Constants
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
from app.common.utils.date_utils import YYYY_MM_DD_HH_MM_SS, parse_date_to_str
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.common.utils.string_utils import split_regex
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.domain.car_warning_info import CarWarningInfo
from app.manager.service.car_warning_info_service import (
    CarWarningInfoService,
    get_car_warning_info_service,
)
from app.system.service.sys_dict_data_service import get_dict_data_service

logger = logging.getLogger("app.api.manager.car_warning_info_controller")

router = APIRouter(prefix="/manager/carwarning", tags=["manager-warning-info"])

#: Java: ``com.ruoyi.web.controller.manager.CarWarningInfoController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.manager.CarWarningInfoController"

#: Java: ``String url = "templates/export/carWarningInfo.xlsx";``
EXPORT_TEMPLATE = "templates/export/carWarningInfo.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: Java: ``sysDictDataService.selectDictDataMap("plate_color")``
PLATE_COLOR_DICT = "plate_color"

#: Java: ``sysDictDataService.selectDictDataMap("car_type")``
CAR_TYPE_DICT = "car_type"

#: Java: ``sysDictDataService.selectDictDataMap("car_vehicle")``
CAR_VEHICLE_DICT = "car_vehicle"

#: Java: ``sysDictDataService.selectDictDataMap("escaped_type")``
ESCAPED_TYPE_DICT = "escaped_type"

#: Java: ``SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");``
FLAG_TIME_PATTERN = "%Y%m%d"

#: Java: ``flag = "curDate"; // 默认查询当天并且车辆为``
DEFAULT_FLAG = "curDate"

#: Java: ``flag.equals("histhory")`` —— 原文就是这么拼的
HISTORY_FLAG = "histhory"

_SERVICE: Optional[CarWarningInfoService] = None


def _service() -> CarWarningInfoService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_warning_info_service()
    return _SERVICE


def reset_warning_info_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarWarningInfo:
    """Java: 形参 ``CarWarningInfo carWarningInfo``（**没有** ``@RequestBody``）."""
    return bind_query_params(CarWarningInfo, request.query_params)


CarWarningInfoParam = Annotated[CarWarningInfo, Depends(_query)]


def _prepare_query(query: CarWarningInfo) -> None:
    """Java: ``list`` / ``export`` 开头那段一模一样的查询参数规整（原地改 ``query``）."""
    flag = ""
    if is_not_blank(query.query_rante):
        flag = query.query_rante
    if is_blank(flag):
        flag = DEFAULT_FLAG
    query.flag = flag

    # Java: SimpleDateFormat("yyyyMMdd").format(new Date())
    formatted_date = datetime.now().strftime(FLAG_TIME_PATTERN)
    if flag == DEFAULT_FLAG:
        query.flag_time = formatted_date
    elif flag == HISTORY_FLAG:
        query.flag_time = formatted_date

    # 路段
    section_code = delete_end(query.section_code)
    if is_not_blank(section_code):
        if section_code.find(Constants.section_all) > -1:
            pass
        else:
            query.section_code_list = split_regex(section_code, ",")
        query.section_code = ""  # 查询范围

    # 选择对象
    code = delete_end(query.code)
    if is_not_blank(code):
        # 服务区 收费站
        query.code_list = split_regex(code, ",")
        query.code = ""  # 查询范围
    else:
        obj_type = is_null(query.type)
        if is_not_blank(obj_type):
            captured = ""
            if obj_type == "1":
                captured = Constants.STATION_CAPTURE
            elif obj_type == "2":
                captured = Constants.GANTRY_CAPTURE
            elif obj_type == "3":
                captured = Constants.SERVICE_AREA_CAPTURE
            query.code_list = [captured]


@router.get("/list", response_model=None)
def list_warning_infos(query: CarWarningInfoParam) -> TableDataInfo:
    """查询预警车辆列表. Java: ``@GetMapping("/list")``.

    Java 的 ``@PreAuthorize("@ss.hasPermi('manager:carwarning:list')")`` 是整行注释，
    所以这里**不加** ``pre_authorize_permi``。

    ``setTenantId(SecurityUtils.getTenantId())`` 同样被注释掉 —— 照抄。
    """
    start_page()
    _prepare_query(query)
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("manager:carwarning:export")
@log(title="预警车辆", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarWarningInfoParam) -> Response:
    """导出预警车辆列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    dict_service = get_dict_data_service()
    # 车牌颜色
    plate_color_map: Dict[str, str] = dict_service.select_dict_data_map(PLATE_COLOR_DICT)
    # 车型
    car_type_map: Dict[str, str] = dict_service.select_dict_data_map(CAR_TYPE_DICT)
    # 车种
    car_vehicle_map: Dict[str, str] = dict_service.select_dict_data_map(CAR_VEHICLE_DICT)
    # 逃费类型
    escaped_type_map: Dict[str, str] = dict_service.select_dict_data_map(ESCAPED_TYPE_DICT)

    _prepare_query(query)
    rows: List[CarWarningInfo] = _service().select_list(query)

    for item in rows:
        if item.gantry_time is not None:
            item.gantry_time_str = parse_date_to_str(
                YYYY_MM_DD_HH_MM_SS, item.gantry_time
            )
        if item.create_time is not None:
            item.create_time_str = parse_date_to_str(
                YYYY_MM_DD_HH_MM_SS, item.create_time
            )
        if item.in_time is not None:
            item.in_time_str = parse_date_to_str(YYYY_MM_DD_HH_MM_SS, item.in_time)
        if item.next_pass_time is not None:
            item.next_pass_time_str = parse_date_to_str(
                YYYY_MM_DD_HH_MM_SS, item.next_pass_time
            )

        item.plate_color = is_null(plate_color_map.get(item.plate_color))
        item.car_type = is_null(car_type_map.get(item.car_type))
        item.car_vehicle = is_null(car_vehicle_map.get(item.car_vehicle))

        # 需要循环 : 逃费类型
        buss_name = ""
        buss_type = delete_end(item.escaped_type)
        if is_not_blank(buss_type):
            for token in split_regex(buss_type, ","):
                if token in escaped_type_map:
                    buss_name = buss_name + escaped_type_map[token] + ","
        item.escaped_type = delete_end(buss_name)

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出预警车辆失败", exc_info=True)
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
    """获取预警车辆详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    row = _service().select_by_id(id) if hasattr(_service(), "select_by_id") else _service().get_by_id(id)
    if isinstance(row, dict):
        row.setdefault("plateColorMark", None)
        row.setdefault("plateColorName", None)
    return AjaxResult.success_data(row)


@router.post("", response_model=None)
@pre_authorize_permi("manager:carwarning:add")
@log(title="预警车辆", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarWarningInfo) -> AjaxResult:
    """新增预警车辆. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("manager:carwarning:edit")
@log(title="预警车辆", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarWarningInfo) -> AjaxResult:
    """修改预警车辆. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("manager:carwarning:remove")
@log(title="预警车辆", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除预警车辆. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "CAR_TYPE_DICT",
    "CAR_VEHICLE_DICT",
    "DEFAULT_FLAG",
    "ENTITY_LIST_KEY",
    "ESCAPED_TYPE_DICT",
    "EXPORT_TEMPLATE",
    "FLAG_TIME_PATTERN",
    "HISTORY_FLAG",
    "OCTET_STREAM_CONTENT_TYPE",
    "PLATE_COLOR_DICT",
    "add",
    "edit",
    "export",
    "get_info",
    "list_warning_infos",
    "remove",
    "reset_warning_info_controller",
]
