"""系统消息处理人 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageDisposeController.java

**8** 个映射
------------
========================  ==========================  ==========
Java                      Method / Path               权限点
========================  ==========================  ==========
``list``                  GET ``/list``               **无**
``export``                GET ``/export``             **无**
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 **无**
``edit``                  PUT ``""``                  **无**
``remove``                DELETE ``/{ids}``           **无**
``removeFlowMessage``     DELETE ``/delmes/{mid}``    **无**
``szzdFlowMessage``       DELETE ``/szzdmes/{mid}``   **无**
========================  ==========================  ==========

两个"按消息主键"的接口
-----------------------
它们都只传 ``mid``，第二个参数是控制器自己算出来的 ``SecurityUtils.getUserId() + ""``
（Java 把 ``Long`` 拼成字符串）—— ``bussId`` 就是"当前登录用户"。
所以同一个消息对不同人操作，落库范围不同。

* ``/delmes/{mid}`` —— 删除**自己**的处理记录（SQL 是**物理** ``delete``，
  见 ``FlowMessageDisposeMapper.removeFlowMessage``）；
* ``/szzdmes/{mid}`` —— 把自己那条置为只读/已读（``MSG_STATUS='1'``）。
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
from app.flow.domain.flow_message_dispose import FlowMessageDispose
from app.flow.service.flow_message_dispose_service import FlowMessageDisposeService
from app.flow.service.flow_message_dispose_service import get_service as _get_service
from app.flow.service.flow_message_dispose_service import reset_service as _reset_service
from app.framework.aspectj.log_aspect import log

logger = logging.getLogger("app.api.flow.flow_message_dispose_controller")

router = APIRouter(prefix="/flow/messagedispose", tags=["flow-message-dispose"])

#: Java: ``com.ruoyi.web.controller.flow.FlowMessageDisposeController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.flow.FlowMessageDisposeController"

#: Java: ``util.exportExcel(list, "系统消息处理人数据")``
EXPORT_SHEET_NAME = "系统消息处理人数据"

_SERVICE: Optional[FlowMessageDisposeService] = None


def _service() -> FlowMessageDisposeService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = _get_service()
    return _SERVICE


def reset_flow_message_dispose_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None
    _reset_service()


def _query(request: Request) -> FlowMessageDispose:
    """Java: 形参 ``FlowMessageDispose flowMessageDispose``（**没有** ``@RequestBody``）."""
    return bind_query_params(FlowMessageDispose, request.query_params)


DisposeParam = Annotated[FlowMessageDispose, Depends(_query)]


def _current_buss_id() -> str:
    """Java: ``SecurityUtils.getUserId() + ""`` —— ``Long`` 拼成 ``String``."""
    return str(get_user_id())


@router.get("/list", response_model=None)
def list_disposes(query: DisposeParam) -> TableDataInfo:
    """查询系统消息处理人列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_flow_message_dispose_list(query))


@router.get("/export", response_model=None)
@log(title="系统消息处理人", business_type=BusinessType.EXPORT, java_method="export")
def export(query: DisposeParam) -> AjaxResult:
    """导出系统消息处理人列表. Java: ``@GetMapping("/export")`` —— 无 ``startPage()``."""
    rows = _service().select_flow_message_dispose_list(query)
    return ExcelUtil(FlowMessageDispose).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取系统消息处理人详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_flow_message_dispose_by_id(id))


@router.post("", response_model=None)
@log(title="系统消息处理人", business_type=BusinessType.INSERT, java_method="add")
def add(entity: FlowMessageDispose) -> AjaxResult:
    """新增系统消息处理人. Java: ``@PostMapping`` + ``@RequestBody``."""
    return _service().save_flow_message_dispose(entity)


@router.put("", response_model=None)
@log(title="系统消息处理人", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: FlowMessageDispose) -> AjaxResult:
    """修改系统消息处理人. Java: ``@PutMapping`` + ``@RequestBody``."""
    return _service().save_flow_message_dispose(entity)


@router.delete("/{ids}", response_model=None)
@log(title="系统消息处理人", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除系统消息处理人. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_flow_message_dispose_by_ids(parse_str_array(ids))


@router.delete("/delmes/{mid}", response_model=None)
def remove_flow_message(mid: str) -> AjaxResult:
    """删除消息 -- 自己. Java: ``@DeleteMapping("/delmes/{mid}")``.

    Java 这里是 ``@DeleteMapping``（不是 GET），照抄。
    """
    return _service().remove_flow_message(mid, _current_buss_id())


@router.delete("/szzdmes/{mid}", response_model=None)
def szzd_flow_message(mid: str) -> AjaxResult:
    """设置已读 -- 自己. Java: ``@DeleteMapping("/szzdmes/{mid}")``."""
    return _service().save_szzd_flow_message(mid, _current_buss_id())


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "add",
    "edit",
    "export",
    "get_info",
    "list_disposes",
    "remove",
    "remove_flow_message",
    "reset_flow_message_dispose_controller",
    "szzd_flow_message",
]
