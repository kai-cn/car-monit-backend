"""常用路线 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarRouteInfoMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarRouteInfoMapper.xml

标准 ``manager`` 模板：22 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.car_route_info import CarRouteInfo
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarRouteInfoVo">``
SELECT_CAR_ROUTE_INFO_VO = """
        t.id,
        t.car_id,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.car_num,
        t.start_address,
        t.start_longitude,
        t.start_latitude,
        t.end_address,
        t.end_longitude,
        t.end_latitude,
        t.route_detail,
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

#: ``resultMap`` 的 25 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_id",
    "car_no",
    "car_type",
    "car_vehicle",
    "car_num",
    "start_address",
    "start_longitude",
    "start_latitude",
    "end_address",
    "end_longitude",
    "end_latitude",
    "route_detail",
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

#: ``selectCarRouteInfoList`` 的 22 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("start_address", "start_address"),
    If("start_longitude", "start_longitude"),
    If("start_latitude", "start_latitude"),
    If("end_address", "end_address"),
    If("end_longitude", "end_longitude"),
    If("end_latitude", "end_latitude"),
    If("route_detail", "route_detail"),
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


class CarRouteInfoMapper(ManagerListMapper):
    """Java: ``interface CarRouteInfoMapper extends BaseMapper<CarRouteInfo>``."""

    table = "car_route_info"
    select_vo = SELECT_CAR_ROUTE_INFO_VO
    entity_cls = CarRouteInfo
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "CarRouteInfoMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_ROUTE_INFO_VO",
]
