"""可疑车辆人工核实 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarSuspiciousCheckMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousCheckMapper.xml

标准 ``manager`` 模板：18 条 ``<if>`` + ``order by t.create_time,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from sqlalchemy import text

from app.base.mapper.ods_sql import If
from app.config.database import session_scope
from app.manager.domain.car_suspicious_check import CarSuspiciousCheck
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarSuspiciousCheckVo">``
SELECT_CAR_SUSPICIOUS_CHECK_VO = """
        t.id,
        t.car_id,
        t.car_no,
        t.suspicous_flag,
        t.attachments,
        t.escaped_type,
        t.back_col1,
        t.charge_amount,
        t.total_amount,
        t.back_col2,
        t.dif_amount,
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

#: ``resultMap`` 的 21 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_id",
    "car_no",
    "suspicous_flag",
    "attachments",
    "escaped_type",
    "back_col1",
    "charge_amount",
    "total_amount",
    "back_col2",
    "dif_amount",
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

#: ``selectCarSuspiciousCheckList`` 的 18 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_id", "car_id"),
    If("car_no", "car_no"),
    If("suspicous_flag", "suspicous_flag"),
    If("attachments", "attachments"),
    If("escaped_type", "escaped_type"),
    If("back_col1", "back_col1"),
    If("charge_amount", "charge_amount", null_only=True),
    If("total_amount", "total_amount", null_only=True),
    If("back_col2", "back_col2"),
    If("dif_amount", "dif_amount", null_only=True),
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


class CarSuspiciousCheckMapper(ManagerListMapper):
    """Java: ``interface CarSuspiciousCheckMapper extends BaseMapper<CarSuspiciousCheck>``."""

    table = "car_suspicious_check"
    select_vo = SELECT_CAR_SUSPICIOUS_CHECK_VO
    entity_cls = CarSuspiciousCheck
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "t.create_time,t.id"

    # Java: int deleteCarSuspiciousCheckBySuspiciousId(String fkId)
    def delete_by_suspicious_id(self, fk_id: str) -> int:
        """按可疑车辆删除核实明细 —— XML 是 ``<delete>``（**物理删除**）。"""
        sql = "delete from car_suspicious_check where car_id = :fkId"
        with session_scope() as session:
            result = session.execute(text(sql), {"fkId": fk_id})
            return result.rowcount or 0


__all__ = [
    "CarSuspiciousCheckMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_SUSPICIOUS_CHECK_VO",
]
