"""流程名称 Mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowNameMapper.java
#               ruoyi-system/src/main/resources/mapper/flow/FlowNameMapper.xml

语句对照（XML id -> Python）：

    selectFlowNameList  -> :meth:`select_list`
    selectFlowNameById  -> :meth:`select_by_id`（只查主表，**不**连 ``sys_dept``）
    insertFlowName      -> :meth:`insert`
    updateFlowName      -> :meth:`update_by_id`
    deleteFlowNameById(s) -> :meth:`delete_by_id` / :meth:`delete_by_ids`
    isExitsKey          -> :meth:`is_exits_key`

三处照抄出来的怪癖
------------------
1. 列表联 ``sys_dept`` 取单位名：``IFNULL(sd.dept_name,'系统默认') tenantName``；
   而 ``<if test="tenantName != null and tenantName != ''">`` 过滤的**也是这个别名**，
   不是某个实体列。
2. ``updateFlowName`` 的 SET 里**没有** ``tenant_id`` / ``create_by`` / ``create_time``
   —— 改流程时换不了单位，也改不了创建人。
3. ``isExitsKey`` 恒定带 ``t.create_by = -1`` —— 只查"系统预置"的流程 key，
   业务侧（``createBy = userId``）建的流程不会被这个查重拦住。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.mapper.ods_sql import If
from app.flow.domain.flow_name import FlowName
from app.flow.mapper.flow_mapper import FlowMapper, execute_count

#: ``<sql id="selectFlowNameVo">`` 的原文。
_SELECT_VO = (
    " t.ID, t.FLOW_KEY, t.FLOW_TITLE, t.FLOW_CONTEXT, t.BUSS_NAME,t.sort, t.eps_id,"
    " t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time,t.tenant_id,"
    " t.flow_business_type"
)


class FlowNameMapper(FlowMapper):
    """Java: ``com.ruoyi.flow.mapper.FlowNameMapper``."""

    table = "flow_name"
    entity_cls = FlowName
    select_vo = _SELECT_VO

    result_columns: Tuple[str, ...] = (
        "id",
        "flow_key",
        "flow_title",
        "flow_context",
        "buss_name",
        "sort",
        "eps_id",
        "del_flag",
        "create_by",
        "create_time",
        "update_by",
        "update_time",
        "tenant_id",
        "flow_business_type",
    )

    #: 列表联表别名（``resultMap`` 里没有 ``tenantName``）。
    extra_properties: Tuple[str, ...] = ("tenant_name",)

    select_suffix = ",IFNULL(sd.dept_name,'系统默认') tenantName"
    from_clause = "flow_name t left join sys_dept sd on sd.dept_id = t.tenant_id"
    detail_from = "flow_name t"

    order_by = "t.tenant_id,t.flow_key,t.id"

    conditions: Tuple[If, ...] = (
        If("id", "id"),
        If("flow_business_type", "flow_business_type"),
        If("flow_key", "FLOW_KEY"),
        If("flow_title", "FLOW_TITLE", like=True),
        # 过滤的是联表别名表达式，不是实体列 -> 用 template
        If("tenant_name", "", template="and IFNULL(sd.dept_name,'系统默认') like concat('%', {p}, '%')"),
        If("flow_context", "FLOW_CONTEXT", like=True),
        If("sort", "sort", null_only=True),
        If("eps_id", "eps_id", null_only=True),
        If("create_by", "create_by", null_only=True),
        If("tenant_id", "tenant_id", null_only=True),
    )

    insert_columns: Tuple[Tuple[str, str], ...] = (
        ("id", "ID"),
        ("flow_business_type", "flow_business_type"),
        ("flow_key", "FLOW_KEY"),
        ("flow_title", "FLOW_TITLE"),
        ("flow_context", "FLOW_CONTEXT"),
        ("buss_name", "BUSS_NAME"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("create_by", "create_by"),
        ("create_time", "create_time"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
        ("tenant_id", "tenant_id"),
    )

    update_columns: Tuple[Tuple[str, str], ...] = (
        ("flow_key", "FLOW_KEY"),
        ("flow_business_type", "flow_business_type"),
        ("flow_title", "FLOW_TITLE"),
        ("flow_context", "FLOW_CONTEXT"),
        ("buss_name", "BUSS_NAME"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    # Java: int isExitsKey(FlowName flowName)
    def is_exits_key(self, query: FlowName) -> int:
        """系统预置流程 key 查重（固定 ``create_by = -1``，见模块文档）。"""
        sql = (
            "select count(1) from flow_name t "
            "where t.del_flag = '0'  and t.FLOW_KEY = :flow_key and t.create_by = -1"
        )
        params = {"flow_key": query.flow_key}
        if query.tenant_id is not None:
            sql += " and t.tenant_id = :tenant_id"
            params["tenant_id"] = query.tenant_id
        if query.id is not None and query.id != "":
            sql += " and t.id != :id"
            params["id"] = query.id
        return execute_count(sql, params)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_MAPPER: Optional[FlowNameMapper] = None


def get_mapper() -> FlowNameMapper:
    global _DEFAULT_MAPPER
    if _DEFAULT_MAPPER is None:
        _DEFAULT_MAPPER = FlowNameMapper()
    return _DEFAULT_MAPPER


__all__ = ["FlowNameMapper", "get_mapper"]
