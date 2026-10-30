"""车辆行驶轨迹 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarTrackInfoMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarTrackInfoMapper.xml

``manager`` 模板的**唯一例外**：排序是 ``order by t.create_time,t.id``（**没有**
``desc``），其余（``WHERE t.del_flag = '0'`` + 22 条 ``<if>`` + 逻辑删）照旧。
拼装逻辑见 :class:`~app.manager.mapper.manager_mapper.ManagerListMapper`。

``selectCarTrackInfoVo`` 不投影 ``t.track_josn``，只有详情语句在末尾补
``,t.track_josn``（见 ``detail_suffix``）。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.car_track_info import CarTrackInfo
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarTrackInfoVo">``
SELECT_CAR_TRACK_INFO_VO = """
        t.id,
        t.car_id,
        t.car_no,
        t.longitude,
        t.latitude,
        t.device_type,
        t.device_no,
        t.lane_no,
        t.snap_time,
        t.receive_time,
        t.snap_pic,
        t.road_section_id,
        t.road_section_name,
        t.track_id,
        t.back_col1,
        t.back_col2,
        t.remark,
        t.status,
        t.sort,
        t.eps_id,
        t.del_flag,
        t.create_by,
        t.create_time,
        t.update_by,
        t.update_time,
        t.tenant_id
"""

#: ``resultMap`` 的 26 列（比投影多一个 ``track_josn``）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_id",
    "car_no",
    "longitude",
    "latitude",
    "device_type",
    "device_no",
    "lane_no",
    "snap_time",
    "receive_time",
    "snap_pic",
    "road_section_id",
    "road_section_name",
    "track_id",
    "track_josn",
    "back_col1",
    "back_col2",
    "remark",
    "status",
    "sort",
    "eps_id",
    "del_flag",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "tenant_id",
)

#: ``selectCarTrackInfoList`` 的 22 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("longitude", "longitude"),
    If("latitude", "latitude"),
    If("device_type", "device_type"),
    If("device_no", "device_no"),
    If("lane_no", "lane_no"),
    If("snap_time", "snap_time", null_only=True),
    If("receive_time", "receive_time", null_only=True),
    If("snap_pic", "snap_pic"),
    If("road_section_id", "road_section_id"),
    If("road_section_name", "road_section_name", like=True),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
    If(
        "apply_time1",
        "create_time",
        template="and t.create_time >= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
    If(
        "apply_time2",
        "create_time",
        template="and t.create_time <= STR_TO_DATE({p},'%Y-%m-%d %H:%i:%s')",
    ),
)


class CarTrackInfoMapper(ManagerListMapper):
    """Java: ``interface CarTrackInfoMapper extends BaseMapper<CarTrackInfo>``."""

    table = "car_track_info"
    select_vo = SELECT_CAR_TRACK_INFO_VO
    entity_cls = CarTrackInfo
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    #: Java: ``order by t.create_time,t.id`` —— 升序（别的 manager XML 都是 ``desc``）
    order_by = "t.create_time,t.id"
    #: Java: 详情语句末尾的 ``,t.track_josn``
    detail_suffix = ",t.track_josn"


__all__ = [
    "CarTrackInfoMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_TRACK_INFO_VO",
]
