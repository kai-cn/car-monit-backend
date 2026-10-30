"""可疑车辆备份 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarSuspiciousBackMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousBackMapper.xml

标准 ``manager`` 模板：47 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.car_suspicious_back import CarSuspiciousBack
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarSuspiciousBackVo">``
SELECT_CAR_SUSPICIOUS_BACK_VO = """
        t.id,
        t.plate_color,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.car_num,
        t.pass_type,
        t.in_station_id,
        t.in_station,
        t.in_time,
        t.out_station_id,
        t.out_station,
        t.out_time,
        t.gantry_station_id,
        t.gantryt_station,
        t.gantry_time,
        t.file_ids,
        t.out_gantry_station_id,
        t.out_gantryt_station,
        t.out_gantry_time,
        t.out_file_ids,
        t.escaped_type,
        t.escaped_type_name,
        t.escaped_num,
        t.is_except,
        t.except_remark,
        t.except_file_ids,
        t.check_status,
        t.org_id,
        t.org_name,
        t.is_white,
        t.white_remark,
        t.white_file_ids,
        t.road_code,
        t.road_name,
        t.section_code,
        t.section_name,
        t.track_id,
        t.back_col1,
        t.back_col2,
        t.remark,
        t.status,
        t.sort,
        t.create_time
"""

#: ``resultMap`` 的 52 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "plate_color",
    "car_no",
    "car_type",
    "car_vehicle",
    "car_num",
    "pass_type",
    "in_station_id",
    "in_station",
    "in_time",
    "out_station_id",
    "out_station",
    "out_time",
    "gantry_station_id",
    "gantryt_station",
    "gantry_time",
    "file_ids",
    "out_gantry_station_id",
    "out_gantryt_station",
    "out_gantry_time",
    "out_file_ids",
    "escaped_type",
    "escaped_type_name",
    "escaped_num",
    "is_except",
    "except_remark",
    "except_file_ids",
    "check_status",
    "org_id",
    "org_name",
    "is_white",
    "white_remark",
    "white_file_ids",
    "road_code",
    "road_name",
    "section_code",
    "section_name",
    "track_id",
    "track_josn",
    "track_names",
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

#: ``selectCarSuspiciousBackList`` 的 47 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("plate_color", "plate_color"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("pass_type", "pass_type"),
    If("in_station_id", "in_station_id"),
    If("in_station", "in_station"),
    If("in_time", "in_time", null_only=True),
    If("out_station_id", "out_station_id"),
    If("out_station", "out_station"),
    If("out_time", "out_time", null_only=True),
    If("gantry_station_id", "gantry_station_id"),
    If("gantryt_station", "gantryt_station"),
    If("gantry_time", "gantry_time", null_only=True),
    If("file_ids", "file_ids"),
    If("out_gantry_station_id", "out_gantry_station_id"),
    If("out_gantryt_station", "out_gantryt_station"),
    If("out_gantry_time", "out_gantry_time", null_only=True),
    If("out_file_ids", "out_file_ids"),
    If("escaped_type", "escaped_type"),
    If("escaped_type_name", "escaped_type_name", like=True),
    If("escaped_num", "escaped_num", null_only=True),
    If("is_except", "is_except"),
    If("except_remark", "except_remark"),
    If("except_file_ids", "except_file_ids"),
    If("check_status", "check_status"),
    If("org_id", "org_id"),
    If("org_name", "org_name", like=True),
    If("is_white", "is_white"),
    If("white_remark", "white_remark"),
    If("white_file_ids", "white_file_ids"),
    If("road_code", "road_code"),
    If("road_name", "road_name", like=True),
    If("section_code", "section_code"),
    If("section_name", "section_name", like=True),
    If("track_id", "track_id"),
    If("track_josn", "track_josn"),
    If("track_names", "track_names"),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
)


class CarSuspiciousBackMapper(ManagerListMapper):
    """Java: ``interface CarSuspiciousBackMapper extends BaseMapper<CarSuspiciousBack>``."""

    table = "car_suspicious_back"
    select_vo = SELECT_CAR_SUSPICIOUS_BACK_VO
    entity_cls = CarSuspiciousBack
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "CarSuspiciousBackMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_SUSPICIOUS_BACK_VO",
]
