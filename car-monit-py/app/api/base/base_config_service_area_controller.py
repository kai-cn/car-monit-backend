"""服务区 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/BaseConfigServiceAreaController.java

7 个映射，全部迁移
------------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``base:configServiceArea:list``
``listQuery``             GET ``/listQuery``          **无**（登录即可）
``export``                GET ``/export``             ``base:configServiceArea:export``
``getInfo``               GET ``/{fwqbm}``            **无**
``add``                   POST ``""``                 ``base:configServiceArea:add``
``edit``                  PUT ``""``                  ``base:configServiceArea:edit``
``remove``                DELETE ``/{fwqbms}``        ``base:configServiceArea:remove``
========================  ==========================  ==============================

三个坑
------
1. ``/{fwqbm}`` 是 **String** 路径变量 —— 它会吃掉所有单段路径（含 ``/export``、
   ``/list``、``/listQuery``），所以字面量路由必须排在它**前面**注册。Spring 靠
   ``AntPathMatcher`` 的"字面量优先"天然成立，FastAPI 靠注册顺序。
2. ``export`` 返回的是**文件名**（落在 ``msg``，没有 ``data`` 键），文件写到
   ``{ruoyi.profile}/download/``，前端再去 ``GET /common/download`` 取。
3. ``add`` / ``edit`` 调的是**同一个** ``saveBaseConfigServiceArea``：``id`` 非空
   就走更新。所以 ``PUT`` 不带 ``id`` 等于新增，而 ``POST`` 带 ``id`` 等于更新。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.base_config_service_area import BaseConfigServiceArea
from app.base.service.base_config_service_area_service import (
    BaseConfigServiceAreaService,
    get_base_config_service_area_service,
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

router = APIRouter(prefix="/base/configServiceArea", tags=["base-config-service-area"])

#: Java: ``com.ruoyi.web.controller.base.BaseConfigServiceAreaController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.BaseConfigServiceAreaController"

#: Java: ``util.exportExcel(list, "服务区数据")`` —— sheet 名与文件名前缀。
EXPORT_SHEET_NAME = "服务区数据"

_SERVICE: Optional[BaseConfigServiceAreaService] = None


def _service() -> BaseConfigServiceAreaService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_base_config_service_area_service()
    return _SERVICE


def reset_config_service_area_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> BaseConfigServiceArea:
    """Java: 形参 ``BaseConfigServiceArea x``（**没有** ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(BaseConfigServiceArea, request.query_params)


#: 查询条件实体。
ConfigServiceAreaParam = Annotated[BaseConfigServiceArea, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("base:configServiceArea:list")
def list_config_service_areas(query: ConfigServiceAreaParam) -> TableDataInfo:
    """查询服务区列表. Java: ``@GetMapping("/list")``.

    Java 里那行 ``setTenantId(SecurityUtils.getTenantId())`` 是**注释掉的**，
    所以列表跨租户可见。照抄。
    """
    start_page()
    rows = _service().select_list(query)
    return get_data_table(rows)


@router.get("/listQuery", response_model=None)
def list_query(query: ConfigServiceAreaParam) -> AjaxResult:
    """查询服务区列表（无权限点、**不分页**）. Java: ``@GetMapping("/listQuery")``.

    ``data`` 是数组；与 ``/list`` 的区别只是没有 ``startPage()``，所以没有
    ``total`` / ``rows`` 信封。
    """
    return AjaxResult.success_data(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:configServiceArea:export")
@log(title="服务区", business_type=BusinessType.EXPORT, java_method="export")
def export(query: ConfigServiceAreaParam) -> AjaxResult:
    """导出服务区列表. Java: ``@GetMapping("/export")``.

    **不受分页影响**（Java 没有 ``startPage()``），返回体只有 ``code`` / ``msg``。
    """
    rows = _service().select_list(query)
    return ExcelUtil(BaseConfigServiceArea).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{fwqbm}", response_model=None)
def get_info(fwqbm: str) -> AjaxResult:
    """获取服务区详细信息. Java: ``@GetMapping(value = "/{fwqbm}")``.

    ``fwqbm`` 是**业务编码**而不是 UUID 主键；查不到时 ``data`` 为 ``null``。
    """
    return AjaxResult.success_data(_service().select_by_id(fwqbm))


@router.post("", response_model=None)
@pre_authorize_permi("base:configServiceArea:add")
@log(title="服务区", business_type=BusinessType.INSERT, java_method="add")
def add(entity: BaseConfigServiceArea) -> AjaxResult:
    """新增服务区. Java: ``@PostMapping public AjaxResult add(@RequestBody ...)``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:configServiceArea:edit")
@log(title="服务区", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: BaseConfigServiceArea) -> AjaxResult:
    """修改服务区. Java: ``@PutMapping public AjaxResult edit(@RequestBody ...)``."""
    return _service().save(entity)


@router.delete("/{fwqbms}", response_model=None)
@pre_authorize_permi("base:configServiceArea:remove")
@log(title="服务区", business_type=BusinessType.DELETE, java_method="remove")
def remove(fwqbms: str) -> AjaxResult:
    """删除服务区. Java: ``@DeleteMapping("/{fwqbms}") public AjaxResult remove(@PathVariable String[] fwqbms)``.

    路径变量是 **``String[]``**（不是 ``Long[]``），所以非 UUID 的业务编码照收；
    走 :func:`parse_str_array` 而不是 ``parse_id_array``。
    """
    return _service().delete_by_ids(parse_str_array(fwqbms))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "ConfigServiceAreaParam",
    "list_config_service_areas",
    "list_query",
    "export",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_config_service_area_controller",
]
