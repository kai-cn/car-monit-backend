"""收费站ip 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollStationIpController.java

2 个映射，全部迁移
------------------
======  ==================  =============================
Java      Method / Path       权限点
======  ==================  =============================
``list``  GET ``/list``       **无**（登录即可）
``getInfo`` GET ``/{id}``     **无**
======  ==================  =============================

结构、权限点、路径变量类型（``Long``）与
:mod:`app.api.base.ods_szdn_gantry_ip_controller` 完全一致；差异只在实体与表名
（以及列表语句末尾那句 ``order by t.big_id``，见 mapper 的说明）。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_szdn_toll_station_ip import OdsSzdnTollStationIp
from app.base.service.ods_szdn_toll_station_ip_service import (
    OdsSzdnTollStationIpService,
    get_ods_szdn_toll_station_ip_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/tollStationIp", tags=["base-toll-station-ip"])

_SERVICE: Optional[OdsSzdnTollStationIpService] = None


def _service() -> OdsSzdnTollStationIpService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_szdn_toll_station_ip_service()
    return _SERVICE


def reset_toll_station_ip_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> OdsSzdnTollStationIp:
    """Java: 形参 ``OdsSzdnTollStationIp odsSzdnTollStationIp`` —— query 绑定。"""
    return bind_query_params(OdsSzdnTollStationIp, request.query_params)


#: 查询条件实体.
TollStationIpParam = Annotated[OdsSzdnTollStationIp, Depends(_query)]


@router.get("/list", response_model=None)
def list_toll_station_ips(query: TollStationIpParam) -> TableDataInfo:
    """查询收费站ip列表. Java: ``@GetMapping("/list")``."""
    start_page()
    rows = _service().select_list(query)
    return get_data_table(rows)


@router.get("/{id}", response_model=None)
def get_info(id: int) -> AjaxResult:
    """获取收费站ip详细信息. Java: ``@GetMapping(value = "/{id}")``."""
    return AjaxResult.success_data(_service().select_by_id(id))


__all__ = [
    "router",
    "TollStationIpParam",
    "list_toll_station_ips",
    "get_info",
    "reset_toll_station_ip_controller",
]
