"""收费流水 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarFeeRecordMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarFeeRecordMapper.xml

标准 ``manager`` 模板：20 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.car_fee_record import CarFeeRecord
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarFeeRecordVo">``
SELECT_CAR_FEE_RECORD_VO = """
        t.id,
        t.car_id,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.in_station_id,
        t.in_station,
        t.in_time,
        t.out_station_id,
        t.out_station,
        t.out_time,
        t.charge_type,
        t.amount,
        t.except_id,
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

#: ``resultMap`` 的 26 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_id",
    "car_no",
    "car_type",
    "car_vehicle",
    "in_station_id",
    "in_station",
    "in_time",
    "out_station_id",
    "out_station",
    "out_time",
    "charge_type",
    "amount",
    "except_id",
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

#: ``selectCarFeeRecordList`` 的 20 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("in_station_id", "in_station_id"),
    If("in_station", "in_station"),
    If("in_time", "in_time", null_only=True),
    If("out_station_id", "out_station_id"),
    If("out_station", "out_station"),
    If("out_time", "out_time", null_only=True),
    If("charge_type", "charge_type"),
    If("amount", "amount", null_only=True),
    If("except_id", "except_id"),
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


class CarFeeRecordMapper(ManagerListMapper):
    """Java: ``interface CarFeeRecordMapper extends BaseMapper<CarFeeRecord>``."""

    table = "car_fee_record"
    select_vo = SELECT_CAR_FEE_RECORD_VO
    entity_cls = CarFeeRecord
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "CarFeeRecordMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_FEE_RECORD_VO",
]
