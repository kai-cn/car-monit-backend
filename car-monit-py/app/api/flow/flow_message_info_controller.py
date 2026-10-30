"""系统内部消息 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java

**8** 个映射
------------
========================  ==========================  ==========
Java                      Method / Path               权限点
========================  ==========================  ==========
``list``                  GET ``/list``               **无**
``listyb``                GET ``/listyb``             **无**
``listyj``                GET ``/listyj``             **无**
``listxx``                GET ``/listxx``             **无**
``export``                GET ``/export``             **无**
``getInfo``               GET ``/{id}``               **无**
``remove``                DELETE ``/{ids}``           **无**
``exportShrz``            GET ``/exportShrz``         **无**
========================  ==========================  ==========

Java 里 **``add`` / ``edit`` 被整段块注释掉了**（源文件 132–148 行），所以这里
**不注册** ``POST ""`` 与 ``PUT ""``。这是"迁移"而不是"补全"，不要顺手加上。

四个列表接口的唯一区别是 ``flag``
---------------------------------
它们都把 ``userId`` 设成当前登录人，再塞一个 ``flag`` 交给 MyBatis 的
``<choose>`` 分支（详见 ``FlowMessageInfoMapper.xml``）：

    ==========  =============================================================
    flag        追加的 where 片段
    ==========  =============================================================
    ``mydb``    我的待办：``MSG_TYPE='2'`` 且 存在自己的 ``MSG_STATUS='2'`` 处理记录
    ``myyb``    我的已办：``MSG_TYPE='2'`` 且 存在自己的 ``MSG_STATUS='1'`` 处理记录
    ``myyj``    我的已结：在 ``myyb`` 之上再加 ``app.FLOW_STATUS='3'``
    ``myxx``    我的消息：``MSG_TYPE='1'`` 且 存在自己的处理记录（任何状态）
    ==========  =============================================================

``myxx`` 还会**多查一列** ``msgStatus``（相关子查询），另外三个不带。

``export`` 与 ``exportShrz`` 的区别
-----------------------------------
* ``export`` —— ``ExcelUtil`` 直接写临时文件，返回 ``AjaxResult``（``msg`` 是文件名）；
  **不设** ``flag``、**不设** ``userId``，即"按查询条件全量"。
* ``exportShrz`` —— easypoi **模板** ``templates/export/exportShrz.xlsx``，
  只导出"某一个消息"对应的审核日志：先按 ``id`` 查消息取
  ``applyName`` / ``createTime``（格式化 ``yyyy-MM-dd``）/ ``msgTitle``，
  再用消息的 ``billOid`` 查审核历史，逐行把 ``sort`` 写成 ``i+1``（**从 1 开始**），
  最后 ``response`` 写完即 ``return null``。查不到消息时 Java 会先 NPE
  （在 try 之外）-> HTTP 200 + ``code 500``，这里同样抛 ``AttributeError``。

路由声明顺序（与 Java 不同，已记录）
------------------------------------
Java 把 ``exportShrz`` 写在 ``/{id}`` **之后**，靠 Spring 的"更具体者优先"仍然命中；
FastAPI 是**声明顺序优先**，所以这里把 ``/exportShrz`` 提到 ``/{id}`` 之前，
否则它会被当成 ``id="exportShrz"`` 的详情查询。
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    get_user_id,
    parse_str_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils.date_utils import YYYY_MM_DD, parse_date_to_str
from app.common.utils.poi.excel_util import ExcelUtil
from app.common.utils.poi.template_export import (
    ExcelExportUtil,
    TemplateExportParams,
    workbook_to_bytes,
)
from app.flow.domain.flow_list import FlowList
from app.flow.domain.flow_message_info import FlowMessageInfo
from app.flow.service.flow_list_service import FlowListService
from app.flow.service.flow_list_service import get_service as _get_flow_list_service
from app.flow.service.flow_message_info_service import FlowMessageInfoService
from app.flow.service.flow_message_info_service import get_service as _get_service
from app.flow.service.flow_message_info_service import reset_service as _reset_service
from app.framework.aspectj.log_aspect import log

logger = logging.getLogger("app.api.flow.flow_message_info_controller")

router = APIRouter(prefix="/flow/messageinfo", tags=["flow-message-info"])

#: Java: ``com.ruoyi.web.controller.flow.FlowMessageInfoController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.flow.FlowMessageInfoController"

#: Java: ``util.exportExcel(list, "系统内部消息数据")``
EXPORT_SHEET_NAME = "系统内部消息数据"

#: Java: ``String url = "templates/export/exportShrz.xlsx";``
EXPORT_SHRZ_TEMPLATE = "templates/export/exportShrz.xlsx"

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"

#: Java: ``map.put("entitylist", list)``
ENTITY_LIST_KEY = "entitylist"

#: ``flag`` 取值 —— 与 ``FlowMessageInfoMapper.xml`` 的 ``<choose>`` 一一对应
FLAG_MY_DB = "mydb"  # 我的待办
FLAG_MY_YB = "myyb"  # 我的已办
FLAG_MY_YJ = "myyj"  # 我的已结
FLAG_MY_XX = "myxx"  # 我的消息

_SERVICE: Optional[FlowMessageInfoService] = None
_FLOW_LIST_SERVICE: Optional[FlowListService] = None


def _service() -> FlowMessageInfoService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = _get_service()
    return _SERVICE


def _flow_list_service() -> FlowListService:
    global _FLOW_LIST_SERVICE
    if _FLOW_LIST_SERVICE is None:
        _FLOW_LIST_SERVICE = _get_flow_list_service()
    return _FLOW_LIST_SERVICE


def reset_flow_message_info_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _SERVICE, _FLOW_LIST_SERVICE
    _SERVICE = None
    _FLOW_LIST_SERVICE = None
    _reset_service()


def _query(request: Request) -> FlowMessageInfo:
    """Java: 形参 ``FlowMessageInfo flowMessageInfo``（**没有** ``@RequestBody``）."""
    return bind_query_params(FlowMessageInfo, request.query_params)


MessageInfoParam = Annotated[FlowMessageInfo, Depends(_query)]


def _list_with_flag(query: FlowMessageInfo, flag: str) -> TableDataInfo:
    """四个列表接口共用的三步：``startPage`` -> ``setFlag`` -> ``setUserId``."""
    start_page()
    query.flag = flag
    query.user_id = get_user_id()
    return get_data_table(_service().select_flow_message_info_list(query))


@router.get("/list", response_model=None)
def list_pending(query: MessageInfoParam) -> TableDataInfo:
    """查询系统内部消息列表 -- 我的待办. Java: ``@GetMapping("/list")``."""
    return _list_with_flag(query, FLAG_MY_DB)


@router.get("/listyb", response_model=None)
def list_done(query: MessageInfoParam) -> TableDataInfo:
    """查询系统内部消息列表 -- 我的已办. Java: ``@GetMapping("/listyb")``."""
    return _list_with_flag(query, FLAG_MY_YB)


@router.get("/listyj", response_model=None)
def list_finished(query: MessageInfoParam) -> TableDataInfo:
    """查询系统内部消息列表 -- 我的已结. Java: ``@GetMapping("/listyj")``."""
    return _list_with_flag(query, FLAG_MY_YJ)


@router.get("/listxx", response_model=None)
def list_messages(query: MessageInfoParam) -> TableDataInfo:
    """查询系统内部消息列表 -- 我的消息. Java: ``@GetMapping("/listxx")``."""
    return _list_with_flag(query, FLAG_MY_XX)


@router.get("/export", response_model=None)
@log(title="系统内部消息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: MessageInfoParam) -> AjaxResult:
    """导出系统内部消息列表. Java: ``@GetMapping("/export")``.

    **不设** ``flag`` / ``userId``，也不 ``startPage()`` —— 导全量。
    """
    rows = _service().select_flow_message_info_list(query)
    return ExcelUtil(FlowMessageInfo).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/exportShrz", response_model=None)
@log(title="导出审核日志", business_type=BusinessType.EXPORT, java_method="exportShrz")
def export_shrz(query: MessageInfoParam) -> Response:
    """导出审核日志. Java: ``@GetMapping("/exportShrz")`` —— 写完响应后 ``return null``.

    模板是 ``templates/export/exportShrz.xlsx``，占位符为
    ``applyName`` / ``createTime`` / ``msgTitle`` / ``entitylist``（明细列表）。
    """
    message_info = _service().select_flow_message_info_by_id(query.id)

    data: Dict[str, Any] = {}
    # Java 先取字段再进 try —— 这里也在 try 之外，保持 NPE/空指针同样的落点
    data["applyName"] = message_info.apply_name
    data["createTime"] = parse_date_to_str(YYYY_MM_DD, message_info.create_time)
    data["msgTitle"] = message_info.msg_title

    history_probe = FlowList()
    history_probe.bill_oid = message_info.bill_oid
    history: List[FlowList] = list(_flow_list_service().select_flow_list_list(history_probe))
    for index, item in enumerate(history):
        # Java: fl.setSort(i+1) —— 从 1 开始
        item.sort = index + 1
    data[ENTITY_LIST_KEY] = history

    try:
        params = TemplateExportParams(EXPORT_SHRZ_TEMPLATE)
        workbook = ExcelExportUtil.export_excel(params, data)
        content = workbook_to_bytes(workbook)
    except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { e.printStackTrace(); }
        logger.error("导出审核日志失败", exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— 没有 filename
            "Content-Disposition": "attachment",
        },
    )


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取系统内部消息详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_flow_message_info_by_id(id))


@router.delete("/{ids}", response_model=None)
@log(title="系统内部消息", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除系统内部消息. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_flow_message_info_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "ENTITY_LIST_KEY",
    "EXPORT_SHEET_NAME",
    "EXPORT_SHRZ_TEMPLATE",
    "FLAG_MY_DB",
    "FLAG_MY_XX",
    "FLAG_MY_YB",
    "FLAG_MY_YJ",
    "OCTET_STREAM_CONTENT_TYPE",
    "export",
    "export_shrz",
    "get_info",
    "list_done",
    "list_finished",
    "list_messages",
    "list_pending",
    "remove",
    "reset_flow_message_info_controller",
]
