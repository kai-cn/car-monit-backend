"""流程节点 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowTemplateController.java

**7** 个映射
------------
========================  ==========================  ==========
Java                      Method / Path               权限点
========================  ==========================  ==========
``list``                  GET ``/list``               **无**
``flowlist``              GET ``/flowlist``           **无**
``export``                GET ``/export``             **无**
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 **无**
``edit``                  PUT ``""``                  **无**
``remove``                DELETE ``/{ids}``           **无**
========================  ==========================  ==========

``@PreAuthorize`` 在 Java 里全是注释行，这里一个都不加。

``/flowlist`` —— 头部插一条"虚拟节点"
-------------------------------------
Java 的逻辑是：

1. ``flowOid`` 为空（``CommonUtil.isNotBlank`` 为假）-> **返回空数组**，
   连数据库都不查；
2. 否则先查真实节点，再在**最前面**插一条手工构造的节点：

   ``{id: "-1", nodeOrder: -1, nodeKey: "tj", nodeName: "申请人提交"}``

   这条记录**不在库里**，``id`` 是 ``"-1"``、``nodeOrder`` 是 ``-1``，
   前端用它画"提交"这个起点。注意它**没有** ``flowOid``。

``/list`` 与 ``/flowlist`` 不一样：``/list`` 是分页表格，``/flowlist`` 是给
流程图用的全量有序数组（SQL 按 ``NODE_ORDER, id`` 排序）。

``remove`` 的一个已知怪癖（照抄，勿修）
--------------------------------------
``FlowTemplateServiceImpl.deleteFlowTemplateByIds`` 是"先删、再
``selectFlowTemplateById(ids[0]).getFlowOid()`` 重算节点链"。因为详情查询**不带**
``del_flag`` 过滤，软删之后仍能取到 ``flowOid``，所以链路重算照常发生 —— 但取的是
"已删除那一行"的 ``flowOid``。这是 Java 的既有行为，此处原样保留。
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
from app.common.utils.common_util import is_not_blank
from app.common.utils.poi.excel_util import ExcelUtil
from app.flow.domain.flow_template import FlowTemplate
from app.flow.service.flow_template_service import FlowTemplateService
from app.flow.service.flow_template_service import get_service as _get_service
from app.flow.service.flow_template_service import reset_service as _reset_service
from app.framework.aspectj.log_aspect import log

logger = logging.getLogger("app.api.flow.flow_template_controller")

router = APIRouter(prefix="/flow/flowtemplate", tags=["flow-template"])

#: Java: ``com.ruoyi.web.controller.flow.FlowTemplateController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.flow.FlowTemplateController"

#: Java: ``util.exportExcel(list, "流程节点数据")``
EXPORT_SHEET_NAME = "流程节点数据"

#: Java: ``firstbo.setId("-1")``
VIRTUAL_NODE_ID = "-1"

#: Java: ``firstbo.setNodeOrder(-1)``
VIRTUAL_NODE_ORDER = -1

#: Java: ``firstbo.setNodeKey("tj")``
VIRTUAL_NODE_KEY = "tj"

#: Java: ``firstbo.setNodeName("申请人提交")``
VIRTUAL_NODE_NAME = "申请人提交"

_SERVICE: Optional[FlowTemplateService] = None


def _service() -> FlowTemplateService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = _get_service()
    return _SERVICE


def reset_flow_template_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None
    _reset_service()


def _query(request: Request) -> FlowTemplate:
    """Java: 形参 ``FlowTemplate flowTemplate``（**没有** ``@RequestBody``）."""
    return bind_query_params(FlowTemplate, request.query_params)


FlowTemplateParam = Annotated[FlowTemplate, Depends(_query)]


def build_virtual_submit_node() -> FlowTemplate:
    """Java: ``new FlowTemplate(); setId("-1"); setNodeOrder(-1); ...``.

    这条"申请人提交"节点只存在于响应里，不入库。
    """
    node = FlowTemplate()
    node.id = VIRTUAL_NODE_ID
    node.node_order = VIRTUAL_NODE_ORDER
    node.node_key = VIRTUAL_NODE_KEY
    node.node_name = VIRTUAL_NODE_NAME
    return node


@router.get("/list", response_model=None)
def list_flow_templates(query: FlowTemplateParam) -> TableDataInfo:
    """查询流程节点列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_flow_template_list(query))


@router.get("/flowlist", response_model=None)
def flowlist(query: FlowTemplateParam) -> AjaxResult:
    """获取流程（带"申请人提交"首节点）. Java: ``@GetMapping("/flowlist")``.

    ``flowOid`` 为空时返回**空数组**；否则 ``[虚拟节点] + 真实节点``。**不分页**。
    """
    result: List[FlowTemplate] = []
    if is_not_blank(query.flow_oid):
        result.append(build_virtual_submit_node())
        result.extend(_service().select_flow_template_list(query))
    return AjaxResult.success_data(result)


@router.get("/export", response_model=None)
@log(title="流程节点", business_type=BusinessType.EXPORT, java_method="export")
def export(query: FlowTemplateParam) -> AjaxResult:
    """导出流程节点列表. Java: ``@GetMapping("/export")`` —— 无 ``startPage()``."""
    rows = _service().select_flow_template_list(query)
    return ExcelUtil(FlowTemplate).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取流程节点详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_flow_template_by_id(id))


@router.post("", response_model=None)
@log(title="流程节点", business_type=BusinessType.INSERT, java_method="add")
def add(entity: FlowTemplate) -> AjaxResult:
    """新增流程节点. Java: ``@PostMapping`` + ``@RequestBody``.

    service 侧会先查 ``isExitsKey`` / ``isExitsSort``，重复时回
    ``节点key存在重复`` / ``节点顺序存在重复``。
    """
    return _service().save_flow_template(entity)


@router.put("", response_model=None)
@log(title="流程节点", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: FlowTemplate) -> AjaxResult:
    """修改流程节点. Java: ``@PutMapping`` + ``@RequestBody``."""
    return _service().save_flow_template(entity)


@router.delete("/{ids}", response_model=None)
@log(title="流程节点", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除流程节点. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_flow_template_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "VIRTUAL_NODE_ID",
    "VIRTUAL_NODE_KEY",
    "VIRTUAL_NODE_NAME",
    "VIRTUAL_NODE_ORDER",
    "add",
    "build_virtual_submit_node",
    "edit",
    "export",
    "flowlist",
    "get_info",
    "list_flow_templates",
    "remove",
    "reset_flow_template_controller",
]
