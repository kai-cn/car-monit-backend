"""车俩白名单 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarWhiteInfoMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarWhiteInfoMapper.xml

列表语句带两个 left join，用来算 ``createInfo``（``concat(sd.dept_name, ' ',
su.nick_name)``）—— 但这个别名**不在** ``resultMap`` 里，MyBatis 不会把它塞进
实体，所以 Java 的列表响应里 ``createInfo`` 恒为 ``null``。这里用
``select_suffix`` 保持 SQL 一致、由 ``map_row`` 丢弃该列，行为相同。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.car_white_info import CarWhiteInfo
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarWhiteInfoVo">``
SELECT_CAR_WHITE_INFO_VO = """
        t.id,
        t.plate_color,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.car_num,
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

#: ``resultMap`` 的 19 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "plate_color",
    "car_no",
    "car_type",
    "car_vehicle",
    "car_num",
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

#: ``selectCarWhiteInfoList`` 的 14 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("plate_color", "plate_color"),
    If("car_no", "car_no"),
    If("car_no_query", "car_no", like=True),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("file_ids", "file_ids"),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
)


class CarWhiteInfoMapper(ManagerListMapper):
    """Java: ``interface CarWhiteInfoMapper extends BaseMapper<CarWhiteInfo>``."""

    table = "car_white_info"
    select_vo = SELECT_CAR_WHITE_INFO_VO
    entity_cls = CarWhiteInfo
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    from_clause = (
        "car_white_info t "
        "left join sys_user su on su.user_id = t.create_by "
        "left join sys_dept sd on t.eps_id = sd.dept_id"
    )
    #: Java: `<include .../>,concat(sd.dept_name, ' ', su.nick_name) createInfo`
    select_suffix = ",concat(sd.dept_name, ' ', su.nick_name) createInfo"


__all__ = [
    "CarWhiteInfoMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_WHITE_INFO_VO",
]
