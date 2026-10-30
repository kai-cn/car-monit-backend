"""我的申请 Mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowApplyInfoMapper.java
#               ruoyi-system/src/main/resources/mapper/flow/FlowApplyInfoMapper.xml

语句对照（XML id -> Python）：

    selectFlowApplyInfoList    -> :meth:`select_list`（继承）
    selectFlowApplyInfoById    -> :meth:`select_by_id`（继承）
    insertFlowApplyInfo        -> :meth:`insert`（继承，XML 语义）
    updateFlowApplyInfo        -> :meth:`update_by_id`（继承，XML 语义）
    deleteFlowApplyInfoById(s) -> :meth:`delete_by_id` / :meth:`delete_by_ids`（继承，逻辑删）
    selectByBillId             -> :meth:`select_by_bill_id`

两处照抄出来的怪癖
------------------
1. 列表语句比 ``<sql>`` 多带一列：``,t.BACK_COL1 auitEmpName`` —— 同一个值出现在
   ``BACK_COL1`` 和别名里，前端读 ``auitEmpName``（见 :mod:`app.flow.mapper.flow_mapper`）。
2. ``selectByBillId`` 的条件写的是 ``t.del_flag = 0``（**数字**，其它语句都是 ``'0'``
   字符串）。MySQL 会隐式转换，结果一样，但 XML 原文如此，这里保留。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.mapper.ods_sql import If
from app.flow.domain.flow_apply_info import FlowApplyInfo
from app.flow.mapper.flow_mapper import FlowMapper, execute_rows

#: ``<sql id="selectFlowApplyInfoVo">`` 的原文。
_SELECT_VO = (
    " t.ID, t.entrust_info, t.BILL_OID, t.BUSS_TYPE, t.FLOW_RUID, t.MSG_TITLE,"
    " t.MSG_CONTEXT, t.MSG_TYPE, t.MSG_URL, t.APPLY_NAME,"
    " t.CURRENT_OID, t.PC_OID, t.BACK_COL1, t.BACK_COL2, t.BACK_COL3, t.FLOW_STATUS,"
    " t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time"
)


class FlowApplyInfoMapper(FlowMapper):
    """Java: ``com.ruoyi.flow.mapper.FlowApplyInfoMapper``."""

    table = "flow_apply_info"
    entity_cls = FlowApplyInfo
    select_vo = _SELECT_VO

    result_columns: Tuple[str, ...] = (
        "id",
        "bill_oid",
        "buss_type",
        "flow_ruid",
        "msg_title",
        "msg_context",
        "msg_type",
        "msg_url",
        "apply_name",
        "current_oid",
        "pc_oid",
        "back_col1",
        "back_col2",
        "back_col3",
        "flow_status",
        "sort",
        "eps_id",
        "del_flag",
        "create_by",
        "create_time",
        "update_by",
        "update_time",
        "entrust_info",
    )

    #: XML: ``<include refid="selectFlowApplyInfoVo"/>,t.BACK_COL1 auitEmpName``
    select_suffix = ",t.BACK_COL1 auitEmpName"
    extra_properties: Tuple[str, ...] = ("auit_emp_name",)

    order_by = "t.create_time desc,t.id"

    conditions: Tuple[If, ...] = (
        If("id", "id"),
        If("bill_oid", "BILL_OID"),
        If("buss_type", "BUSS_TYPE"),
        If("flow_ruid", "FLOW_RUID"),
        If("msg_title", "MSG_TITLE", like=True),
        If("msg_context", "MSG_CONTEXT", like=True),
        If("msg_type", "MSG_TYPE"),
        If("msg_url", "MSG_URL"),
        If("apply_name", "APPLY_NAME", like=True),
        If("current_oid", "CURRENT_OID"),
        If("pc_oid", "PC_OID"),
        If("back_col1", "BACK_COL1"),
        If("back_col2", "BACK_COL2"),
        If("back_col3", "BACK_COL3"),
        If("flow_status", "FLOW_STATUS"),
        If("sort", "sort", null_only=True),
        If("eps_id", "eps_id", null_only=True),
        If("create_by", "create_by", null_only=True),
    )

    insert_columns: Tuple[Tuple[str, str], ...] = (
        ("id", "ID"),
        ("entrust_info", "entrust_info"),
        ("bill_oid", "BILL_OID"),
        ("buss_type", "BUSS_TYPE"),
        ("flow_ruid", "FLOW_RUID"),
        ("msg_title", "MSG_TITLE"),
        ("msg_context", "MSG_CONTEXT"),
        ("msg_type", "MSG_TYPE"),
        ("msg_url", "MSG_URL"),
        ("apply_name", "APPLY_NAME"),
        ("current_oid", "CURRENT_OID"),
        ("pc_oid", "PC_OID"),
        ("back_col1", "BACK_COL1"),
        ("back_col2", "BACK_COL2"),
        ("back_col3", "BACK_COL3"),
        ("flow_status", "FLOW_STATUS"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("create_by", "create_by"),
        ("create_time", "create_time"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    #: 与 insert 同序，但**少了** ``id``（XML 的 ``<trim prefix="SET">`` 里没有它）。
    update_columns: Tuple[Tuple[str, str], ...] = (
        ("bill_oid", "BILL_OID"),
        ("entrust_info", "entrust_info"),
        ("buss_type", "BUSS_TYPE"),
        ("flow_ruid", "FLOW_RUID"),
        ("msg_title", "MSG_TITLE"),
        ("msg_context", "MSG_CONTEXT"),
        ("msg_type", "MSG_TYPE"),
        ("msg_url", "MSG_URL"),
        ("apply_name", "APPLY_NAME"),
        ("current_oid", "CURRENT_OID"),
        ("pc_oid", "PC_OID"),
        ("back_col1", "BACK_COL1"),
        ("back_col2", "BACK_COL2"),
        ("back_col3", "BACK_COL3"),
        ("flow_status", "FLOW_STATUS"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("create_by", "create_by"),
        ("create_time", "create_time"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    # Java: FlowApplyInfo selectByBillId(String billId)
    def select_by_bill_id(self, bill_id: str) -> Optional[FlowApplyInfo]:
        """按业务单据查申请 —— 注意条件里的 ``del_flag = 0`` 是**数字**。

        Java 接口返回值是单个 ``FlowApplyInfo``（MyBatis 走 ``selectOne``）：无行返回
        ``null``，多于一行抛 ``TooManyResultsException``。这里取首行 —— 唯一调用方
        ``submitEntrustFlow`` 只判空，一行与多行的可见差异是拿哪一条的历史。
        """
        sql = (
            f"SELECT {self.select_vo} FROM flow_apply_info t "
            f"WHERE t.del_flag = 0 AND t.bill_oid = :billId"
        )
        rows = execute_rows(sql, {"billId": bill_id})
        return None if not rows else self.map_row(rows[0])


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_MAPPER: Optional[FlowApplyInfoMapper] = None


def get_mapper() -> FlowApplyInfoMapper:
    global _DEFAULT_MAPPER
    if _DEFAULT_MAPPER is None:
        _DEFAULT_MAPPER = FlowApplyInfoMapper()
    return _DEFAULT_MAPPER


__all__ = ["FlowApplyInfoMapper", "get_mapper"]
