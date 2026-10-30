"""路段信息控制器 —— 生成器模板 + ExcelUtil 导出.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnSectionController.java

**7** 个映射
------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               **无**（登录即可）
``listAll``               GET ``/listAll``            **无**
``export``                GET ``/export``             ``base:section:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``base:section:add``
``edit``                  PUT ``""``                  ``base:section:edit``
``remove``                DELETE ``/{ids}``           ``base:section:remove``
========================  ==========================  ==============================

``list`` 与 ``listAll`` 查的是**同一条语句**、都 ``startPage()``，唯一区别是注释掉的
``setTenantId`` 只出现在 ``list`` 里 —— 两边都不做租户过滤，所以行为完全一致
（Java 原样如此，不改）。

``export`` 走的是 ``ExcelUtil``（**不是** easypoi 模板）
-------------------------------------------------------
``util.exportExcel(list, "路段信息数据")`` 生成文件落到 ``{download}/``、把**文件名放在
``msg``** 里返回（``AjaxResult.success(String)`` 的重载决议），客户端再走
``GET /common/download?fileName=...`` 取内容。详见 :mod:`app.common.utils.poi.excel_util`。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_szdn_section import OdsSzdnSection
from app.base.service.ods_szdn_section_service import (
    OdsSzdnSectionService,
    get_ods_szdn_section_service,
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

router = APIRouter(prefix="/base/section", tags=["base-section"])

#: Java: ``com.ruoyi.web.controller.base.OdsSzdnSectionController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.OdsSzdnSectionController"

#: Java: ``util.exportExcel(list, "路段信息数据")``
EXPORT_SHEET_NAME = "路段信息数据"

_SERVICE: Optional[OdsSzdnSectionService] = None


def _service() -> OdsSzdnSectionService:
    """Java: ``@Autowired IOdsSzdnSectionService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_szdn_section_service()
    return _SERVICE


def reset_section_controller(service: Optional[OdsSzdnSectionService] = None) -> None:
    """Test helper: drop / inject the cached collaborator."""
    global _SERVICE
    _SERVICE = service


def _query(request: Request) -> OdsSzdnSection:
    """Java: 形参 ``OdsSzdnSection odsSzdnSection``（无 ``@RequestBody``）—— query 绑定."""
    return bind_query_params(OdsSzdnSection, request.query_params)


SectionParam = Annotated[OdsSzdnSection, Depends(_query)]


@router.get("/list", response_model=None)
def list_sections(query: SectionParam) -> TableDataInfo:
    """查询路段信息列表. Java: ``@GetMapping("/list")``."""
    start_page()
    # Java: // odsSzdnSection.setTenantId(SecurityUtils.getTenantId()); —— 注释掉的租户过滤
    return get_data_table(_service().select_list(query))


@router.get("/listAll", response_model=None)
def list_all_sections(query: SectionParam) -> TableDataInfo:
    """查询路段信息列表：选择弹窗. Java: ``@GetMapping("/listAll")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:section:export")
@log(title="路段信息", business_type=BusinessType.EXPORT, java_method="export")
def export(query: SectionParam) -> AjaxResult:
    """导出路段信息列表. Java: ``@GetMapping("/export")``."""
    rows = _service().select_list(query)
    return ExcelUtil(OdsSzdnSection).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:  # noqa: A002 —— 形参名照抄 Java 的 ``String id``
    """获取路段信息详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("base:section:add")
@log(title="路段信息", business_type=BusinessType.INSERT, java_method="add")
def add(entity: OdsSzdnSection) -> AjaxResult:
    """新增路段信息. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:section:edit")
@log(title="路段信息", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: OdsSzdnSection) -> AjaxResult:
    """修改路段信息. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("base:section:remove")
@log(title="路段信息", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除路段信息. Java: ``@DeleteMapping("/{ids}")`` —— ``String[]``."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "EXPORT_SHEET_NAME",
    "SectionParam",
    "add",
    "edit",
    "export",
    "get_info",
    "list_all_sections",
    "list_sections",
    "remove",
    "reset_section_controller",
    "router",
]
