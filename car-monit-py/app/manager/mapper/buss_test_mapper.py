"""业务测试 Mapper.

# Migrated from: com/ruoyi/manager/mapper/BussTestMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/BussTestMapper.xml

标准 ``manager`` 模板：21 条 ``<if>`` + ``order by t.create_time desc,t.id``。
"""

from __future__ import annotations

from typing import Tuple

from app.base.mapper.ods_sql import If
from app.manager.domain.buss_test import BussTest
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectBussTestVo">``
SELECT_BUSS_TEST_VO = """
        t.id,
        t.bill_name,
        t.bill_type,
        t.amount,
        t.dept_id,
        t.user_id,
        t.apply_time,
        t.apply_time2,
        t.file_ids,
        t.flow_key,
        t.flow_ruid,
        t.flow_apply_oid,
        t.flow_status,
        t.sh_time,
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
    "bill_name",
    "bill_type",
    "amount",
    "dept_id",
    "user_id",
    "apply_time",
    "apply_time2",
    "file_ids",
    "flow_key",
    "flow_ruid",
    "flow_apply_oid",
    "flow_status",
    "sh_time",
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

#: ``selectBussTestList`` 的 21 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("bill_name", "bill_name", like=True),
    If("bill_type", "bill_type"),
    If("amount", "amount", null_only=True),
    If("dept_id", "dept_id", null_only=True),
    If("user_id", "user_id", null_only=True),
    If("apply_time", "apply_time", null_only=True),
    If("apply_time2", "apply_time2", null_only=True),
    If("file_ids", "file_ids"),
    If("flow_key", "flow_key"),
    If("flow_ruid", "flow_ruid"),
    If("flow_apply_oid", "flow_apply_oid"),
    If("flow_status", "flow_status"),
    If("sh_time", "sh_time", null_only=True),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
)


class BussTestMapper(ManagerListMapper):
    """Java: ``interface BussTestMapper extends BaseMapper<BussTest>``."""

    table = "buss_test"
    select_vo = SELECT_BUSS_TEST_VO
    entity_cls = BussTest
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS


__all__ = [
    "BussTestMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_BUSS_TEST_VO",
]
