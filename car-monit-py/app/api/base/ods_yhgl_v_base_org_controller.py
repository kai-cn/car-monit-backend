"""机构信息 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsYhglVBaseOrgController.java

6 个映射，全部迁移
------------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               **无**（登录即可）
``export``                GET ``/export``             ``base:org:export``
``getInfo``               GET ``/{bigId}``            **无**
``add``                   POST ``""``                 ``base:org:add``
``edit``                  PUT ``""``                  ``base:org:edit``
``remove``                DELETE ``/{bigIds}``        ``base:org:remove``
========================  ==========================  ==============================

主键是 ``big_id``（``@TableId(type = IdType.INPUT)``），路径变量名叫 ``bigId`` /
``bigIds``，与 ``/base/fwqjcxx`` 的 ``agentPk`` 只是命名差异。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_yhgl_v_base_org import OdsYhglVBaseOrg
from app.base.service.ods_yhgl_v_base_org_service import (
    OdsYhglVBaseOrgService,
    get_ods_yhgl_v_base_org_service,
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

router = APIRouter(prefix="/base/org", tags=["base-org"])

#: Java: ``com.ruoyi.web.controller.base.OdsYhglVBaseOrgController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.OdsYhglVBaseOrgController"

#: Java: ``util.exportExcel(list, "机构信息数据")``
EXPORT_SHEET_NAME = "机构信息数据"

_SERVICE: Optional[OdsYhglVBaseOrgService] = None


def _service() -> OdsYhglVBaseOrgService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_yhgl_v_base_org_service()
    return _SERVICE


def reset_org_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> OdsYhglVBaseOrg:
    """Java: 形参 ``OdsYhglVBaseOrg x``（无 ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(OdsYhglVBaseOrg, request.query_params)


#: 查询条件实体。
OrgParam = Annotated[OdsYhglVBaseOrg, Depends(_query)]


@router.get("/list", response_model=None)
def list_orgs(query: OrgParam) -> TableDataInfo:
    """查询机构信息列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:org:export")
@log(title="机构信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: OrgParam) -> AjaxResult:
    """导出机构信息列表. Java: ``@GetMapping("/export")``."""
    rows = _service().select_list(query)
    return ExcelUtil(OdsYhglVBaseOrg).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{big_id}", response_model=None)
def get_info(big_id: str) -> AjaxResult:
    """获取机构信息详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    return AjaxResult.success_data(_service().select_by_id(big_id))


@router.post("", response_model=None)
@pre_authorize_permi("base:org:add")
@log(title="机构信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: OdsYhglVBaseOrg) -> AjaxResult:
    """新增机构信息. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:org:edit")
@log(title="机构信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: OdsYhglVBaseOrg) -> AjaxResult:
    """修改机构信息. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{big_ids}", response_model=None)
@pre_authorize_permi("base:org:remove")
@log(title="机构信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(big_ids: str) -> AjaxResult:
    """删除机构信息. Java: ``@DeleteMapping("/{bigIds}")``."""
    return _service().delete_by_ids(parse_str_array(big_ids))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "OrgParam",
    "list_orgs",
    "export",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_org_controller",
]
