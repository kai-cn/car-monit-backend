"""查询日志 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarQueryLogMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarQueryLogMapper.xml

标准 ``manager`` 模板：9 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.car_query_log import CarQueryLog
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarQueryLogVo">``
SELECT_CAR_QUERY_LOG_VO = """
        t.id,
        t.user_id,
        t.user_name,
        t.user_ip,
        t.model_type,
        t.menu_point,
        t.query_condition,
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
    "user_id",
    "user_name",
    "user_ip",
    "model_type",
    "menu_point",
    "query_condition",
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

#: ``selectCarQueryLogList`` 的 9 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("user_id", "user_id"),
    If("user_name", "user_name", like=True),
    If("user_ip", "user_ip"),
    If("model_type", "model_type"),
    If("menu_point", "menu_point"),
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


class CarQueryLogMapper(ManagerListMapper):
    """Java: ``interface CarQueryLogMapper extends BaseMapper<CarQueryLog>``."""

    table = "car_query_log"
    select_vo = SELECT_CAR_QUERY_LOG_VO
    entity_cls = CarQueryLog
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "CarQueryLogMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_QUERY_LOG_VO",
]
