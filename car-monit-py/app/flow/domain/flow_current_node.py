"""流程_当前节点 flow_current_node.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowCurrentNode.java

``extends BaseUuidEntity``。除实体列外，本对象还兼作**查询条件载体**：
``roleId`` / ``tableName`` / ``projectId`` / ``flowKey`` / ``roleKey`` / ``deptId``
等字段在 ``selectEmpInfoList`` / ``selectUserListByRole`` 里当入参用，
在普通列表语句里则不参与过滤（XML 里没有对应的 ``<if>``）。
照抄即可，不要因为它们"看起来没用"就删掉。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity


class FlowCurrentNode(BaseUuidEntity):
    """Java: ``com.ruoyi.flow.domain.FlowCurrentNode``."""

    #: 流程OID
    flow_oid: Optional[str] = None
    #: 当前节点OID(流程节点OID) 流程模板(flow_template) oid
    current_oid: Optional[str] = None
    #: 节点顺序（Java ``Integer``）
    node_order: Optional[int] = None
    #: 节点KEY
    node_key: Optional[str] = None
    #: 节点名称
    node_name: Optional[str] = None
    #: 当前流程类型(字典：1人员2角色3其他)
    config_type: Optional[str] = None
    #: 节点配置id
    config_id: Optional[str] = None
    #: 节点配置名称
    config_name: Optional[str] = None
    #: 单据OID
    bill_oid: Optional[str] = None
    #: 处理人ID
    auit_emp_oid: Optional[str] = None
    #: 处理人名称
    auit_emp_name: Optional[str] = None
    #: 备用字段1 项目id
    back_col1: Optional[str] = None
    #: 备用字段2 委托之前的审核人id
    back_col2: Optional[str] = None
    #: 备用字段3 委托之前的审核人名称
    back_col3: Optional[str] = None
    #: 角色id（查询入参）
    role_id: Optional[str] = None
    #: 表名称（``updateFlowTable`` 的 ``${tableName}`` 入参）
    table_name: Optional[str] = None
    #: 项目id
    project_id: Optional[str] = None
    #: 流程key
    flow_key: Optional[str] = None
    #: 流程实例ID
    flow_ruid: Optional[str] = None
    #: 流程申请ID
    flow_apply_oid: Optional[str] = None
    #: 流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)
    flow_status: Optional[str] = None
    #: 审核结论（T同意 F拒绝 R退回 S提交 委托 entrust）
    sh_value: Optional[str] = None
    #: 内容
    sh_context: Optional[str] = None
    #: 委托人id
    entrust_user_id: Optional[str] = None
    #: 委托人名称
    entrust_user_name: Optional[str] = None
    #: 角色key（``selectUserListByRole`` 的分支开关）
    role_key: Optional[str] = None
    #: 部门ID（Java ``Long``）
    dept_id: Optional[int] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("flow_oid", Excel(name="流程OID")),
        ("current_oid", Excel(name="当前节点OID(流程节点OID)")),
        ("node_order", Excel(name="节点顺序")),
        ("node_key", Excel(name="节点KEY")),
        ("node_name", Excel(name="节点名称")),
        ("config_type", Excel(name="当前流程类型(字典：1人员2角色3其他)")),
        ("config_id", Excel(name="节点配置id")),
        ("config_name", Excel(name="节点配置名称")),
        ("bill_oid", Excel(name="单据OID")),
        ("auit_emp_oid", Excel(name="处理人ID")),
        ("auit_emp_name", Excel(name="处理人名称")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("back_col3", Excel(name="备用字段3")),
        ("flow_key", Excel(name="流程key")),
        ("flow_ruid", Excel(name="流程实例ID")),
        ("flow_apply_oid", Excel(name="流程申请ID")),
        ("flow_status", Excel(name="流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)")),
    )


__all__ = ["FlowCurrentNode"]
