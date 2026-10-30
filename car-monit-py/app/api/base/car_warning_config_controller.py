"""服务区判定规则 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CarWarningConfigController.java

6 个映射，全部迁移
------------------
========================  ==========================  ==============================
Java                      Method / Path               权限点
========================  ==========================  ==============================
``list``                  GET ``/list``               ``base:config:list``
``export``                GET ``/export``             ``base:config:export``
``getInfo``               GET ``/{id}``               **无**
``add``                   POST ``""``                 ``base:config:add``
``edit``                  PUT ``""``                  ``base:config:edit``
``remove``                DELETE ``/{ids}``           ``base:config:remove``
========================  ==========================  ==============================

与其它模板的四处差异
--------------------
1. ``list`` **有**权限点（``base:config:list``），其它模板的 ``list`` 都没有；
2. 保存 / 删除都会刷新 Redis 缓存（见
   :meth:`~app.base.service.car_warning_config_service.CarWarningConfigService.cache_warning_config`）；
3. 删除是**物理删除**；
4. ``selectXxxList`` 的 XML 用了 ``join base_config_service_area`` 与 ``<where>``，
   而且 ``<if>`` 引用了表里**不存在**的列 —— 见
   :mod:`app.base.mapper.car_warning_config_mapper` 的说明（原代码缺陷，照抄）。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.car_warning_config import CarWarningConfig
from app.base.service.car_warning_config_service import (
    CarWarningConfigService,
    get_car_warning_config_service,
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

router = APIRouter(prefix="/base/config", tags=["base-config"])

#: Java: ``com.ruoyi.web.controller.base.CarWarningConfigController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.base.CarWarningConfigController"

#: Java: ``util.exportExcel(list, "服务区判定规则数据")``
EXPORT_SHEET_NAME = "服务区判定规则数据"

_SERVICE: Optional[CarWarningConfigService] = None


def _service() -> CarWarningConfigService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_car_warning_config_service()
    return _SERVICE


def reset_car_warning_config_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> CarWarningConfig:
    """Java: 形参 ``CarWarningConfig x``（无 ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(CarWarningConfig, request.query_params)


#: 查询条件实体。
CarWarningConfigParam = Annotated[CarWarningConfig, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("base:config:list")
def list_car_warning_configs(query: CarWarningConfigParam) -> TableDataInfo:
    """查询服务区判定规则列表. Java: ``@GetMapping("/list")``."""
    start_page()
    return get_data_table(_service().select_list(query))


@router.get("/export", response_model=None)
@pre_authorize_permi("base:config:export")
@log(title="服务区判定规则", business_type=BusinessType.EXPORT, java_method="export")
def export(query: CarWarningConfigParam) -> AjaxResult:
    """导出服务区判定规则列表. Java: ``@GetMapping("/export")``."""
    rows = _service().select_list(query)
    return ExcelUtil(CarWarningConfig).export_excel(list(rows), EXPORT_SHEET_NAME)


@router.get("/{id}", response_model=None)
def get_info(id: str) -> AjaxResult:
    """获取服务区判定规则详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


@router.post("", response_model=None)
@pre_authorize_permi("base:config:add")
@log(title="服务区判定规则", business_type=BusinessType.INSERT, java_method="add")
def add(entity: CarWarningConfig) -> AjaxResult:
    """新增服务区判定规则. Java: ``@PostMapping``."""
    return _service().save(entity)


@router.put("", response_model=None)
@pre_authorize_permi("base:config:edit")
@log(title="服务区判定规则", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: CarWarningConfig) -> AjaxResult:
    """修改服务区判定规则. Java: ``@PutMapping``."""
    return _service().save(entity)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("base:config:remove")
@log(title="服务区判定规则", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除服务区判定规则. Java: ``@DeleteMapping("/{ids}")``（物理删除）."""
    return _service().delete_by_ids(parse_str_array(ids))


__all__ = [
    "router",
    "EXPORT_SHEET_NAME",
    "CarWarningConfigParam",
    "list_car_warning_configs",
    "export",
    "get_info",
    "add",
    "edit",
    "remove",
    "reset_car_warning_config_controller",
]
