"""门架交易查询 Mapper.

# Migrated from: com/ruoyi/manager/mapper/GantryTradeInfoMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/GantryTradeInfoMapper.xml

标准 ``manager`` 模板：22 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.gantry_trade_info import GantryTradeInfo
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectGantryTradeInfoVo">``
SELECT_GANTRY_TRADE_INFO_VO = """
        t.id,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.car_num,
        t.in_station_id,
        t.in_station,
        t.in_time,
        t.out_station_id,
        t.out_station,
        t.out_time,
        t.charge_type,
        t.amount,
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
    "car_no",
    "car_type",
    "car_vehicle",
    "car_num",
    "in_station_id",
    "in_station",
    "in_time",
    "out_station_id",
    "out_station",
    "out_time",
    "charge_type",
    "amount",
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

#: ``selectGantryTradeInfoList`` 的 22 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("in_station_id", "in_station_id"),
    If("in_station", "in_station"),
    If("in_time", "in_time", null_only=True),
    If("out_station_id", "out_station_id"),
    If("out_station", "out_station"),
    If("out_time", "out_time", null_only=True),
    If("charge_type", "charge_type"),
    If("amount", "amount", null_only=True),
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


class GantryTradeInfoMapper(ManagerListMapper):
    """Java: ``interface GantryTradeInfoMapper extends BaseMapper<GantryTradeInfo>``."""

    table = "gantry_trade_info"
    select_vo = SELECT_GANTRY_TRADE_INFO_VO
    entity_cls = GantryTradeInfo
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "GantryTradeInfoMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_GANTRY_TRADE_INFO_VO",
]
