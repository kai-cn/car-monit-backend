"""流程_当前节点 Mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowCurrentNodeMapper.java
#               ruoyi-system/src/main/resources/mapper/flow/FlowCurrentNodeMapper.xml

语句对照（XML id -> Python）：

    selectFlowCurrentNodeList  -> :meth:`select_list`
    selectFlowCurrentNodeById  -> :meth:`select_by_id`
    insertFlowCurrentNode      -> :meth:`insert`
    updateFlowCurrentNode      -> :meth:`update_by_id`
    deleteFlowCurrentNodeById(s) -> :meth:`delete_by_id` / :meth:`delete_by_ids`（逻辑删）
    deleteByBillId             -> :meth:`delete_by_bill_id`（**物理删**）
    selectEmpInfoList          -> :meth:`select_emp_info_list`
    updateFlowTable            -> :meth:`update_flow_table`
    selectUserListByRole       -> :meth:`select_user_list_by_role`
    selectUserListByDept       -> :meth:`select_user_list_by_dept`

三处必须照抄的"坏味道"
----------------------
1. ``deleteByBillId`` 是 ``<delete>``（物理删除），而上面两条是按 ``del_flag`` 的逻辑删。
   重新提交申请时整条流程轨迹会被真删掉，这是现状。
2. ``updateFlowTable`` 用 ``${tableName}`` **字符串拼接**表名（不是 ``#{}`` 绑定）。
   业务表名来自调用方（``FlowCurrentNode#tableName``），SQL 注入面与 Java 一致。
3. ``updateFlowTable`` 里 ``<if test="flowStatus != null and flowStatus == 3">`` 是
   ``String`` 与 ``int`` 比较，OGNL 会做数值强制转换 —— 只有 ``"3"`` 命中。
   （真传了非数字串，OGNL 抛 ``NumberFormatException``；这里只认 ``"3"``，不抛。）
4. ``selectEmpInfoList`` 的 ``dutyAudit`` 分支把 ``${backCol1}`` 当**表名**拼进去
   （``clean`` 之外的另一条注入面）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.base.mapper.ods_sql import If, map_result_row
from app.flow.domain.flow_current_node import FlowCurrentNode
from app.flow.mapper.flow_mapper import FlowMapper, execute_rows, execute_update

#: ``<sql id="selectFlowCurrentNodeVo">`` 的原文。
_SELECT_VO = (
    " t.ID, t.FLOW_OID, t.CURRENT_OID, t.NODE_ORDER, t.NODE_KEY, t.NODE_NAME,"
    " t.CONFIG_TYPE, t.CONFIG_ID, t.CONFIG_NAME, t.BILL_OID, t.AUIT_EMP_OID, t.AUIT_EMP_NAME,"
    " t.BACK_COL1, t.BACK_COL2, t.BACK_COL3, t.sort, t.eps_id, t.del_flag, t.create_by,"
    " t.create_time, t.update_by, t.update_time"
)

#: ``selectEmpInfoList`` / ``selectUserListByRole`` / ``selectUserListByDept`` 的投影。
_EMP_SELECT = "t.user_id AUIT_EMP_OID,t.nick_name AUIT_EMP_NAME"

#: 这三条语句用 ``resultMap="FlowCurrentNodeResult"``，但只有两列有别名。
_EMP_PROPERTIES = ("auit_emp_oid", "auit_emp_name")


class FlowCurrentNodeMapper(FlowMapper):
    """Java: ``com.ruoyi.flow.mapper.FlowCurrentNodeMapper``."""

    table = "flow_current_node"
    entity_cls = FlowCurrentNode
    select_vo = _SELECT_VO

    result_columns: Tuple[str, ...] = (
        "id",
        "flow_oid",
        "current_oid",
        "node_order",
        "node_key",
        "node_name",
        "config_type",
        "config_id",
        "config_name",
        "bill_oid",
        "auit_emp_oid",
        "auit_emp_name",
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

    order_by = "t.create_time desc,t.id"

    conditions: Tuple[If, ...] = (
        If("id", "id"),
        If("flow_oid", "FLOW_OID"),
        If("current_oid", "CURRENT_OID"),
        If("node_order", "NODE_ORDER", null_only=True),
        If("node_key", "NODE_KEY"),
        If("node_name", "NODE_NAME", like=True),
        If("config_type", "CONFIG_TYPE"),
        If("config_id", "CONFIG_ID"),
        If("config_name", "CONFIG_NAME", like=True),
        If("bill_oid", "BILL_OID"),
        If("auit_emp_oid", "AUIT_EMP_OID"),
        If("auit_emp_name", "AUIT_EMP_NAME", like=True),
        If("back_col1", "BACK_COL1"),
        If("back_col2", "BACK_COL2"),
        If("back_col3", "BACK_COL3"),
        If("sort", "sort", null_only=True),
        If("eps_id", "eps_id", null_only=True),
        If("create_by", "create_by", null_only=True),
    )

    insert_columns: Tuple[Tuple[str, str], ...] = (
        ("id", "ID"),
        ("flow_oid", "FLOW_OID"),
        ("current_oid", "CURRENT_OID"),
        ("node_order", "NODE_ORDER"),
        ("node_key", "NODE_KEY"),
        ("node_name", "NODE_NAME"),
        ("config_type", "CONFIG_TYPE"),
        ("config_id", "CONFIG_ID"),
        ("config_name", "CONFIG_NAME"),
        ("bill_oid", "BILL_OID"),
        ("auit_emp_oid", "AUIT_EMP_OID"),
        ("auit_emp_name", "AUIT_EMP_NAME"),
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
        ("flow_oid", "FLOW_OID"),
        ("current_oid", "CURRENT_OID"),
        ("node_order", "NODE_ORDER"),
        ("node_key", "NODE_KEY"),
        ("node_name", "NODE_NAME"),
        ("config_type", "CONFIG_TYPE"),
        ("config_id", "CONFIG_ID"),
        ("config_name", "CONFIG_NAME"),
        ("bill_oid", "BILL_OID"),
        ("auit_emp_oid", "AUIT_EMP_OID"),
        ("auit_emp_name", "AUIT_EMP_NAME"),
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

    # Java: int deleteByBillId(String billOid)
    def delete_by_bill_id(self, bill_oid: str) -> int:
        """**物理删除**（XML 是 ``<delete>``，与同表的逻辑删不同）。"""
        sql = "delete from  flow_current_node  where BILL_OID = :billOid"
        return execute_update(sql, {"billOid": bill_oid})

    # Java: List<FlowCurrentNode> selectEmpInfoList(FlowCurrentNode flowCurrentNode)
    def select_emp_info_list(self, query: FlowCurrentNode) -> List[FlowCurrentNode]:
        """按角色 / 租户 / 部门 / 审核类型挑人（``flag`` 取值见 XML 注释）。"""
        sql = (
            f"select {_EMP_SELECT} from sys_user t "
            f"where t.del_flag = '0' and t.status = '0'"
        )
        params: Dict[str, Any] = {}

        if query.role_id is not None and query.role_id != "":
            sql += (
                " and exists (select 1 from sys_user_role t1"
                " where t1.user_id = t.user_id and t1.role_id = :role_id)"
            )
            params["role_id"] = query.role_id

        if query.tenant_id is not None:
            sql += (
                " and exists (select 1 from sys_dept td where td.del_flag = '0'"
                " and td.dept_id = t.dept_id and td.tenant_id = :tenant_id)"
            )
            params["tenant_id"] = query.tenant_id

        if query.dept_id is not None:
            sql += " and t.dept_id = :dept_id"
            params["dept_id"] = query.dept_id

        # 科室值班人审核 —— ${backCol1} 是表名，直接拼接
        if query.flag is not None and query.flag == "dutyAudit":
            sql += (
                f" and t.dept_id in  (select tp.borrow_dept_id from {query.back_col1} tp"
                f" where  tp.id = :bill_oid)"
            )
            params["bill_oid"] = query.bill_oid

        # 部门经理
        if query.flag is not None and query.flag == "bmjlAudit":
            sql += (
                " AND EXISTS ( SELECT 1 FROM sys_dept ds WHERE ds.del_flag = '0'"
                " AND ds.dept_id = (SELECT tt.dept_id FROM sys_user tt WHERE tt.user_id = :back_col1)"
                " AND ds.leader_id = t.user_id )"
            )
            params["back_col1"] = query.back_col1

        # 分管领导
        if query.flag is not None and query.flag == "fgldAudit":
            sql += (
                " AND EXISTS ( SELECT 1 FROM sys_dept ds WHERE ds.del_flag = '0'"
                " AND ds.dept_id = (SELECT tt.dept_id FROM sys_user tt WHERE tt.user_id = :back_col1)"
                " AND ds.fgld_id = t.user_id )"
            )
            params["back_col1"] = query.back_col1

        return [
            map_result_row(self.entity_cls, _EMP_PROPERTIES, row)
            for row in execute_rows(sql, params)
        ]

    # Java: int updateFlowTable(FlowCurrentNode flowCurrentNode)
    def update_flow_table(self, query: FlowCurrentNode) -> int:
        """把流程信息回写到**业务表**（``${tableName}`` 拼接，见模块文档）。"""
        sets: List[str] = []
        params: Dict[str, Any] = {"bill_oid": query.bill_oid}
        if query.flow_key is not None:
            sets.append("flow_key = :flow_key")
            params["flow_key"] = query.flow_key
        if query.flow_ruid is not None:
            sets.append("flow_ruid = :flow_ruid")
            params["flow_ruid"] = query.flow_ruid
        if query.flow_apply_oid is not None:
            sets.append("flow_apply_oid = :flow_apply_oid")
            params["flow_apply_oid"] = query.flow_apply_oid
        if query.flow_status is not None:
            sets.append("flow_status = :flow_status")
            params["flow_status"] = query.flow_status
        # OGNL: flowStatus == 3 —— String 与 int 的数值比较，只有 "3" 命中
        if query.flow_status is not None and str(query.flow_status) == "3":
            sets.append("sh_time = now()")
        sets.append("update_time = now()")
        sql = f"update {query.table_name} set {', '.join(sets)} where id = :bill_oid"
        return execute_update(sql, params)

    # Java: List<FlowCurrentNode> selectUserListByRole(FlowCurrentNode flowCurrentNode)
    def select_user_list_by_role(self, query: FlowCurrentNode) -> List[FlowCurrentNode]:
        sql = (
            f"select {_EMP_SELECT} from sys_user t "
            f"where t.del_flag = '0' and t.status = '0'"
        )
        params: Dict[str, Any] = {}
        if query.role_key is not None and query.role_key != "":
            sql += (
                " and exists (select 1 from sys_user_role t1,sys_role t2"
                " where t1.user_id = t.user_id and t1.role_id = t2.role_id"
                " and t2.role_key = :role_key)"
            )
            params["role_key"] = query.role_key
        if query.dept_id is not None:
            sql += " and  t.dept_id = :dept_id"
            params["dept_id"] = query.dept_id
        return [
            map_result_row(self.entity_cls, _EMP_PROPERTIES, row)
            for row in execute_rows(sql, params)
        ]

    # Java: List<FlowCurrentNode> selectUserListByDept(FlowCurrentNode flowCurrentNode)
    def select_user_list_by_dept(self, query: FlowCurrentNode) -> List[FlowCurrentNode]:
        """部门设置的分管领导（``sys_dept.leader_id``）。"""
        sql = (
            f"select {_EMP_SELECT} from sys_user t "
            f"where t.del_flag = '0' and t.status = '0'"
            " AND EXISTS ( SELECT 1 FROM sys_dept ds WHERE ds.del_flag = '0'"
            " AND ds.dept_id = :dept_id AND ds.leader_id = t.user_id )"
        )
        return [
            map_result_row(self.entity_cls, _EMP_PROPERTIES, row)
            for row in execute_rows(sql, {"dept_id": query.dept_id})
        ]


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_MAPPER: Optional[FlowCurrentNodeMapper] = None


def get_mapper() -> FlowCurrentNodeMapper:
    global _DEFAULT_MAPPER
    if _DEFAULT_MAPPER is None:
        _DEFAULT_MAPPER = FlowCurrentNodeMapper()
    return _DEFAULT_MAPPER


__all__ = ["FlowCurrentNodeMapper", "get_mapper"]
