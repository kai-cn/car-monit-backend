"""轨迹数据 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailTracksController.java

2 个映射，全部迁移
------------------
=========  ==================  ==========
Java        Method / Path       权限点
=========  ==================  ==========
``list``   GET ``/list``       **无**
``getInfo`` GET ``/{uuid}``     **无**
=========  ==================  ==========

注意
----
* 这里的 ``/list`` 调的是 ``selectZdataTrailTracksList``（**不是**
  ``carTrackQuery``）。``carTrackQuery`` 由 ``manager`` 包的
  ``CarTrackInfoController`` 使用，方法实现在
  :class:`~app.base.service.zdata_trail_tracks_service.ZdataTrailTracksService`。
* ``/{uuid}`` 是 ``String`` —— UUID 主键，任意字符串都不会触发类型转换错误。
* XML 的列表语句带 ``order by t.enter_time desc``，所以 ``orderByColumn`` /
  ``isAsc`` **不生效**。
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request

from app.base.domain.zdata_trail_tracks import ZdataTrailTracks
from app.base.service.zdata_trail_tracks_service import (
    ZdataTrailTracksService,
    get_zdata_trail_tracks_service,
)
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo

router = APIRouter(prefix="/base/trailtracks", tags=["base-trail-tracks"])

_SERVICE: Optional[ZdataTrailTracksService] = None


def _service() -> ZdataTrailTracksService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = get_zdata_trail_tracks_service()
    return _SERVICE


def reset_trail_tracks_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


def _query(request: Request) -> ZdataTrailTracks:
    """Java: 形参 ``ZdataTrailTracks x``（**没有** ``@RequestBody``）—— query 绑定。

    瞬态查询字段 ``carNo`` / ``applyTime1`` / ``applyTime2`` 也走这条路径
    （它们都是实体字段，``bind_query_params`` 按别名识别）。
    """
    return bind_query_params(ZdataTrailTracks, request.query_params)


#: 查询条件实体.
TrailTracksParam = Annotated[ZdataTrailTracks, Depends(_query)]


@router.get("/list", response_model=None)
def list_trail_tracks(query: TrailTracksParam) -> TableDataInfo:
    """查询轨迹数据列表. Java: ``@GetMapping("/list")``."""
    start_page()
    rows = _service().select_list(query)
    return get_data_table(rows)


@router.get("/{uuid}", response_model=None)
def get_info(uuid: str) -> AjaxResult:
    """获取轨迹数据详细信息. Java: ``@GetMapping(value = "/{uuid}")``."""
    return AjaxResult.success_data(_service().select_by_id(uuid))


__all__ = [
    "TrailTracksParam",
    "get_info",
    "list_trail_tracks",
    "reset_trail_tracks_controller",
    "router",
]
