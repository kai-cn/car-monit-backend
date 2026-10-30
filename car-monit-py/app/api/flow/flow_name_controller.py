"""流程名称 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowNameController.java

**8** 个映射
------------
========================  ==========================  =========================
Java                      Method / Path               权限点
========================  ==========================  =========================
``list``                  GET ``/list``               ``flow:flowname:list``
``listQuery``             GET ``/listQuery``          **无**
``export``                GET ``/export``             ``flow:flowname:export``
``getInfo``               GET ``/{id}``               ``flow:flowname:query``
``add``                   POST ``""``                 ``flow:flowname:add``
``edit``                  PUT ``""``                  ``flow:flowname:edit``
``remove``                DELETE ``/{ids}``           ``flow:flowname:remove``
``tbFlow``                POST ``/tbFlow``            ``flow:flowname:edit``
========================  ==========================  =========================

这是 flow 包里**唯一**逐个方法都挂 ``@PreAuthorize`` 的控制器（其它 6 个的注解
在 Java 里几乎全是注释行）。

``/list`` 与 ``/listQuery`` 的区别
----------------------------------
* ``/list`` —— 管理员视角，**不过滤租户**，要 ``flow:flowname:list`` 权限。
* ``/listQuery`` —— 单位视角，控制器里插了一句
  ``flowName.setTenantId(SecurityUtils.getTenantId())``，**没有**权限点，登录即可。

``/tbFlow``
-----------
把某个流程的节点模板同步到所有 ``isUint='1'`` 的单位（详见
``FlowNameServiceImpl.tbFlow``）；权限点复用 ``flow:flowname:edit``（不是 :add）。
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
from app.common.utils.security_utils import get_tenant_id
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.flow.domain.flow_name import FlowName
from app.flow.service.flow_name_service import FlowNameService
from app.flow.service.flow_name_service import get_service as _get_service
from app.flow.service.flow_name_service import reset_service as _reset_service

logger = logging.getLogger("app.api.flow.flow_name_controller")

router = APIRouter(prefix="/flow/flowname", tags=["flow-name"])

#: Java: ``com.ruoyi.web.controller.flow.FlowNameController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.flow.FlowNameController"

#: Java: ``util.exportExcel(list, "流程名称数据")``
EXPORT_SHEET_NAME = "流程名称数据"

_SERVICE: Optional[FlowNameService] = None


def _service() -> FlowNameService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = _get_service()
    return _SERVICE


def reset_flow_name_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None
    _reset_service()


def _query(request: Request) -> FlowName:
    """Java: 形参 ``FlowName flowName``（**没有** ``@RequestBody``）."""
    return bind_query_params(FlowName, request.query_params)


FlowNameParam = Annotated[FlowName, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("flow:flowname:list")
def list_flow_names(query: FlowNameParam) -> TableDataInfo:
    """查询流程名称列表 -- 管理员. Java: ``@GetMapping("/list")`` —— 不过滤租户."""
    start_page()
    return get_data_table(_service().select_flow_name_list(query))


@router.get("/listQuery", response_model=None)
def list_query(query: FlowNameParam) -> TableDataInfo:
    """查询流程名称列表 -- 单位查询自己的. Java: ``@GetMapping("/listQuery")``.

    ``setTenantId(SecurityUtils.getTenantId())`` —— 只看本单位。**没有**权限点。
    """
    start_page()
    query.tenant_id = get_tenant_id()
    return get_data_table(_service().select_flow_name_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("flow:flowname:export")
@log(title="流程名称", business_type=BusinessType.EXPORT, java_method="export")
def export(query: FlowNameParam) -> AjaxResult:
    """导出流程名称列表. Java: ``@GetMapping("/export")`` —— 无 ``startPage()``."""
    rows = _service().select_flow_name_list(query)
    return ExcelUtil(FlowName).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
@pre_authorize_permi("flow:flowname:query")
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取流程名称详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_flow_name_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("flow:flowname:add")
@log(title="流程名称", business_type=BusinessType.INSERT, java_method="add")
def add(entity: FlowName) -> AjaxResult:
    """新增流程名称. Java: ``@PostMapping`` + ``@RequestBody``.

    service 侧会先查 ``isExitsKey``，重名时返回 ``节点key存在重复``。
    """
    return _service().save_flow_name(entity)


@router.put("", response_model=None)
@pre_authorize_permi("flow:flowname:edit")
@log(title="流程名称", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: FlowName) -> AjaxResult:
    """修改流程名称. Java: ``@PutMapping`` + ``@RequestBody``."""
    return _service().save_flow_name(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("flow:flowname:remove")
@log(title="流程名称", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除流程名称. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_flow_name_by_ids(parse_str_array(ids))


@router.post("/tbFlow", response_model=None)
@pre_authorize_permi("flow:flowname:edit")
@log(title="同步其他单位的工作流", business_type=BusinessType.UPDATE, java_method="tbFlow")
def tb_flow(entity: FlowName) -> AjaxResult:
    """同步其他单位的工作流. Java: ``@PostMapping("/tbFlow")`` + ``@RequestBody``."""
    return _service().tb_flow(entity)


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "get_info",
    "list_flow_names",
    "list_query",
    "remove",
    "reset_flow_name_controller",
    "tb_flow",
]
