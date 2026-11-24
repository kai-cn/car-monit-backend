"""基础-收费流水控制器 —— 上游取数 + 本地字典/缓存装饰 + easypoi 模板导出.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java

**3** 个映射
------------
=====================  ==============================  ==============================
Java                   Method / Path                   权限点
=====================  ==============================  ==============================
``list``               GET ``/list``                   ``base:feerecords:list``
``export``             GET ``/export``                 ``base:feerecords:list``（**同一个**）
``getInfo``            GET ``/{bigId}``                **无**（登录即可）
=====================  ==============================  ==============================

注意 ``export`` 复用的是 ``list`` 的权限点（Java 写的就是 ``base:feerecords:list``），
不是 ``base:feerecords:export``。

``list`` 的六条规则
-------------------
1. **先写查询日志**（``modelType="3"``、``menuPoint="1"``），`queryCondition` 是实体
   的 fastjson2 序列化（**省略 null**）。日志写失败会直接 500 —— 没有 try。
2. 缺省 ``pageNum=1`` / ``pageSize=10``。
3. ``sectionCodeStr`` 先 ``deleteEnd``（只削**一个**结尾逗号）；非空且含
   ``Constants.section_all``（``"all"``）时**整串清空**（不是挑出 ``all`` 删掉）。
4. **时间段是必填的**：``inApplyTime1`` 与 ``inApplyTime2`` 都非空才会调上游，否则
   直接返回空列表 + ``total=0``（``code`` 仍是 200）。
5. 上游返回后按 ``plateColor`` 给车牌加后缀、``feevehicletype``/``vehicleclass`` 查字典
   翻译、按 ``fee > 0`` 判定 ``chargeStatus``，然后把 ``fee`` **置空**（不回传给前端）。
6. ``sectionName`` / ``roadname`` 从 Redis ``SECTION_LIST`` 里按路段编码补齐
   （``CommonUtil.isNull`` 削空格后的键）。

``export`` 与 ``list`` 的差别
-----------------------------
* 日志的 ``menuPoint`` 是 ``"2"``；权限点仍是 ``list`` 的；
* 取数走 ``/base/feerecords/listToExport``（**裸数组**，不受分页影响）；
* 少一次 ``JSON.parseArray``（Forest 直接反序列化成 ``List<OdsLwzxsfsjFeeRecords01>``）；
* 多翻译一个 ``passstate``；
* 最后用 ``templates/export/feeRecords.xlsx`` 渲染，**字节直接写进响应**、
  Java 返回 ``null`` —— Python 侧返回 :class:`starlette.responses.Response`。
  模板路径 / 渲染出错时 Java 只 ``printStackTrace()``，于是回 **200 + 空 body + 无响应头**，
  这里同样处理。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Mapping, Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.base.domain.ods_lwzxsfsj_fee_records01 import OdsLwzxsfsjFeeRecords01
from app.base.service.forest.http_ods_lwzxsfsj_fee_records01_service import (
    HttpOdsLwzxsfsjFeeRecords01Service,
)
from app.base.util.cache_reader import read_section_list, section_by_code_map
from app.common.constant.constants import section_all
from app.common.constant.http_status import HttpStatus
from app.common.core.controller.base_controller import bind_query_params
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.common_util import delete_end, is_not_blank, is_null
from app.common.utils.json_utils import to_json_string_without_null
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.framework.web.service.permission_service import pre_authorize_permi
from app.manager.service.car_query_log_service import (
    CarQueryLogService,
    get_car_query_log_service,
)
from app.system.service.sys_dict_data_service import SysDictDataService, get_dict_data_service

logger = logging.getLogger("app.api.base.ods_lwzxsfsj_fee_records01_controller")

router = APIRouter(prefix="/base/feerecords", tags=["base-fee-records"])

#: Java: ``String url = "templates/export/feeRecords.xlsx";``
EXPORT_TEMPLATE = "templates/export/feeRecords.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)`` —— 模板里 ``{{$fe:entitylist ...}}`` 的名字。
ENTITY_LIST_KEY = "entitylist"

#: 字典类型（三个翻译 + 导出时多一个通行状态）。
DICT_PLATE_COLOR = "plate_color"
DICT_CAR_TYPE_OLD = "car_type_old"
DICT_CAR_VEHICLE_OLD = "car_vehicle_old"
DICT_PASSSTATE = "passstate"

#: ``chargeStatus`` 的两个取值。
CHARGE_STATUS_SUCCESS = "成功"
CHARGE_STATUS_FAILURE = "失败"

_COLLABORATORS: Optional[Dict[str, Any]] = None


def _collaborators() -> Dict[str, Any]:
    """Java 的四个 ``@Autowired`` / ``@Resource``（进程内单例）。"""
    global _COLLABORATORS
    if _COLLABORATORS is None:
        _COLLABORATORS = {
            "client": HttpOdsLwzxsfsjFeeRecords01Service(),
            "redis_cache": get_redis_cache(),
            "dict_service": get_dict_data_service(),
            "car_query_log_service": get_car_query_log_service(),
        }
    return _COLLABORATORS


def reset_fee_records_controller(
    client: Optional[HttpOdsLwzxsfsjFeeRecords01Service] = None,
    redis_cache: Optional[RedisCache] = None,
    dict_service: Optional[SysDictDataService] = None,
    car_query_log_service: Optional[CarQueryLogService] = None,
) -> None:
    """Test helper: drop / inject the cached collaborators."""
    global _COLLABORATORS
    if client is None and redis_cache is None and dict_service is None and car_query_log_service is None:
        _COLLABORATORS = None
        return
    current = dict(_collaborators())
    if client is not None:
        current["client"] = client
    if redis_cache is not None:
        current["redis_cache"] = redis_cache
    if dict_service is not None:
        current["dict_service"] = dict_service
    if car_query_log_service is not None:
        current["car_query_log_service"] = car_query_log_service
    _COLLABORATORS = current


def _query(request: Request) -> OdsLwzxsfsjFeeRecords01:
    """Java: 形参 ``OdsLwzxsfsjFeeRecords01 q``（无 ``@RequestBody``）—— query 绑定."""
    return bind_query_params(OdsLwzxsfsjFeeRecords01, request.query_params)


FeeRecordsParam = Annotated[OdsLwzxsfsjFeeRecords01, Depends(_query)]


def _normalize(query: OdsLwzxsfsjFeeRecords01) -> None:
    """``list`` / ``export`` 共用的三步预处理（缺省分页 + 路段串归一）。"""
    # 当前页面
    if query.page_num is None:
        query.page_num = 1
    # 分页大小
    if query.page_size is None:
        query.page_size = 10

    #  路段
    section_code_str = delete_end(query.section_code_str)
    if is_not_blank(section_code_str):
        if section_code_str.find(section_all) > -1:
            query.section_code_str = ""


def _require_time_range(query: OdsLwzxsfsjFeeRecords01) -> bool:
    """Java: ``isNotBlank(inApplyTime1) && isNotBlank(inApplyTime2)`` —— 时间段必填."""
    return is_not_blank(query.in_apply_time1) and is_not_blank(query.in_apply_time2)


def _decorate(
    rows: List[OdsLwzxsfsjFeeRecords01],
    dict_service: SysDictDataService,
    section_map: Mapping[str, Any],
    passstate: bool,
) -> None:
    """``list`` / ``export`` 里逐行装饰的那段 ``for`` 循环（``passstate`` 是唯一差别）."""
    # 车牌颜色
    plate_color_map = dict_service.select_dict_data_map(DICT_PLATE_COLOR)
    # 车型
    car_type_map = dict_service.select_dict_data_map(DICT_CAR_TYPE_OLD)
    # 车种
    car_vehicle_map = dict_service.select_dict_data_map(DICT_CAR_VEHICLE_OLD)
    # 通行状态（只有导出用）
    passstate_map = (
        dict_service.select_dict_data_map(DICT_PASSSTATE) if passstate else {}
    )

    for fee_records in rows:
        if is_not_blank(fee_records.plate_color):
            plate_color_value = is_null(plate_color_map.get(fee_records.plate_color))
            if is_not_blank(plate_color_value):
                fee_records.vehicleplate = (
                    is_null(fee_records.vehicleplate) + "_" + plate_color_value
                )

        if is_not_blank(fee_records.feevehicletype):
            fee_records.feevehicletype = is_null(
                car_type_map.get(is_null(fee_records.feevehicletype))
            )

        if is_not_blank(fee_records.vehicleclass):
            fee_records.vehicleclass = is_null(
                car_vehicle_map.get(is_null(fee_records.vehicleclass))
            )

        fee = fee_records.fee
        if fee is not None and fee > 0:  # Java: BigDecimal.compareTo(ZERO) > 0
            fee_records.charge_status = CHARGE_STATUS_SUCCESS
        else:
            fee_records.charge_status = CHARGE_STATUS_FAILURE
        fee_records.fee = None

        section_code = is_null(fee_records.section_code_str)
        if is_not_blank(section_code):
            if section_code in section_map:
                section = section_map[section_code]
                fee_records.section_name = section.section_name
                fee_records.roadname = section.road_name

        if passstate:
            fee_records.passstate = is_null(passstate_map.get(fee_records.passstate))


@router.get("/list", response_model=None)
@pre_authorize_permi("base:feerecords:list")
def list_fee_records(query: FeeRecordsParam) -> TableDataInfo:
    """查询基础-收费流水列表. Java: ``@GetMapping("/list")``."""
    collaborators = _collaborators()

    # 插入查询日志
    collaborators["car_query_log_service"].query_log(
        to_json_string_without_null(query), "3", "1"
    )

    _normalize(query)

    rsp_data = TableDataInfo()
    rows: List[OdsLwzxsfsjFeeRecords01] = []
    total = 0

    # 时间段必填
    if _require_time_range(query):
        table_data_info = collaborators["client"].get_ods_lwzxsfsj_fee_records01_page(query)
        upstream_rows = table_data_info.get_rows()
        if upstream_rows is not None and len(upstream_rows) > 0:
            # Java: JSON.parseArray(JSON.toJSONString(rows), OdsLwzxsfsjFeeRecords01.class)
            rows = [OdsLwzxsfsjFeeRecords01.model_validate(item) for item in upstream_rows]
            if rows:
                section_map = section_by_code_map(
                    read_section_list(collaborators["redis_cache"])
                )
                _decorate(rows, collaborators["dict_service"], section_map, passstate=False)
            total = table_data_info.get_total()

    rsp_data.set_code(HttpStatus.SUCCESS)
    rsp_data.set_msg("查询成功")
    rsp_data.set_rows(rows)
    rsp_data.set_total(total)
    return rsp_data


@router.get("/export", response_model=None)
@pre_authorize_permi("base:feerecords:list")
def export(query: FeeRecordsParam) -> Response:
    """导出基础-收费流水列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    collaborators = _collaborators()

    # 插入查询日志
    collaborators["car_query_log_service"].query_log(
        to_json_string_without_null(query), "3", "2"
    )

    _normalize(query)

    rows: List[OdsLwzxsfsjFeeRecords01] = []
    # 时间段必填
    if _require_time_range(query):
        payload = collaborators["client"].get_ods_lwzxsfsj_fee_records01_list_to_export(query)
        # Forest 直接把裸数组反序列化成 List<OdsLwzxsfsjFeeRecords01>
        rows = [OdsLwzxsfsjFeeRecords01.model_validate(item) for item in payload]

    if rows:
        section_map = section_by_code_map(read_section_list(collaborators["redis_cache"]))
        _decorate(rows, collaborators["dict_service"], section_map, passstate=True)

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出收费流水失败", exc_info=True)
        # 响应头在 Java 里是渲染成功之后才设的，所以失败时是"200 + 空 body + 无响应头"
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


@router.get("/{big_id}", response_model=None)
def get_info(big_id: str) -> AjaxResult:
    """获取基础-收费流水详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    row = _collaborators()["client"].select_ods_lwzxsfsj_fee_records01_by_id(big_id)
    if isinstance(row, dict):
        for field in ("plateColorMark", "plateColorName", "chargeStatus", "entimeStr", "receivetimeStr", "sectionName"):
            row.setdefault(field, None)
    return AjaxResult.success_data(row)


__all__ = [
    "CHARGE_STATUS_FAILURE",
    "CHARGE_STATUS_SUCCESS",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "FeeRecordsParam",
    "OCTET_STREAM_CONTENT_TYPE",
    "export",
    "get_info",
    "list_fee_records",
    "reset_fee_records_controller",
    "router",
]
