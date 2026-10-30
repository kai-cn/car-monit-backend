"""流程_当前节点 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowCurrentNodeController.java

**10** 个映射
-------------
==========================  ===================================  ==========
Java                        Method / Path                        权限点
==========================  ===================================  ==========
``list``                    GET ``/list``                        **无**
``export``                  GET ``/export``                      **无**
``getInfo``                 GET ``/{id}``                        **无**
``getInfoByBillId``         GET ``/getInfoByBillId/{billOid}``    **无**
``add``                     POST ``""``                          **无**
``edit``                    PUT ``""``                           **无**
``remove``                  DELETE ``/{ids}``                    **无**
``saveFlowAuit``            PUT ``/saveFlowAuit``                **无**
``submitReturn``            POST ``/submitReturn``               **无**
``submitEntrustFlow``       POST ``/submitEntrustFlow``          **无**
==========================  ===================================  ==========

本控制器在 Java 里**一个** ``@PreAuthorize`` 都没有（全是注释行），这里保持不放。

``getInfoByBillId`` 的"查不到就回显查询条件"
---------------------------------------------
Java 先 ``new FlowCurrentNode()`` 再把 ``billOid`` 塞进去当查询条件，查完若列表非空
就取 ``list.get(0)``，**否则原样返回那个查询对象**（即 ``{billOid: ..., 其余全是 null}``）。
所以这个接口永远不会回 ``data: null``。照抄。

路由声明顺序
------------
``/getInfoByBillId/{billOid}`` 是两段路径，与 ``/{id}`` 不冲突；但仍按 Java 的顺序
把静态段放在 ``/{id}`` 之前，避免后来加接口时踩坑。
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

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
from app.common.utils.poi.excel_util import ExcelUtil
from app.flow.domain.flow_current_node import FlowCurrentNode
from app.flow.service.flow_current_node_service import FlowCurrentNodeService
from app.flow.service.flow_current_node_service import get_service as _get_service
from app.flow.service.flow_current_node_service import reset_service as _reset_service
from app.framework.aspectj.log_aspect import log

logger = logging.getLogger("app.api.flow.flow_current_node_controller")

router = APIRouter(prefix="/flow/currentnode", tags=["flow-current-node"])

#: Java: ``com.ruoyi.web.controller.flow.FlowCurrentNodeController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.flow.FlowCurrentNodeController"

#: Java: ``util.exportExcel(list, "流程_当前节点数据")``
EXPORT_SHEET_NAME = "流程_当前节点数据"

_SERVICE: Optional[FlowCurrentNodeService] = None


def _service() -> FlowCurrentNodeService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = _get_service()
    return _SERVICE


def reset_flow_current_node_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None
    _reset_service()


def _query(request: Request) -> FlowCurrentNode:
    """Java: 形参 ``FlowCurrentNode flowCurrentNode``（**没有** ``@RequestBody``）."""
    return bind_query_params(FlowCurrentNode, request.query_params)


CurrentNodeParam = Annotated[FlowCurrentNode, Depends(_query)]


@router.get("/list", response_model=None)
def list_current_nodes(query: CurrentNodeParam) -> TableDataInfo:
    """查询流程_当前节点列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_flow_current_node_list(query))


@router.get("/export", response_model=None)
@log(title="流程_当前节点", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CurrentNodeParam) -> AjaxResult:
    """导出流程_当前节点列表. Java: ``@GetMapping("/export")``.

    Java 这里没有 ``startPage()`` —— 导全量。
    """
    rows = _service().select_flow_current_node_list(query)
    return ExcelUtil(FlowCurrentNode).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/getInfoByBillId/{billOid}", response_model=None)
def get_info_by_bill_id(billOid: str) -> AjaxResult:  # noqa: N803 —— 照抄 Java 形参名
    """根据单据ID获取当前节点. Java: ``@GetMapping(value = "/getInfoByBillId/{billOid}")``.

    查不到时返回**查询对象本身**（只带 ``billOid``），不是 ``null``。
    """
    probe = FlowCurrentNode()
    probe.bill_oid = billOid
    rows = _service().select_flow_current_node_list(probe)
    if len(rows) > 0:
        probe = rows[0]
    return AjaxResult.success_data(probe)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取流程_当前节点详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_flow_current_node_by_id(id))


@router.post("", response_model=None)
@log(title="流程_当前节点", business_type=BusinessType.INSERT, java_method="add")
def add(entity: FlowCurrentNode) -> AjaxResult:
    """新增流程_当前节点. Java: ``@PostMapping`` + ``@RequestBody``."""
    return _service().save_flow_current_node(entity)


@router.put("", response_model=None)
@log(title="流程_当前节点", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: FlowCurrentNode) -> AjaxResult:
    """修改流程_当前节点. Java: ``@PutMapping`` + ``@RequestBody``."""
    return _service().save_flow_current_node(entity)


@router.delete("/{ids}", response_model=None)
@log(title="流程_当前节点", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除流程_当前节点. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_flow_current_node_by_ids(parse_str_array(ids))


@router.put("/saveFlowAuit", response_model=None)
def save_flow_auit(entity: FlowCurrentNode) -> AjaxResult:
    """流程审核. Java: ``@PutMapping("/saveFlowAuit")`` + ``@RequestBody``.

    ``shValue``: ``1`` 同意 / ``2`` 拒绝 / ``3`` 退回；走 :meth:`save_flow_auit` 的完整分支。
    """
    return _service().save_flow_auit(entity)


@router.post("/submitReturn", response_model=None)
def submit_return(entity: FlowCurrentNode) -> AjaxResult:
    """撤销流程. Java: ``@PostMapping("/submitReturn")`` + ``@RequestBody``."""
    return _service().submit_return(entity)


@router.post("/submitEntrustFlow", response_model=None)
def submit_entrust_flow(entity: FlowCurrentNode) -> AjaxResult:
    """委托-办理流程. Java: ``@PostMapping("/submitEntrustFlow")`` + ``@RequestBody``."""
    return _service().submit_entrust_flow(entity)


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "get_info",
    "get_info_by_bill_id",
    "list_current_nodes",
    "remove",
    "reset_flow_current_node_controller",
    "save_flow_auit",
    "submit_entrust_flow",
    "submit_return",
]
