"""省界设备ip 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryIpController.java

2 个映射，全部迁移
------------------
======  ==================  =============================
Java      Method / Path       权限点
======  ==================  =============================
``list``  GET ``/list``       **无**（登录即可）
``getInfo`` GET ``/{id}``     **无**
======  ==================  =============================

与 ``BaseConfigServiceAreaController`` 的差异
--------------------------------------------
1. 只有 2 个端点（没有 add / edit / remove / export / listQuery）—— 这是一张
   纯只读的配置表。
2. ``/{id}`` 的路径变量是 **``Long``**（Java ``@PathVariable("id") Long id``），
   不是业务编码。传非数字时 Java 抛 ``MethodArgumentTypeMismatchException`` ->
   全局处理器回 ``code 500``（HTTP 仍是 200）；FastAPI 侧同样回 ``code 500``。
3. 两个端点都**没有** ``@PreAuthorize`` —— 登录即可访问。
4. ``/list`` 里那行 ``setTenantId(SecurityUtils.getTenantId())`` 在 Java 里是
   **注释掉的**，所以列表不过滤租户。照抄（不要"顺手"加上）。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_szdn_gantry_ip import OdsSzdnGantryIp
from app.base.service.ods_szdn_gantry_ip_service import (
    OdsSzdnGantryIpService,
    get_ods_szdn_gantry_ip_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/gantryIp", tags=["base-gantry-ip"])

_SERVICE: Optional[OdsSzdnGantryIpService] = None


def _service() -> OdsSzdnGantryIpService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_szdn_gantry_ip_service()
    return _SERVICE


def reset_gantry_ip_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> OdsSzdnGantryIp:
    """Java: 形参 ``OdsSzdnGantryIp odsSzdnGantryIp``（**没有** ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(OdsSzdnGantryIp, request.query_params)


#: 查询条件实体.
GantryIpParam = Annotated[OdsSzdnGantryIp, Depends(_query)]


@router.get("/list", response_model=None)
def list_gantry_ips(query: GantryIpParam) -> TableDataInfo:
    """查询省界设备ip列表. Java: ``@GetMapping("/list")``."""
    start_page()
    rows = _service().select_list(query)
    return get_data_table(rows)


@router.get("/{id}", response_model=None)
def get_info(id: int) -> AjaxResult:
    """获取省界设备ip详细信息. Java: ``@GetMapping(value = "/{id}")``.

    查不到时 ``data`` 为 ``null``（HTTP 200 + ``msg: 操作成功``），不是 404。
    """
    return AjaxResult.success_data(_service().select_by_id(id))


__all__ = [
    "router",
    "GantryIpParam",
    "list_gantry_ips",
    "get_info",
    "reset_gantry_ip_controller",
]
