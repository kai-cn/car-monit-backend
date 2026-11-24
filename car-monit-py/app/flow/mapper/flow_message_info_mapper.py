"""系统内部消息 Mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowMessageInfoMapper.java
#               ruoyi-system/src/main/resources/mapper/flow/FlowMessageInfoMapper.xml

语句对照（XML id -> Python）：

    selectFlowMessageInfoList  -> :meth:`select_list`（按 ``flag`` 动态变形）
    selectFlowMessageInfoById  -> :meth:`select_by_id`（**不**连表、不带别名）
    insertFlowMessageInfo      -> :meth:`insert`
    updateFlowMessageInfo      -> :meth:`update_by_id`
    deleteFlowMessageInfoById(s) -> :meth:`delete_by_id` / :meth:`delete_by_ids`

``flag`` 驱动整条语句变形（本包最"动态"的一份 XML）
--------------------------------------------------
=========================  ==========================================================
``flag``                   变化
=========================  ==========================================================
（不传 / ``""``）          只有联表别名 ``flowStatus`` / ``curEmpNames``
``mydb``（我的待办）       ``MSG_TYPE='2'`` + 存在 ``MSG_STATUS='2'`` 的处理人
``myyb``（我的已办）       ``MSG_TYPE='2'`` + 存在 ``MSG_STATUS='1'`` 的处理人
``myyj``（我的已结）       同 ``myyb``，再 ``and app.FLOW_STATUS = '3'``
``myxx``（我的消息）       ``MSG_TYPE='1'`` + 存在任一处理人，
                           **并在投影里多一列** ``msgStatus`` 子查询
=========================  ==========================================================

投影里的动态部分走 :meth:`select_suffix_for`（需要带命名参数 ``userId``），
WHERE 尾部的四段走 :meth:`fragment_before`（``anchor is None`` 即"所有 ``<if>`` 之后"）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from app.base.mapper.ods_sql import If
from app.flow.domain.flow_message_info import FlowMessageInfo
from app.flow.mapper.flow_mapper import FlowMapper

#: ``<sql id="selectFlowMessageInfoVo">`` 的原文。
_SELECT_VO = (
    " t.ID, t.message_no, t.BILL_OID, t.BUSS_TYPE, t.FLOW_RUID, t.MSG_TITLE,"
    " t.MSG_CONTEXT, t.MSG_TYPE, t.MSG_URL, t.PC_OID,"
    " t.APPLY_NAME, t.BACK_COL1, t.BACK_COL2, t.BACK_COL3, t.sort, t.eps_id, t.del_flag,"
    " t.create_by, t.create_time, t.update_by, t.update_time"
)

#: 联表带出的两列（``flag`` 无关，永远都在）。
_JOIN_SUFFIX = ",app.FLOW_STATUS flowStatus,app.BACK_COL1 curEmpNames"

#: ``myxx`` 时追加的子查询。
_MSG_STATUS_SUFFIX = (
    " ,(select t2.MSG_STATUS from flow_message_dispose t2 where t2.del_flag = '0'"
    " and t2.mid = t.id and t2.BUSS_ID = :userId) msgStatus"
)


class FlowMessageInfoMapper(FlowMapper):
    """Java: ``com.ruoyi.flow.mapper.FlowMessageInfoMapper``."""

    table = "flow_message_info"
    entity_cls = FlowMessageInfo
    select_vo = _SELECT_VO

    result_columns: Tuple[str, ...] = (
        "id",
        "message_no",
        "bill_oid",
        "buss_type",
        "flow_ruid",
        "msg_title",
        "msg_context",
        "msg_type",
        "msg_url",
        "pc_oid",
        "apply_name",
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

    #: ``resultMap`` 之外的三个别名属性（见 :mod:`app.flow.mapper.flow_mapper`）。
    extra_properties: Tuple[str, ...] = ("flow_status", "cur_emp_names", "msg_status")

    select_suffix = _JOIN_SUFFIX
    from_clause = (
        "flow_message_info t left join flow_apply_info app"
        " on app.del_flag = '0' and app.BILL_OID = t.BILL_OID"
    )
    #: 详情语句只查主表（XML: ``from flow_message_info t where t.ID = #{id}``）。
    detail_from = "flow_message_info t"

    order_by = "t.create_time desc,t.id"

    conditions: Tuple[If, ...] = (
        If("id", "id"),
        If("message_no", "message_no"),
        If("bill_oid", "BILL_OID"),
        If("buss_type", "BUSS_TYPE"),
        If("flow_ruid", "FLOW_RUID"),
        If("msg_title", "MSG_TITLE", like=True),
        If("msg_context", "MSG_CONTEXT", like=True),
        If("msg_type", "MSG_TYPE"),
        If("msg_url", "MSG_URL"),
        If("pc_oid", "PC_OID"),
        If("apply_name", "APPLY_NAME", like=True),
        If("back_col1", "BACK_COL1"),
        If("back_col2", "BACK_COL2"),
        If("back_col3", "BACK_COL3"),
        If("sort", "sort", null_only=True),
        If("eps_id", "eps_id", null_only=True),
        If("create_by", "create_by", null_only=True),
    )

    insert_columns: Tuple[Tuple[str, str], ...] = (
        ("id", "ID"),
        ("message_no", "message_no"),
        ("bill_oid", "BILL_OID"),
        ("buss_type", "BUSS_TYPE"),
        ("flow_ruid", "FLOW_RUID"),
        ("msg_title", "MSG_TITLE"),
        ("msg_context", "MSG_CONTEXT"),
        ("msg_type", "MSG_TYPE"),
        ("msg_url", "MSG_URL"),
        ("pc_oid", "PC_OID"),
        ("apply_name", "APPLY_NAME"),
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

    #: 注意 ``message_no`` 在 SET 里的位置（XML 把它排在 ``bill_oid`` 之后）。
    update_columns: Tuple[Tuple[str, str], ...] = (
        ("bill_oid", "BILL_OID"),
        ("message_no", "message_no"),
        ("buss_type", "BUSS_TYPE"),
        ("flow_ruid", "FLOW_RUID"),
        ("msg_title", "MSG_TITLE"),
        ("msg_context", "MSG_CONTEXT"),
        ("msg_type", "MSG_TYPE"),
        ("msg_url", "MSG_URL"),
        ("pc_oid", "PC_OID"),
        ("apply_name", "APPLY_NAME"),
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

    def select_suffix_for(self, query: Any) -> Tuple[str, Dict[str, Any]]:
        """``myxx`` 时投影多一列 ``msgStatus``（绑定 ``query.userId``）。"""
        if query.flag is not None and query.flag == "myxx":
            return self.select_suffix + _MSG_STATUS_SUFFIX, {"userId": query.user_id}
        return self.select_suffix, {}

    def fragment_before(
        self, anchor: Optional[str], query: Any
    ) -> Tuple[str, Dict[str, Any]]:
        """``flag`` 的四段过滤 —— 位置在全部 ``<if>`` 之后、``order by`` 之前。"""
        if anchor is not None:
            return "", {}
        flag = query.flag
        if flag is None:
            return "", {}

        # 我的待办
        if flag == "mydb":
            return (
                "and t.MSG_TYPE = '2'"
                " and  exists (select 1 from flow_message_dispose t1 where t1.del_flag = '0'"
                " and t1.mid = t.id and t1.BUSS_ID = :userId and t1.MSG_STATUS = '2')",
                {"userId": query.user_id},
            )

        # 我的已办
        if flag == "myyb":
            return (
                "and t.MSG_TYPE = '2'"
                " and  exists (select 1 from flow_message_dispose t1 where t1.del_flag = '0'"
                " and t1.mid = t.id and t1.BUSS_ID = :userId and t1.MSG_STATUS = '1')",
                {"userId": query.user_id},
            )

        # 我的已结
        if flag == "myyj":
            return (
                "and t.MSG_TYPE = '2'"
                " and  exists (select 1 from flow_message_dispose t1 where t1.del_flag = '0'"
                " and t1.mid = t.id and t1.BUSS_ID = :userId and t1.MSG_STATUS = '1')"
                " and app.FLOW_STATUS = '3'",
                {"userId": query.user_id},
            )

        # 我的消息
        if flag == "myxx":
            return (
                "and t.MSG_TYPE = '1'"
                " and  exists (select 1 from flow_message_dispose t1 where t1.del_flag = '0'"
                " and t1.mid = t.id and t1.BUSS_ID = :userId)",
                {"userId": query.user_id},
            )

        return "", {}


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_MAPPER: Optional[FlowMessageInfoMapper] = None


def get_mapper() -> FlowMessageInfoMapper:
    global _DEFAULT_MAPPER
    if _DEFAULT_MAPPER is None:
        _DEFAULT_MAPPER = FlowMessageInfoMapper()
    return _DEFAULT_MAPPER


__all__ = ["FlowMessageInfoMapper", "get_mapper"]
