"""门架抓拍流水控制器 —— 跨月分表查询（本地库）优先，Forest 代理兜底.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java

**4** 个映射
------------
=====================  ==============================  ==================================
Java                   Method / Path                   权限点
=====================  ==============================  ==================================
``list``               GET ``/list``                   ``base:snapshotflow:list``
``export``             GET ``/export``                 ``base:snapshotflow:list``（**同一个**）
``getInfo``            GET ``/{bigId}``                **无**（登录即可）
``getEarliestSnapshottime``  GET ``/earliest-time``    **无**（登录即可）
=====================  ==============================  ==================================

``list`` 的两条分支
-------------------
* **时间段齐**（``applyTime1`` 与 ``applyTime2`` 都非空）-> 走
  :class:`~app.base.service.enhanced.snapshot_flow_enhanced_service.SnapshotFlowEnhancedService`
  （本地 MySQL 的 ``ods_rt_szdn_snapshot_flow_yyyyMM`` 分表）；
* **否则** -> 直接回空列表 + ``total=0``（``code 200`` / ``msg 查询成功``），
  **不**查上游、也**不**查本地。

降级分支是死代码
----------------
``queryPage`` 自己 ``catch (Exception)`` 后返回空表，**从不抛异常**，所以控制器里
"失败就降级到 Forest 代理"的那段 ``catch`` 永远不会执行。这里按原样保留结构
（一旦哪天 ``queryPage`` 改成会抛，行为就与 Java 对齐）。

``export`` 的 ``directionStr``
------------------------------
.. code-block:: java

    list.stream().forEach(dp -> {
        dp.setDirectionStr(directionMap.get(dp.getDirection().toString()));
    });

``dp.getDirection()`` 是 ``Integer``：为 ``null`` 时 ``.toString()`` **NPE**（``code 500``），
翻译不到时得到 ``null``（照抄，不兜底成空串）。注意这里用的是 ``for`` 而不是
``for (X x : list)``，所以列表为空也不会跳过翻译表查询（字典照样查一次）。

``/{bigId}`` 与 ``/earliest-time`` 的路由顺序
---------------------------------------------
``/earliest-time`` 是字面量，必须**先**注册 —— FastAPI 按注册顺序匹配，``/{big_id}``
会把 ``earliest-time`` 当成 ``bigId``（Spring 的 ``AntPathMatcher`` 优先字面量，不受顺序影响）。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.base.domain.ods_rt_szdn_snapshot_flow_addcode import OdsRtSzdnSnapshotFlowAddcode
from app.base.service.enhanced.snapshot_flow_enhanced_service import (
    SnapshotFlowEnhancedService,
    get_snapshot_flow_enhanced_service,
)
from app.base.service.forest.http_ods_rt_szdn_snapshot_flow_addcode_service import (
    HttpOdsRtSzdnSnapshotFlowAddcodeService,
)
from app.common.constant.constants import section_all
from app.common.constant.http_status import HttpStatus
from app.common.core.controller.base_controller import bind_query_params
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.utils.common_util import delete_end, is_not_blank
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

logger = logging.getLogger("app.api.base.ods_rt_szdn_snapshot_flow_addcode_controller")

router = APIRouter(prefix="/base/snapshotflow", tags=["base-snapshot-flow"])

#: Java: ``String url = "templates/export/snapshotFlow.xlsx";``
EXPORT_TEMPLATE = "templates/export/snapshotFlow.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: 方向字典类型。
DICT_DIRECTION = "direction"

#: ``getEarliestSnapshottime`` 无数据时的文案。
NO_DATA_MESSAGE = "暂无数据"

_COLLABORATORS: Optional[Dict[str, Any]] = None


def _collaborators() -> Dict[str, Any]:
    """Java 的四个 ``@Autowired`` / ``@Resource``（进程内单例）。"""
    global _COLLABORATORS
    if _COLLABORATORS is None:
        _COLLABORATORS = {
            "client": HttpOdsRtSzdnSnapshotFlowAddcodeService(),
            "dict_service": get_dict_data_service(),
            "car_query_log_service": get_car_query_log_service(),
            "enhanced_service": get_snapshot_flow_enhanced_service(),
        }
    return _COLLABORATORS


def reset_snapshot_flow_controller(
    client: Optional[HttpOdsRtSzdnSnapshotFlowAddcodeService] = None,
    dict_service: Optional[SysDictDataService] = None,
    car_query_log_service: Optional[CarQueryLogService] = None,
    enhanced_service: Optional[SnapshotFlowEnhancedService] = None,
) -> None:
    """Test helper: drop / inject the cached collaborators."""
    global _COLLABORATORS
    if (
        client is None
        and dict_service is None
        and car_query_log_service is None
        and enhanced_service is None
    ):
        _COLLABORATORS = None
        return
    current = dict(_collaborators())
    if client is not None:
        current["client"] = client
    if dict_service is not None:
        current["dict_service"] = dict_service
    if car_query_log_service is not None:
        current["car_query_log_service"] = car_query_log_service
    if enhanced_service is not None:
        current["enhanced_service"] = enhanced_service
    _COLLABORATORS = current


def _query(request: Request) -> OdsRtSzdnSnapshotFlowAddcode:
    """Java: 形参 ``OdsRtSzdnSnapshotFlowAddcode q``（无 ``@RequestBody``）—— query 绑定."""
    return bind_query_params(OdsRtSzdnSnapshotFlowAddcode, request.query_params)


SnapshotFlowParam = Annotated[OdsRtSzdnSnapshotFlowAddcode, Depends(_query)]


def _normalize(query: OdsRtSzdnSnapshotFlowAddcode) -> None:
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


def _require_time_range(query: OdsRtSzdnSnapshotFlowAddcode) -> bool:
    """Java: ``isNotBlank(applyTime1) && isNotBlank(applyTime2)`` —— 时间段必填."""
    return is_not_blank(query.apply_time1) and is_not_blank(query.apply_time2)


@router.get("/list", response_model=None)
@pre_authorize_permi("base:snapshotflow:list")
def list_snapshot_flows(query: SnapshotFlowParam) -> TableDataInfo:
    """查询门架抓拍流水列表. Java: ``@GetMapping("/list")``."""
    collaborators = _collaborators()

    # 查询日志
    collaborators["car_query_log_service"].query_log(
        to_json_string_without_null(query), "2", "1"
    )

    _normalize(query)

    rsp_data = TableDataInfo()
    rows: List[OdsRtSzdnSnapshotFlowAddcode] = []
    total = 0

    # 时间段必填
    if _require_time_range(query):
        try:
            rsp_data = collaborators["enhanced_service"].query_page(query)
        except Exception:  # noqa: BLE001 —— Java: catch (Exception e)
            # Dead code in Java: queryPage() 自己吞掉所有异常，这里只是保留结构
            logger.error("【分表查询】异常，降级到 Forest 代理", exc_info=True)
            table_data_info = collaborators["client"].get_ods_rt_szdn_snapshot_flow_addcode_page(
                query
            )
            upstream_rows = table_data_info.get_rows()
            if upstream_rows is not None and len(upstream_rows) > 0:
                rows = [
                    OdsRtSzdnSnapshotFlowAddcode.model_validate(item)
                    for item in upstream_rows
                ]
                total = table_data_info.get_total()
            rsp_data.set_code(HttpStatus.SUCCESS)
            rsp_data.set_msg("查询成功")
            rsp_data.set_rows(rows)
            rsp_data.set_total(total)
    else:
        rsp_data.set_code(HttpStatus.SUCCESS)
        rsp_data.set_msg("查询成功")
        rsp_data.set_rows(rows)
        rsp_data.set_total(total)
    return rsp_data


@router.get("/export", response_model=None)
@pre_authorize_permi("base:snapshotflow:list")
def export(query: SnapshotFlowParam) -> Response:
    """导出门架抓拍流水列表. Java: ``@GetMapping("/export")`` —— 写完响应后 ``return null``."""
    collaborators = _collaborators()

    # 查询日志
    collaborators["car_query_log_service"].query_log(
        to_json_string_without_null(query), "2", "2"
    )

    _normalize(query)

    rows: List[OdsRtSzdnSnapshotFlowAddcode] = []
    # 时间段必填
    if _require_time_range(query):
        try:
            rows = collaborators["enhanced_service"].query_list_for_export(query)
        except Exception:  # noqa: BLE001 —— Java: catch (Exception e)
            logger.error("【分片导出】异常，降级到 Forest 代理", exc_info=True)
            rows = [
                OdsRtSzdnSnapshotFlowAddcode.model_validate(item)
                for item in collaborators[
                    "client"
                ].get_ods_rt_szdn_snapshot_flow_addcode_list_to_export(query)
            ]

    # 方向
    direction_map = collaborators["dict_service"].select_dict_data_map(DICT_DIRECTION)
    for item in rows:
        if item.direction is None:
            # Java: dp.getDirection().toString() —— NPE
            raise TypeError("java.lang.NullPointerException")
        item.direction_str = direction_map.get(str(item.direction))

    data: Dict[str, Any] = {ENTITY_LIST_KEY: rows}
    try:
        params = TemplateExportParams(EXPORT_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出门架抓拍流水失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


@router.get("/earliest-time", response_model=None)
def get_earliest_snapshottime() -> AjaxResult:
    """查询 GaussDB 中最早的 snapshottime. Java: ``@GetMapping("/earliest-time")``.

    字面量路由，必须排在 ``/{big_id}`` **之前**。
    返回的是上游的原始 JSON 值（Java 侧是 ``java.util.Date``，Jackson 会渲染成
    时间戳或 ISO-8601，取决于上游怎么发 —— 这里原样透传，见 ``COMPATIBILITY.md``）。
    """
    earliest_time = _collaborators()["client"].get_earliest_snapshottime()
    if earliest_time is not None:
        return AjaxResult.success_data(earliest_time)
    return AjaxResult.success_message(NO_DATA_MESSAGE)


@router.get("/{big_id}", response_model=None)
def get_info(big_id: str) -> AjaxResult:
    """获取门架抓拍流水详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    row = _collaborators()["client"].select_ods_rt_szdn_snapshot_flow_addcode_by_id(big_id)
    if isinstance(row, dict):
        for field in ("plateColorMark", "plateColorName", "directionStr"):
            row.setdefault(field, None)
    return AjaxResult.success_data(row)


__all__ = [
    "DICT_DIRECTION",
    "ENTITY_LIST_KEY",
    "EXPORT_TEMPLATE",
    "NO_DATA_MESSAGE",
    "OCTET_STREAM_CONTENT_TYPE",
    "SnapshotFlowParam",
    "export",
    "get_earliest_snapshottime",
    "get_info",
    "list_snapshot_flows",
    "reset_snapshot_flow_controller",
    "router",
]
