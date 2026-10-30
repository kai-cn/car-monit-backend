"""审核历史记录 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowListController.java

**7** 个映射
------------
========================  ==========================  ==========
Java                      Method / Path               权限点
========================  ==========================  ==========
``list``                  GET ``/list``               **无**
``listnew``               GET ``/listnew``            **无**
``export``                GET ``/export``             **无**
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 **无**
``edit``                  PUT ``""``                  **无**
``remove``                DELETE ``/{ids}``           **无**
========================  ==========================  ==========

``listnew`` —— 在历史末尾补一条"当前状态"
------------------------------------------
这是本控制器唯一有业务逻辑的方法，Java 原文的步骤是：

1. ``billOid`` 为空（``StringUtils.isEmpty``，即 ``null`` 或空串）时改成 ``"-1"``
   —— 于是查不到任何历史，返回空数组而不是全表。
2. 用 ``billOid`` 查审核历史（**注意用的是 ``selectFlowListList``**，即 ``create_time ASC``
   那个；虽然接口层还有 ``selectFlowListListNew``（``desc``），但这里**没有**用它）。
3. 再用同一个 ``billOid`` 查 ``flow_apply_info``，取第一条：
   * ``flow_status == "2"``（审批中）且 ``BACK_COL1``（当前审批人）非空
     -> 补一条 ``{shUser: 当前审批人, shValue: "待审批"}``；
   * ``flow_status == "3"``（审批通过）
     -> 补一条 ``{shValue: "流程结束"}``；
   * 其它状态（起草中/退回/拒绝）不补。
4. ``listnew`` **没有** ``startPage()``。

``CommonUtil.isNull`` 的语义是"``null`` -> ``""``，其余 ``toString().trim()``"，
所以比较前已经把空白去掉、``null`` 也已经归一成空串 —— 这里用
:func:`app.common.utils.common_util.is_null` 保持一致。
"""

from __future__ import annotations

import logging
from typing import Annotated, List, Optional

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
from app.common.enums.flow_type_enum import FlowTypeEnum
from app.common.utils.common_util import is_null
from app.common.utils.poi.excel_util import ExcelUtil
from app.common.utils.string_utils import is_empty
from app.flow.domain.flow_apply_info import FlowApplyInfo
from app.flow.domain.flow_list import FlowList
from app.flow.service.flow_apply_info_service import FlowApplyInfoService
from app.flow.service.flow_apply_info_service import get_service as _get_apply_service
from app.flow.service.flow_list_service import FlowListService
from app.flow.service.flow_list_service import get_service as _get_service
from app.flow.service.flow_list_service import reset_service as _reset_service
from app.framework.aspectj.log_aspect import log

logger = logging.getLogger("app.api.flow.flow_list_controller")

router = APIRouter(prefix="/flow/flowlist", tags=["flow-list"])

#: Java: ``com.ruoyi.web.controller.flow.FlowListController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.flow.FlowListController"

#: Java: ``util.exportExcel(list, "审核历史记录数据")``
EXPORT_SHEET_NAME = "审核历史记录数据"

#: Java: ``flowList.setBillOid("-1")`` —— 用来"查不到任何一条"的哨兵值
EMPTY_BILL_OID = "-1"

#: Java: ``addbo.setShValue("待审批")``
PENDING_AUDIT_TEXT = "待审批"

#: Java: ``addbo.setShValue("流程结束")``
FLOW_END_TEXT = "流程结束"

_SERVICE: Optional[FlowListService] = None
_APPLY_SERVICE: Optional[FlowApplyInfoService] = None


def _service() -> FlowListService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = _get_service()
    return _SERVICE


def _apply_service() -> FlowApplyInfoService:
    global _APPLY_SERVICE
    if _APPLY_SERVICE is None:
        _APPLY_SERVICE = _get_apply_service()
    return _APPLY_SERVICE


def reset_flow_list_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _SERVICE, _APPLY_SERVICE
    _SERVICE = None
    _APPLY_SERVICE = None
    _reset_service()


def _query(request: Request) -> FlowList:
    """Java: 形参 ``FlowList flowList``（**没有** ``@RequestBody``）."""
    return bind_query_params(FlowList, request.query_params)


FlowListParam = Annotated[FlowList, Depends(_query)]


@router.get("/list", response_model=None)
def list_flow_lists(query: FlowListParam) -> TableDataInfo:
    """查询审核历史记录列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_flow_list_list(query))


@router.get("/listnew", response_model=None)
def listnew(query: FlowListParam) -> AjaxResult:
    """根据单据查询（历史 + 当前状态尾巴）. Java: ``@GetMapping("/listnew")``.

    见模块 docstring 的四步；**不分页**。
    """
    if is_empty(query.bill_oid):
        query.bill_oid = EMPTY_BILL_OID

    rows: List[FlowList] = list(_service().select_flow_list_list(query))

    # Java: FlowApplyInfo flowApplyInfo = new FlowApplyInfo(); setBillOid(...)
    probe = FlowApplyInfo()
    probe.bill_oid = query.bill_oid
    apply_list = _apply_service().select_flow_apply_info_list(probe)
    if len(apply_list) > 0:
        apply_info = apply_list[0]
        status = is_null(apply_info.flow_status)
        auit_emp_name = is_null(apply_info.back_col1)
        if status == str(FlowTypeEnum.APPROVE.get_code()):
            # 当前审核人 —— 空了就不补
            if auit_emp_name != "":
                extra = FlowList()
                extra.sh_user = auit_emp_name
                extra.sh_value = PENDING_AUDIT_TEXT
                rows.append(extra)
        elif status == str(FlowTypeEnum.END.get_code()):
            extra = FlowList()
            extra.sh_value = FLOW_END_TEXT
            rows.append(extra)

    return AjaxResult.success_data(rows)


@router.get("/export", response_model=None)
@log(title="审核历史记录", business_type=BusinessType.EXPORT, java_method="export")
def export(query: FlowListParam) -> AjaxResult:
    """导出审核历史记录列表. Java: ``@GetMapping("/export")``.

    Java 没有 ``startPage()`` —— 导全量。
    """
    rows = _service().select_flow_list_list(query)
    return ExcelUtil(FlowList).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取审核历史记录详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_flow_list_by_id(id))


@router.post("", response_model=None)
@log(title="审核历史记录", business_type=BusinessType.INSERT, java_method="add")
def add(entity: FlowList) -> AjaxResult:
    """新增审核历史记录. Java: ``@PostMapping`` + ``@RequestBody``."""
    return _service().save_flow_list(entity)


@router.put("", response_model=None)
@log(title="审核历史记录", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: FlowList) -> AjaxResult:
    """修改审核历史记录. Java: ``@PutMapping`` + ``@RequestBody``."""
    return _service().save_flow_list(entity)


@router.delete("/{ids}", response_model=None)
@log(title="审核历史记录", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除审核历史记录. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_flow_list_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "EMPTY_BILL_OID",
    "EXPORT_SHEET_NAME",
    "FLOW_END_TEXT",
    "PENDING_AUDIT_TEXT",
    "add",
    "edit",
    "export",
    "get_info",
    "list_flow_lists",
    "listnew",
    "remove",
    "reset_flow_list_controller",
]
