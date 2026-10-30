"""系统消息处理人 Mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowMessageDisposeMapper.java
#               ruoyi-system/src/main/resources/mapper/flow/FlowMessageDisposeMapper.xml

语句对照（XML id -> Python）：

    selectFlowMessageDisposeList  -> :meth:`select_list`
    selectFlowMessageDisposeById  -> :meth:`select_by_id`
    insertFlowMessageDispose      -> :meth:`insert`
    updateFlowMessageDispose      -> :meth:`update_by_id`
    deleteFlowMessageDisposeById(s) -> :meth:`delete_by_id` / :meth:`delete_by_ids`（逻辑删）
    removeFlowMessage             -> :meth:`remove_flow_message`（**物理删**）
    saveSzzdFlowMessage           -> :meth:`save_szzd_flow_message`
    saveSzzdFlowMessageAll        -> :meth:`save_szzd_flow_message_all`
    updateBusinessByMessageId     -> :meth:`update_business_by_message_id`

``removeFlowMessage`` 是物理删除
-------------------------------
"删除自己的一条待办"在 XML 里是 ``<delete>``，而同一份 XML 的
``deleteFlowMessageDisposeById(s)`` 是 ``update ... set del_flag = '1'``。
两种语义并存是现状，不要统一。

``saveSzzdFlowMessageAll`` 会**改写处理人**
-----------------------------------------
``update ... set MSG_STATUS = '1', BUSS_ID = #{bussId} where ... MSG_STATUS = '2'``
—— 把一条消息里所有"未办理"的处理人都改成当前操作人并置为已办理（"全部办理"）。
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.base.mapper.ods_sql import If
from app.flow.domain.flow_message_dispose import FlowMessageDispose
from app.flow.mapper.flow_mapper import FlowMapper, execute_update

#: ``<sql id="selectFlowMessageDisposeVo">`` 的原文。
_SELECT_VO = (
    " t.ID, t.MID, t.BUSS_ID, t.BUSS_NAME, t.MSG_STATUS, t.HANG_TIME, t.DISPOSE_OTHER,"
    " t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time"
)


class FlowMessageDisposeMapper(FlowMapper):
    """Java: ``com.ruoyi.flow.mapper.FlowMessageDisposeMapper``."""

    table = "flow_message_dispose"
    entity_cls = FlowMessageDispose
    select_vo = _SELECT_VO

    result_columns: Tuple[str, ...] = (
        "id",
        "mid",
        "buss_id",
        "buss_name",
        "msg_status",
        "hang_time",
        "dispose_other",
        "sort",
        "eps_id",
        "del_flag",
        "create_by",
        "create_time",
        "update_by",
        "update_time",
    )

    order_by = "t.create_time desc,t.id"

    conditions: Tuple[If, ...] = (
        If("id", "id"),
        If("mid", "MID"),
        If("buss_id", "BUSS_ID"),
        If("buss_name", "BUSS_NAME", like=True),
        If("msg_status", "MSG_STATUS"),
        If("hang_time", "HANG_TIME", null_only=True),
        If("dispose_other", "DISPOSE_OTHER"),
        If("sort", "sort", null_only=True),
        If("eps_id", "eps_id", null_only=True),
        If("create_by", "create_by", null_only=True),
    )

    insert_columns: Tuple[Tuple[str, str], ...] = (
        ("id", "ID"),
        ("mid", "MID"),
        ("buss_id", "BUSS_ID"),
        ("buss_name", "BUSS_NAME"),
        ("msg_status", "MSG_STATUS"),
        ("hang_time", "HANG_TIME"),
        ("dispose_other", "DISPOSE_OTHER"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("create_by", "create_by"),
        ("create_time", "create_time"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    update_columns: Tuple[Tuple[str, str], ...] = (
        ("mid", "MID"),
        ("buss_id", "BUSS_ID"),
        ("buss_name", "BUSS_NAME"),
        ("msg_status", "MSG_STATUS"),
        ("hang_time", "HANG_TIME"),
        ("dispose_other", "DISPOSE_OTHER"),
        ("sort", "sort"),
        ("eps_id", "eps_id"),
        ("del_flag", "del_flag"),
        ("create_by", "create_by"),
        ("create_time", "create_time"),
        ("update_by", "update_by"),
        ("update_time", "update_time"),
    )

    # Java: int removeFlowMessage(FlowMessageDispose flowMessageDispose)
    def remove_flow_message(self, mid: str, buss_id: Optional[str]) -> int:
        """**物理删除**：``delete from flow_message_dispose where MID = ? [and BUSS_ID = ?]``。"""
        sql = "delete from flow_message_dispose where MID = :mid"
        params = {"mid": mid}
        if buss_id is not None and buss_id != "":
            sql += " and BUSS_ID = :buss_id"
            params["buss_id"] = buss_id
        return execute_update(sql, params)

    # Java: int saveSzzdFlowMessage(FlowMessageDispose flowMessageDispose)
    def save_szzd_flow_message(self, mid: str, buss_id: Optional[str]) -> int:
        """把自己那条待办置为已办理（只动 ``MSG_STATUS = '1'``，不改处理人）。"""
        sql = (
            "update flow_message_dispose set MSG_STATUS = '1' "
            "where del_flag = '0' and  MID = :mid"
        )
        params = {"mid": mid}
        if buss_id is not None and buss_id != "":
            sql += " and BUSS_ID = :buss_id"
            params["buss_id"] = buss_id
        return execute_update(sql, params)

    # Java: int saveSzzdFlowMessageAll(FlowMessageDispose flowMessageDispose)
    def save_szzd_flow_message_all(self, mid: str, buss_id: str) -> int:
        """把所有"未办理"的处理人都改成 ``bussId`` 并置为已办理。

        ``MSG_STATUS = '2'`` 这个条件很关键：已经办过的人**不会**被改写。
        """
        sql = (
            "update flow_message_dispose set MSG_STATUS = '1',BUSS_ID = :buss_id "
            "where del_flag = '0' and  MID = :mid  and MSG_STATUS = '2'"
        )
        return execute_update(sql, {"mid": mid, "buss_id": buss_id})

    # Java: int updateBusinessByMessageId(FlowMessageDispose flowMessageDispose)
    def update_business_by_message_id(self, entity: FlowMessageDispose) -> int:
        """按 ``mid`` 批量回写处理结果（``buss_name`` / ``msg_status`` / ``hang_time``）。

        无调用点（唯一调用方 ``dealBusinessMessage`` 本身没被调用），照抄保留。
        """
        sql = (
            "UPDATE flow_message_dispose SET buss_name = :buss_name,"
            " msg_status = :msg_status, hang_time = :hang_time"
            " WHERE del_flag = '0' AND mid = :mid"
        )
        params = {
            "buss_name": entity.buss_name,
            "msg_status": entity.msg_status,
            "hang_time": entity.hang_time,
            "mid": entity.mid,
        }
        return execute_update(sql, params)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_MAPPER: Optional[FlowMessageDisposeMapper] = None


def get_mapper() -> FlowMessageDisposeMapper:
    global _DEFAULT_MAPPER
    if _DEFAULT_MAPPER is None:
        _DEFAULT_MAPPER = FlowMessageDisposeMapper()
    return _DEFAULT_MAPPER


__all__ = ["FlowMessageDisposeMapper", "get_mapper"]
