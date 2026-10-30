"""服务区车辆流水 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsCxztFwqcllsController.java

2 个映射，全部迁移
------------------
=========  ======================  =============================
Java        Method / Path           权限点
=========  ======================  =============================
``list``   GET ``/list``           ``manager:fwqclls:list``（**有**）
``getInfo`` GET ``/{bigId}``        **无**
=========  ======================  =============================

⚠ 前缀是 ``/manager/fwqclls``
-----------------------------
Java 的**类**在 ``com.ruoyi.web.controller.base`` 包里（所以迁移后仍在
``app/api/base/``），但 ``@RequestMapping`` 写的是 ``/manager/fwqclls`` —— 全项目
只有这一处"包名与路径不一致"。不要因为文件在 ``base`` 目录就把它改成 ``/base/*``，
前端路由与权限点都依赖现名。

``/list`` 与同批其它 ODS 表的另外两点差异
----------------------------------------
1. **带权限点**（其它 ``/base/*`` 的只读列表都**没有** ``@PreAuthorize``）。
   权限不足时回 HTTP 200 + ``code 403``（由全局异常处理器统一改写）。
2. ``/{bigId}`` 的路径变量是 **``Long``**，传非数字 -> ``code 500``。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_cxzt_fwqclls import OdsCxztFwqclls
from app.base.service.ods_cxzt_fwqclls_service import (
    OdsCxztFwqcllsService,
    get_ods_cxzt_fwqclls_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.framework.web.service.permission_service import pre_authorize_permi

router = APIRouter(prefix="/manager/fwqclls", tags=["manager-fwqclls"])

_SERVICE: Optional[OdsCxztFwqcllsService] = None


def _service() -> OdsCxztFwqcllsService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_ods_cxzt_fwqclls_service()
    return _SERVICE


def reset_fwqclls_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> OdsCxztFwqclls:
    """Java: 形参 ``OdsCxztFwqclls x``（**没有** ``@RequestBody``）—— query 绑定。"""
    return bind_query_params(OdsCxztFwqclls, request.query_params)


#: 查询条件实体.
FwqcllsParam = Annotated[OdsCxztFwqclls, Depends(_query)]


@router.get("/list", response_model=None)
@pre_authorize_permi("manager:fwqclls:list")
def list_fwqclls(query: FwqcllsParam) -> TableDataInfo:
    """查询服务区车辆流水列表. Java: ``@GetMapping("/list")``.

    Java 里那行 ``setTenantId(SecurityUtils.getTenantId())`` 是**注释掉的**，
    所以列表跨租户可见。照抄。
    """
    start_page()
    rows = _service().select_list(query)
    return get_data_table(rows)


@router.get("/{bigId}", response_model=None)
def get_info(bigId: int) -> AjaxResult:
    """获取服务区车辆流水详细信息. Java: ``@GetMapping(value = "/{bigId}")``.

    查不到时 ``data`` 为 ``null``（HTTP 200 + ``msg: 操作成功``），不是 404。
    """
    return AjaxResult.success_data(_service().select_by_id(bigId))


__all__ = [
    "FwqcllsParam",
    "get_info",
    "list_fwqclls",
    "reset_fwqclls_controller",
    "router",
]
