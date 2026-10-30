"""轨迹包装 VO（``TrailInfo``）—— 一条轨迹 = 轨迹对象 + 轨迹点列表 + 路线 + 设备统计.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailInfo.java

字段顺序即 JSON 顺序：``trailUuid`` / ``enterTime`` / ``tracks`` / ``trailList`` /
``raodTrailList``（原文就是 ``raod``）/ ``trailDevCountBO``。

``trailDevCountBO`` 必须显式写 ``alias``：``to_camel`` 把 ``_bo`` 拼成 ``Bo``，
而 Java 的键是**大写缩写** ``BO``。少了这个别名，``/manager/cartrackinfo/listByCarByTime``
的每一行都会同时"少一个 Java 有的键、多一个 Java 没有的键"（实测 10 处）。
同样的坑见 :mod:`app.base.domain.trail_bo` 的 ``...CaptureBO`` 系列。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.base.domain.geometry import Geometry
from app.base.domain.trail_bo import TrailBo
from app.base.domain.trail_dev_count_bo import TrailDevCountBO
from app.base.domain.zdata_trail_tracks import ZdataTrailTracks
from app.common.core.domain.domain_model import DomainModel


class TrailInfo(DomainModel):
    """Java: ``com.ruoyi.base.domain.TrailInfo``."""

    #: 轨迹 ID（实际存的是车牌号，见 ``CarTrackInfoController``）
    trail_uuid: Optional[str] = None
    #: 进入时间（分区键，月度分区粒度）
    enter_time: Optional[datetime] = None
    #: 轨迹对象
    tracks: Optional[ZdataTrailTracks] = None
    #: 轨迹详情
    trail_list: Optional[List[TrailBo]] = None
    #: 路线轨迹
    raod_trail_list: Optional[List[Geometry]] = None
    #: 设备集合
    trail_dev_count_bo: Optional[TrailDevCountBO] = Field(
        default=None, alias="trailDevCountBO"
    )


__all__ = ["TrailInfo"]
