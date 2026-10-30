"""我的申请 flow_apply_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowApplyInfo.java

``extends BaseUuidEntity``，23 列全部由 ``FlowApplyInfoMapper.xml`` 的 ``resultMap`` 映射。

``auitEmpName`` 的特殊之处
--------------------------
它**不在** ``resultMap`` 里，却有 setter，列表语句通过
``select <sql>,t.BACK_COL1 auitEmpName`` 这个别名把它带出来。MyBatis 的
``autoMappingBehavior`` 默认是 ``PARTIAL``，未映射的列仍会按列名自动匹配属性，
所以在 Java 里 ``auitEmpName`` **是有值的**。Python 侧靠
:func:`app.base.mapper.ods_sql.map_result_row` 的「别名 -> 驼峰」匹配来还原同一行为，
不能用只认 ``resultMap`` 的 ``map_row``。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_uuid_entity import BaseUuidEntity


class FlowApplyInfo(BaseUuidEntity):
    """Java: ``com.ruoyi.flow.domain.FlowApplyInfo``."""

    #: 单据OID
    bill_oid: Optional[str] = None
    #: 业务类型-字典
    buss_type: Optional[str] = None
    #: 流程实例ID
    flow_ruid: Optional[str] = None
    #: 标题
    msg_title: Optional[str] = None
    #: 内容
    msg_context: Optional[str] = None
    #: 消息类型(1:通知业务，2:办理业务)
    msg_type: Optional[str] = None
    #: 处理的URL
    msg_url: Optional[str] = None
    #: 申请人
    apply_name: Optional[str] = None
    #: 当前节点OID(流程节点OID)
    current_oid: Optional[str] = None
    #: 批次OID
    pc_oid: Optional[str] = None
    #: 备用字段1 当前审批人名称
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 备用字段3
    back_col3: Optional[str] = None
    #: 流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)
    flow_status: Optional[str] = None
    #: 当前审批人名称 —— 列表语句别名 ``t.BACK_COL1 auitEmpName``（不在 resultMap 里）
    auit_emp_name: Optional[str] = None
    #: 流程委托数据，里面保存的是 JSON 数组（见 :class:`EntrustInfo`）
    entrust_info: Optional[str] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("bill_oid", Excel(name="单据OID")),
        ("buss_type", Excel(name="业务类型-字典")),
        ("flow_ruid", Excel(name="流程实例ID")),
        ("msg_title", Excel(name="标题")),
        ("msg_context", Excel(name="内容")),
        ("msg_type", Excel(name="消息类型(1:通知业务，2:办理业务)")),
        ("msg_url", Excel(name="处理的URL")),
        ("apply_name", Excel(name="申请人")),
        ("current_oid", Excel(name="当前节点OID(流程节点OID)")),
        ("pc_oid", Excel(name="批次OID")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("back_col3", Excel(name="备用字段3")),
        ("flow_status", Excel(name="流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)")),
    )


__all__ = ["FlowApplyInfo"]
