"""门架拍识查询 Mapper.

# Migrated from: com/ruoyi/manager/mapper/GantryCarMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/GantryCarMapper.xml

标准 ``manager`` 模板：21 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.gantry_car import GantryCar
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectGantryCarVo">``
SELECT_GANTRY_CAR_VO = """
        t.id,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.car_num,
        t.in_station_id,
        t.in_station,
        t.in_time,
        t.gantry_station_id,
        t.gantryt_station,
        t.gantry_time,
        t.file_ids,
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

#: ``resultMap`` 的 24 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_no",
    "car_type",
    "car_vehicle",
    "car_num",
    "in_station_id",
    "in_station",
    "in_time",
    "gantry_station_id",
    "gantryt_station",
    "gantry_time",
    "file_ids",
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

#: ``selectGantryCarList`` 的 21 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("in_station_id", "in_station_id"),
    If("in_station", "in_station"),
    If("in_time", "in_time", null_only=True),
    If("gantry_station_id", "gantry_station_id"),
    If("gantryt_station", "gantryt_station"),
    If("gantry_time", "gantry_time", null_only=True),
    If("file_ids", "file_ids"),
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
        template="and t.create_time >= STR_TO_DATE({p},'%Y-%m-%d')",
    ),
    If(
        "apply_time2",
        "create_time",
        template="and t.create_time < date_add(STR_TO_DATE({p},'%Y-%m-%d'), interval 1 day)",
    ),
)


class GantryCarMapper(ManagerListMapper):
    """Java: ``interface GantryCarMapper extends BaseMapper<GantryCar>``."""

    table = "gantry_car"
    select_vo = SELECT_GANTRY_CAR_VO
    entity_cls = GantryCar
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "GantryCarMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_GANTRY_CAR_VO",
]
