"""门架抓拍流水.

# Migrated from: com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowAddcode.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsDate, OdsEpochDate
from app.common.core.domain.domain_model import DomainModel


class OdsRtSzdnSnapshotFlowAddcode(DomainModel):
    """Java: ``com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode``."""

    big_id: Optional[str] = None
    datasource: Optional[str] = None
    cameratype: Optional[str] = None
    deviceid: Optional[str] = None
    gantrycode: Optional[str] = None
    gantryname: Optional[str] = None
    roadcode: Optional[str] = None
    roadname: Optional[str] = None
    sectioncode: Optional[str] = None
    sectionname: Optional[str] = None
    tollcode: Optional[str] = None
    tollname: Optional[str] = None
    orgcode: Optional[str] = None
    orgname: Optional[str] = None
    direction: Optional[int] = None
    hexcode: Optional[str] = None
    pileno: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    deviceip: Optional[str] = None
    siteid: Optional[int] = None
    laneid: Optional[int] = None
    snapshottimeunix: Optional[int] = None
    snapshottime: OdsEpochDate = None
    receivedtimeunix: Optional[int] = None
    receivedtime: OdsDate = None
    platenumber: Optional[str] = None
    platecolor: Optional[str] = None
    platecolorcode: Optional[int] = None
    platetype: Optional[str] = None
    platetypecode: Optional[int] = None
    plateconfidence: Optional[int] = None
    carbrand: Optional[str] = None
    carcolor: Optional[str] = None
    carcolorcode: Optional[int] = None
    cartype: Optional[str] = None
    cartypecode: Optional[int] = None
    cardirection: Optional[str] = None
    snappicturepath: Optional[str] = None
    loadtime: OdsDate = None
    gradelevel: Optional[int] = None
    datauuid: Optional[str] = None
    reserve3: Optional[str] = None
    id: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    snapshottime_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    apply_time1: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    apply_time2: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    page_num: Optional[int] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    page_size: Optional[int] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    direction_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    section_code_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    type: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    code: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL


__all__ = ["OdsRtSzdnSnapshotFlowAddcode"]
