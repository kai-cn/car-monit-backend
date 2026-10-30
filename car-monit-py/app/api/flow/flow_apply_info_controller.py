"""我的申请 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowApplyInfoController.java

**7** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               **无**
``listAll``               GET ``/listAll``            ``flow:applyinfo:list``
``export``                GET ``/export``             **无**
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 **无**
``edit``                  PUT ``""``                  **无**
``remove``                DELETE ``/{ids}``           **无**
========================  ==========================  ==============================

``/list`` 与 ``/listAll`` 的唯一区别
------------------------------------
``/list`` 在控制器里插了一句 ``flowApplyInfo.setCreateBy(SecurityUtils.getUserId())``
（注释写着"查询我的申请"），所以只能看到自己创建的单子；``/listAll`` 没有这句，
能看到全部 —— 它也是本控制器**唯一**保留 ``@PreAuthorize`` 的方法，其余 6 个在
Java 里都是注释掉的。

``export`` 走 ``ExcelUtil``（不是模板导出），返回的 ``AjaxResult`` 里 ``msg`` 是
文件名、**没有** ``data`` 键。
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

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
from app.common.utils.poi.excel_util import ExcelUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.flow.domain.flow_apply_info import FlowApplyInfo
from app.flow.service.flow_apply_info_service import FlowApplyInfoService
from app.flow.service.flow_apply_info_service import get_service as _get_service
from app.flow.service.flow_apply_info_service import reset_service as _reset_service

logger = logging.getLogger("app.api.flow.flow_apply_info_controller")

router = APIRouter(prefix="/flow/applyinfo", tags=["flow-apply-info"])

#: Java: ``com.ruoyi.web.controller.flow.FlowApplyInfoController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.flow.FlowApplyInfoController"

#: Java: ``util.exportExcel(list, "我的申请数据")``
EXPORT_SHEET_NAME = "我的申请数据"

_SERVICE: Optional[FlowApplyInfoService] = None


def _service() -> FlowApplyInfoService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = _get_service()
    return _SERVICE


def reset_flow_apply_info_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None
    _reset_service()


def _query(request: Request) -> FlowApplyInfo:
    """Java: 形参 ``FlowApplyInfo flowApplyInfo``（**没有** ``@RequestBody``）."""
    return bind_query_params(FlowApplyInfo, request.query_params)


ApplyInfoParam = Annotated[FlowApplyInfo, Depends(_query)]


@router.get("/list", response_model=None)
def list_apply_infos(query: ApplyInfoParam) -> TableDataInfo:
    """查询我的申请列表. Java: ``@GetMapping("/list")``.

    ``setCreateBy(SecurityUtils.getUserId())`` —— 只看自己创建的。
    """
    start_page()
    query.create_by = get_user_id()
    return get_data_table(_service().select_flow_apply_info_list(query))


@router.get("/listAll", response_model=None)
@pre_authorize_permi("flow:applyinfo:list")
def list_all_apply_infos(query: ApplyInfoParam) -> TableDataInfo:
    """查询全部申请. Java: ``@GetMapping("/listAll")`` —— **没有** ``setCreateBy``."""
    start_page()
    return get_data_table(_service().select_flow_apply_info_list(query))


@router.get("/export", response_model=None)
@log(title="我的申请", business_type=BusinessType.EXPORT, java_method="export")
def export(query: ApplyInfoParam) -> AjaxResult:
    """导出我的申请列表. Java: ``@GetMapping("/export")``.

    注意 Java 这里**没有** ``startPage()``，也**没有** ``setCreateBy`` ——
    导的是"按查询条件能查到的全部"，不受"我的"限制。照抄。
    """
    rows = _service().select_flow_apply_info_list(query)
    return ExcelUtil(FlowApplyInfo).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取我的申请详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_flow_apply_info_by_id(id))


@router.post("", response_model=None)
@log(title="我的申请", business_type=BusinessType.INSERT, java_method="add")
def add(entity: FlowApplyInfo) -> AjaxResult:
    """新增我的申请. Java: ``@PostMapping`` + ``@RequestBody``."""
    return _service().save_flow_apply_info(entity)


@router.put("", response_model=None)
@log(title="我的申请", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: FlowApplyInfo) -> AjaxResult:
    """修改我的申请. Java: ``@PutMapping`` + ``@RequestBody``."""
    return _service().save_flow_apply_info(entity)


@router.delete("/{ids}", response_model=None)
@log(title="我的申请", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除我的申请. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_flow_apply_info_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "get_info",
    "list_all_apply_infos",
    "list_apply_infos",
    "remove",
    "reset_flow_apply_info_controller",
]
