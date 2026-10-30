"""车辆出入口拟合轨迹.

# Migrated from: com/ruoyi/base/domain/ZdataTrailFitting.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsDate, OdsEpochDate
from app.common.core.domain.domain_model import DomainModel


class ZdataTrailFitting(DomainModel):
    """Java: ``com.ruoyi.base.domain.ZdataTrailFitting``."""

    cid: Optional[str] = None
    enaxlecount: Optional[int] = None
    entime: OdsDate = None
    entolllaneid: Optional[str] = None
    entollstationid: Optional[str] = None
    entollstationname: Optional[str] = None
    envehicleclass: Optional[int] = None
    envehicleid: Optional[str] = None
    envehicletype: Optional[int] = None
    enweight: Optional[int] = None
    extime: OdsEpochDate = None
    extolllaneid: Optional[str] = None
    extollstationid: Optional[str] = None
    extollstationname: Optional[str] = None
    exvehicleclass: Optional[int] = None
    exvehicleid: Optional[str] = None
    exvehicletype: Optional[int] = None
    exweight: Optional[int] = None
    trailpoints: Optional[str] = None


__all__ = ["ZdataTrailFitting"]
