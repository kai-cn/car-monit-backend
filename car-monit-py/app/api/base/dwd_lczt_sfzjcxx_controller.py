"""收费站基础信息 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztSfzjcxxController.java

6 个映射，全部迁移
------------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               **无**（登录即可）
``export``                GET ``/export``             ``base:sfzjcxx:export``
``getInfo``               GET ``/{agentPk}``          **无**
``add``                   POST ``""``                 ``base:sfzjcxx:add``
``edit``                  PUT ``""``                  ``base:sfzjcxx:edit``
``remove``                DELETE ``/{agentPks}``      ``base:sfzjcxx:remove``
========================  ==========================  ==============================

结构与 :mod:`app.api.base.dwd_lczt_fwqjcxx_controller` 完全一致。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.dwd_lczt_sfzjcxx import DwdLcztSfzjcxx
from app.base.service.dwd_lczt_sfzjcxx_service import (
    DwdLcztSfzjcxxService,
    get_dwd_lczt_sfzjcxx_service,
)
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
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi

router = APIRouter(prefix="/base/sfzjcxx", tags=["base-sfzjcxx"])

#: Java: ``com.ruoyi.web.controller.base.DwdLcztSfzjcxxController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.DwdLcztSfzjcxxController"

#: Java: ``util.exportExcel(list, "收费站基础信息数据")``
EXPORT_SHEET_NAME = "收费站基础信息数据"

_SERVICE: Optional[DwdLcztSfzjcxxService] = None


def _service() -> DwdLcztSfzjcxxService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_dwd_lczt_sfzjcxx_service()
    return _SERVICE


def reset_sfzjcxx_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> DwdLcztSfzjcxx:
    """Java: 形参 ``DwdLcztSfzjcxx x``（无 ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(DwdLcztSfzjcxx, request.query_params)


#: 查询条件实体。
SfzjcxxParam = Annotated[DwdLcztSfzjcxx, Depends(_query)]


@router.get("/list", response_model=None)
def list_sfzjcxx(query: SfzjcxxParam) -> TableDataInfo:
    """查询收费站基础信息列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:sfzjcxx:export")
@log(title="收费站基础信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: SfzjcxxParam) -> AjaxResult:
    """导出收费站基础信息列表. Java: ``@GetMapping("/export")``."""
    rows = _service().select_list(query)
    return ExcelUtil(DwdLcztSfzjcxx).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{agent_pk}", response_model=None)
def get_info(agent_pk: str) -> AjaxResult:
    """获取收费站基础信息详细信息. Java: ``@GetMapping(value = "/{agentPk}")``."""
    return AjaxResult.success_data(_service().select_by_id(agent_pk))


@router.post("", response_model=None)
@pre_authorize_permi("base:sfzjcxx:add")
@log(title="收费站基础信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: DwdLcztSfzjcxx) -> AjaxResult:
    """新增收费站基础信息. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:sfzjcxx:edit")
@log(title="收费站基础信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: DwdLcztSfzjcxx) -> AjaxResult:
    """修改收费站基础信息. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{agent_pks}", response_model=None)
@pre_authorize_permi("base:sfzjcxx:remove")
@log(title="收费站基础信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(agent_pks: str) -> AjaxResult:
    """删除收费站基础信息. Java: ``@DeleteMapping("/{agentPks}")``."""
    return _service().delete_by_ids(parse_str_array(agent_pks))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "SfzjcxxParam",
    "list_sfzjcxx",
    "export",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_sfzjcxx_controller",
]
