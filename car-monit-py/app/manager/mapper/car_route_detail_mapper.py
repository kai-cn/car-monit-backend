"""常用路线明细 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarRouteDetailMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarRouteDetailMapper.xml

标准 ``manager`` 模板：31 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.car_route_detail import CarRouteDetail
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarRouteDetailVo">``
SELECT_CAR_ROUTE_DETAIL_VO = """
        t.id,
        t.route_id,
        t.car_id,
        t.car_no,
        t.data_source,
        t.data_source_name,
        t.last_pass_time,
        t.last_pass_picture,
        t.last_pass_type,
        t.last_pass_address,
        t.last_pass_longitude,
        t.last_pass_latitude,
        t.last_pass_cardirection,
        t.road_section_id,
        t.road_section_name,
        t.next_pass_time,
        t.next_pass_type,
        t.next_pass_address,
        t.next_pass_longitude,
        t.next_pass_latitude,
        t.org_id,
        t.org_name,
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

#: ``resultMap`` 的 34 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "route_id",
    "car_id",
    "car_no",
    "data_source",
    "data_source_name",
    "last_pass_time",
    "last_pass_picture",
    "last_pass_type",
    "last_pass_address",
    "last_pass_longitude",
    "last_pass_latitude",
    "last_pass_cardirection",
    "road_section_id",
    "road_section_name",
    "next_pass_time",
    "next_pass_type",
    "next_pass_address",
    "next_pass_longitude",
    "next_pass_latitude",
    "org_id",
    "org_name",
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

#: ``selectCarRouteDetailList`` 的 31 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("route_id", "route_id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("data_source", "data_source"),
    If("data_source_name", "data_source_name", like=True),
    If("last_pass_time", "last_pass_time", null_only=True),
    If("last_pass_picture", "last_pass_picture"),
    If("last_pass_type", "last_pass_type"),
    If("last_pass_address", "last_pass_address"),
    If("last_pass_longitude", "last_pass_longitude"),
    If("last_pass_latitude", "last_pass_latitude"),
    If("last_pass_cardirection", "last_pass_cardirection"),
    If("road_section_id", "road_section_id"),
    If("road_section_name", "road_section_name", like=True),
    If("next_pass_time", "next_pass_time", null_only=True),
    If("next_pass_type", "next_pass_type"),
    If("next_pass_address", "next_pass_address"),
    If("next_pass_longitude", "next_pass_longitude"),
    If("next_pass_latitude", "next_pass_latitude"),
    If("org_id", "org_id"),
    If("org_name", "org_name", like=True),
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


class CarRouteDetailMapper(ManagerListMapper):
    """Java: ``interface CarRouteDetailMapper extends BaseMapper<CarRouteDetail>``."""

    table = "car_route_detail"
    select_vo = SELECT_CAR_ROUTE_DETAIL_VO
    entity_cls = CarRouteDetail
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "CarRouteDetailMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_ROUTE_DETAIL_VO",
]
