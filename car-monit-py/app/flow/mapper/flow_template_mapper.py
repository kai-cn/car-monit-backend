"""流程节点 Mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowTemplateMapper.java
#               ruoyi-system/src/main/resources/mapper/flow/FlowTemplateMapper.xml

语句对照（XML id -> Python）：

    selectFlowTemplateList  -> :meth:`select_list`（按 ``NODE_ORDER, id`` 升序）
    selectFlowTemplateById  -> :meth:`select_by_id`
    insertFlowTemplate      -> :meth:`insert`
    updateFlowTemplate      -> :meth:`update_by_id`
    deleteFlowTemplateById(s) -> :meth:`delete_by_id` / :meth:`delete_by_ids`
    isExitsKey              -> :meth:`is_exits_key`
    isExitsSort             -> :meth:`is_exits_sort`

注意
----
* 列名拼写是 ``CONFIG_CONDTION``（少一个 ``i``），与实体字段 ``configCondtion`` 对应。
* ``updateFlowTemplate`` 的 SET **不含** ``create_by`` / ``create_time``。
* 两条查重语句都是 ``count(1)`` 且排除自身（``t.id != #{id}``，仅当 ``id`` 非空）。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.mapper.ods_sql import If
from app.flow.domain.flow_template import FlowTemplate
from app.flow.mapper.flow_mapper import FlowMapper, execute_count

#: ``<sql id="selectFlowTemplateVo">`` 的原文。
_SELECT_VO = (
    " t.ID, t.FLOW_OID, t.FLOW_TYPE, t.NODE_ORDER, t.NODE_KEY, t.NODE_NAME,"
    " t.NEXT_NODE_OID, t.PREVIOUS_NODE_OID, t.RETURN_NUM, t.RETURN_NODE_OID,"
    " t.CONFIG_CONDTION, t.CONFIG_TYPE, t.CONFIG_ID, t.CONFIG_NAME, t.sort,"
    " t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time"
)


class FlowTemplateMapper(FlowMapper):
    """Java: ``com.ruoyi.flow.mapper.FlowTemplateMapper``."""

    table = "flow_template"
    entity_cls = FlowTemplate
    select_vo = _SELECT_VO

    result_columns: Tuple[str, ...] = (
        "id",
        "flow_oid",
        "flow_type",
        "node_order",
        "node_key",
        "node_name",
        "next_node_oid",
        "previous_node_oid",
        "return_num",
        "return_node_oid",
        "config_condtion",
        "config_type",
        "config_id",
        "config_name",
        "sort",
        "eps_id",
        "del_flag",
        "create_by",
        "create_time",
        "update_by",
        "update_time",
    )

    order_by = "t.NODE_ORDER ,t.id"

    conditions: Tuple[If, ...] = (
        If("id", "id"),
        If("flow_oid", "FLOW_OID"),
        If("flow_type", "FLOW_TYPE"),
        If("node_order", "NODE_ORDER", null_only=True),
        If("node_key", "NODE_KEY"),
        If("node_name", "NODE_NAME", like=True),
        If("next_node_oid", "NEXT_NODE_OID"),
        If("previous_node_oid", "PREVIOUS_NODE_OID"),
        If("return_num", "RETURN_NUM", null_only=True),
        If("return_node_oid", "RETURN_NODE_OID"),
        If("config_condtion", "CONFIG_CONDTION"),
        If("config_type", "CONFIG_TYPE"),
        If("config_id", "CONFIG_ID"),
        If("config_name", "CONFIG_NAME", like=True),
        If("sort", "sort", null_only=True),
        If("eps_id", "eps_id", null_only=True),
        If("create_by", "create_by", null_only=True),
    )

    insert_columns: Tuple[Tuple[str, str], ...] = (
        ("id", "ID"),
        ("flow_oid", "FLOW_OID"),
        ("flow_type", "FLOW_TYPE"),
        ("node_order", "NODE_ORDER"),
        ("node_key", "NODE_KEY"),
        ("node_name", "NODE_NAME"),
        ("next_node_oid", "NEXT_NODE_OID"),
        ("previous_node_oid", "PREVIOUS_NODE_OID"),
        ("return_num", "RETURN_NUM"),
        ("return_node_oid", "RETURN_NODE_OID"),
        ("config_condtion", "CONFIG_CONDTION"),
        ("config_type", "CONFIG_TYPE"),
        ("config_id", "CONFIG_ID"),
        ("config_name", "CONFIG_NAME"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("create_by", "create_by"),
        ("create_time", "create_time"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    update_columns: Tuple[Tuple[str, str], ...] = (
        ("flow_oid", "FLOW_OID"),
        ("flow_type", "FLOW_TYPE"),
        ("node_order", "NODE_ORDER"),
        ("node_key", "NODE_KEY"),
        ("node_name", "NODE_NAME"),
        ("next_node_oid", "NEXT_NODE_OID"),
        ("previous_node_oid", "PREVIOUS_NODE_OID"),
        ("return_num", "RETURN_NUM"),
        ("return_node_oid", "RETURN_NODE_OID"),
        ("config_condtion", "CONFIG_CONDTION"),
        ("config_type", "CONFIG_TYPE"),
        ("config_id", "CONFIG_ID"),
        ("config_name", "CONFIG_NAME"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    # Java: int isExitsKey(FlowTemplate flowTemplate)
    def is_exits_key(self, query: FlowTemplate) -> int:
        """同一流程内节点 key 查重。"""
        sql = (
            "select count(1) from flow_template t "
            "where t.del_flag = '0' and t.FLOW_OID = :flow_oid and t.NODE_KEY = :node_key"
        )
        params = {"flow_oid": query.flow_oid, "node_key": query.node_key}
        if query.id is not None and query.id != "":
            sql += " and t.id != :id"
            params["id"] = query.id
        return execute_count(sql, params)

    # Java: int isExitsSort(FlowTemplate flowTemplate)
    def is_exits_sort(self, query: FlowTemplate) -> int:
        """同一流程内节点顺序查重。"""
        sql = (
            "select count(1) from flow_template t "
            "where t.del_flag = '0' and t.FLOW_OID = :flow_oid and t.NODE_ORDER = :node_order"
        )
        params = {"flow_oid": query.flow_oid, "node_order": query.node_order}
        if query.id is not None and query.id != "":
            sql += " and t.id != :id"
            params["id"] = query.id
        return execute_count(sql, params)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_MAPPER: Optional[FlowTemplateMapper] = None


def get_mapper() -> FlowTemplateMapper:
    global _DEFAULT_MAPPER
    if _DEFAULT_MAPPER is None:
        _DEFAULT_MAPPER = FlowTemplateMapper()
    return _DEFAULT_MAPPER


__all__ = ["FlowTemplateMapper", "get_mapper"]
