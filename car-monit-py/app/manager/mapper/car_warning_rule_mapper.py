"""预警规则 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarWarningRuleMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarWarningRuleMapper.xml

``manager`` 包的标准模板：``WHERE t.del_flag = '0'`` + 16 条 ``<if>`` +
``order by t.create_time desc,t.id``。拼装逻辑见
:class:`~app.manager.mapper.manager_mapper.ManagerListMapper`。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.car_warning_rule import CarWarningRule
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarWarningRuleVo">``
SELECT_CAR_WARNING_RULE_VO = """
        t.id,
        t.rule_name,
        t.notice_range_id,
        t.notice_range_anme,
        t.notice,
        t.notice_type,
        t.notice_user_id,
        t.notice_user_name,
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

#: ``resultMap`` 的 22 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "rule_name",
    "notice_range_id",
    "notice_range_anme",
    "notice",
    "notice_type",
    "notice_user_id",
    "notice_user_name",
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

#: ``selectCarWarningRuleList`` 的 16 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("rule_name", "rule_name", like=True),
    If("notice_range_id", "notice_range_id"),
    If("notice_range_anme", "notice_range_anme", like=True),
    If("notice", "notice"),
    If("notice_type", "notice_type"),
    If("notice_user_id", "notice_user_id"),
    If("notice_user_name", "notice_user_name", like=True),
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


class CarWarningRuleMapper(ManagerListMapper):
    """Java: ``interface CarWarningRuleMapper extends BaseMapper<CarWarningRule>``."""

    table = "car_warning_rule"
    select_vo = SELECT_CAR_WARNING_RULE_VO
    entity_cls = CarWarningRule
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "CarWarningRuleMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_WARNING_RULE_VO",
]
