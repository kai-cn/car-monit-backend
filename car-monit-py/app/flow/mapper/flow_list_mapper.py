"""审核历史记录 Mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowListMapper.java
#               ruoyi-system/src/main/resources/mapper/flow/FlowListMapper.xml

语句对照（XML id -> Python）：

    selectFlowListList     -> :meth:`select_list`（升序 ``t.create_time ASC ,t.id``）
    selectFlowListListNew  -> :meth:`select_list_new`（降序 ``t.create_time desc ,t.id``）
    selectFlowListById     -> :meth:`select_by_id`
    insertFlowList         -> :meth:`insert`
    updateFlowList         -> :meth:`update_by_id`
    deleteFlowListById(s)  -> :meth:`delete_by_id` / :meth:`delete_by_ids`

两条列表语句的 ``<if>`` 完全相同，**只差排序方向**；除 ``/flow/flowlist/list``
与 ``/flow/flowlist/listnew`` 之外没有别的调用点。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from app.base.mapper.ods_sql import If
from app.flow.domain.flow_list import FlowList
from app.flow.mapper.flow_mapper import FlowMapper

#: ``<sql id="selectFlowListVo">`` 的原文。
_SELECT_VO = (
    " t.ID, t.BILL_OID, t.BUSS_TYPE, t.TASK_ID, t.flow_ruid, t.CURRENT_OID, t.SH_USER,"
    " t.SH_KEY, t.SH_VALUE, t.SH_CONTEXT, t.BACK_COL1, t.BACK_COL2, t.BACK_COL3, t.sort,"
    " t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time"
)

#: ``selectFlowListList`` 的排序（升序）。
_ORDER_ASC = "t.create_time ASC ,t.id"

#: ``selectFlowListListNew`` 的排序（降序）。
_ORDER_DESC = "t.create_time desc ,t.id"


class FlowListMapper(FlowMapper):
    """Java: ``com.ruoyi.flow.mapper.FlowListMapper``."""

    table = "flow_list"
    entity_cls = FlowList
    select_vo = _SELECT_VO

    result_columns: Tuple[str, ...] = (
        "id",
        "bill_oid",
        "buss_type",
        "task_id",
        "flow_ruid",
        "current_oid",
        "sh_user",
        "sh_key",
        "sh_value",
        "sh_context",
        "back_col1",
        "back_col2",
        "back_col3",
        "sort",
        "eps_id",
        "del_flag",
        "create_by",
        "create_time",
        "update_by",
        "update_time",
    )

    order_by = _ORDER_ASC

    conditions: Tuple[If, ...] = (
        If("id", "id"),
        If("bill_oid", "BILL_OID"),
        If("buss_type", "BUSS_TYPE"),
        If("task_id", "TASK_ID"),
        If("flow_ruid", "flow_ruid"),
        If("current_oid", "CURRENT_OID"),
        If("sh_user", "SH_USER"),
        If("sh_key", "SH_KEY"),
        If("sh_value", "SH_VALUE"),
        If("sh_context", "SH_CONTEXT"),
        If("back_col1", "BACK_COL1"),
        If("back_col2", "BACK_COL2"),
        If("back_col3", "BACK_COL3"),
        If("sort", "sort", null_only=True),
        If("eps_id", "eps_id", null_only=True),
        If("create_by", "create_by", null_only=True),
    )

    insert_columns: Tuple[Tuple[str, str], ...] = (
        ("id", "ID"),
        ("bill_oid", "BILL_OID"),
        ("buss_type", "BUSS_TYPE"),
        ("task_id", "TASK_ID"),
        ("flow_ruid", "flow_ruid"),
        ("current_oid", "CURRENT_OID"),
        ("sh_user", "SH_USER"),
        ("sh_key", "SH_KEY"),
        ("sh_value", "SH_VALUE"),
        ("sh_context", "SH_CONTEXT"),
        ("back_col1", "BACK_COL1"),
        ("back_col2", "BACK_COL2"),
        ("back_col3", "BACK_COL3"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("create_by", "create_by"),
        ("create_time", "create_time"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    update_columns: Tuple[Tuple[str, str], ...] = (
        ("bill_oid", "BILL_OID"),
        ("buss_type", "BUSS_TYPE"),
        ("task_id", "TASK_ID"),
        ("flow_ruid", "flow_ruid"),
        ("current_oid", "CURRENT_OID"),
        ("sh_user", "SH_USER"),
        ("sh_key", "SH_KEY"),
        ("sh_value", "SH_VALUE"),
        ("sh_context", "SH_CONTEXT"),
        ("back_col1", "BACK_COL1"),
        ("back_col2", "BACK_COL2"),
        ("back_col3", "BACK_COL3"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("create_by", "create_by"),
        ("create_time", "create_time"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    # Java: List<FlowList> selectFlowListListNew(FlowList flowList)
    def select_list_new(self, query: FlowList) -> List[FlowList]:
        """同一条 ``<if>`` 列表，排序反过来（XML 里单独写了一份语句）。"""
        return self.select_list(query, order_by=_ORDER_DESC)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_MAPPER: Optional[FlowListMapper] = None


def get_mapper() -> FlowListMapper:
    global _DEFAULT_MAPPER
    if _DEFAULT_MAPPER is None:
        _DEFAULT_MAPPER = FlowListMapper()
    return _DEFAULT_MAPPER


__all__ = ["FlowListMapper", "get_mapper"]
