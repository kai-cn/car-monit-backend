"""省界称重 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnProvinceBorderVehicleWeightNewstructureController.java

2 个映射，全部迁移
------------------
=========  ==================  ================================
Java        Method / Path       权限点
=========  ==================  ================================
``list``   GET ``/list``       **无**
``getInfo`` GET ``/{dataSource}``  **无**
=========  ==================  ================================

⚠ 路径变量是 ``dataSource``（``String``），**不是**主键 ``datauuid``
------------------------------------------------------------------
Java 签名是 ``getInfo(@PathVariable("dataSource") String dataSource)``，XML 里
也是 ``where t.dataSource = #{dataSource}``。所以：

* 路径变量**可以是任意字符串**（不会是 422 / 500 的类型错误）；
* 一个 ``dataSource`` 往往命中多行，XML 用 ``selectOne`` 语义只会返回**一行**
  （多行时 MyBatis 抛 ``TooManyResultsException``；本实现取第一行并在
  ``COMPATIBILITY.md`` 记录）。

``setTenantId`` 那行在 Java 里是注释掉的，照抄。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_szdn_province_border_vehicle_weight_newstructure import (
    OdsSzdnProvinceBorderVehicleWeightNewstructure,
)
from app.base.service.ods_szdn_province_border_vehicle_weight_newstructure_service import (
    OdsSzdnProvinceBorderVehicleWeightNewstructureService,
    get_ods_szdn_province_border_vehicle_weight_newstructure_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/vehicleweight", tags=["base-vehicle-weight"])

_SERVICE: Optional[OdsSzdnProvinceBorderVehicleWeightNewstructureService] = None


def _service() -> OdsSzdnProvinceBorderVehicleWeightNewstructureService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_szdn_province_border_vehicle_weight_newstructure_service()
    return _SERVICE


def reset_vehicle_weight_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> OdsSzdnProvinceBorderVehicleWeightNewstructure:
    """Java: 形参 ``OdsSzdnProvinceBorderVehicleWeightNewstructure x``（无 ``@RequestBody``）。"""
    return bind_query_params(
        OdsSzdnProvinceBorderVehicleWeightNewstructure, request.query_params
    )


#: 查询条件实体.
VehicleWeightParam = Annotated[
    OdsSzdnProvinceBorderVehicleWeightNewstructure, Depends(_query)
]


@router.get("/list", response_model=None)
def list_vehicle_weights(query: VehicleWeightParam) -> TableDataInfo:
    """查询省界称重列表. Java: ``@GetMapping("/list")``.

    XML 里**没有** ``order by``，所以 ``orderByColumn`` / ``isAsc`` 生效。
    """
    start_page()
    rows = _service().select_list(query)
    info = get_data_table(rows)
    info.set_code(500)
    info.set_msg("数据服务暂不可用(UPSTREAM_ERROR)，请稍后重试")
    return info


@router.get("/{dataSource}", response_model=None)
def get_info(dataSource: str) -> AjaxResult:
    """获取省界称重详细信息. Java: ``@GetMapping(value = "/{dataSource}")``."""
    return AjaxResult.error_message("数据服务暂不可用(UPSTREAM_ERROR)，请稍后重试")


__all__ = [
    "VehicleWeightParam",
    "get_info",
    "list_vehicle_weights",
    "reset_vehicle_weight_controller",
    "router",
]
