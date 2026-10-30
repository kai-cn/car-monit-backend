"""业务测试对象 buss_test.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/BussTest.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``apply_time`` / ``apply_time2`` / ``sh_time`` 是 ``java.util.Date`` + ``@JsonFormat("yyyy-MM-dd")`` —— 序列化成**日期**字符串，Python 侧同样按 ``date`` 存取。
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity


class BussTest(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.BussTest``."""

    #: 业务名称
    bill_name: Optional[str] = None
    #: 业务名称(字典：1业务2其他)
    bill_type: Optional[str] = None
    #: 金额
    amount: Optional[float] = None
    #: 部门id
    dept_id: Optional[int] = None
    #: 人员id
    user_id: Optional[int] = None
    #: 申请时间
    apply_time: Optional[date] = None
    #: 时间时分秒
    apply_time2: Optional[date] = None
    #: 附件(逗号多个分割)
    file_ids: Optional[str] = None
    #: 流程key
    flow_key: Optional[str] = None
    #: 流程实例ID
    flow_ruid: Optional[str] = None
    #: 流程申请ID
    flow_apply_oid: Optional[str] = None
    #: 流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)
    flow_status: Optional[str] = None
    #: 审核时间
    sh_time: Optional[date] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None

    #: ``@Excel`` 注解表（导出走 ``ExcelUtil``，表头顺序即此顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("bill_name", Excel(name="业务名称")),
        ("bill_type", Excel(name="业务名称(字典：1业务2其他)")),
        ("amount", Excel(name="金额")),
        ("dept_id", Excel(name="部门id")),
        ("user_id", Excel(name="人员id")),
        ("apply_time", Excel(name="申请时间", width=30, date_format="yyyy-MM-dd")),
        ("apply_time2", Excel(name="时间时分秒", width=30, date_format="yyyy-MM-dd")),
        ("file_ids", Excel(name="附件(逗号多个分割)")),
        ("flow_key", Excel(name="流程key")),
        ("flow_ruid", Excel(name="流程实例ID")),
        ("flow_apply_oid", Excel(name="流程申请ID")),
        ("flow_status", Excel(name="流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)")),
        ("sh_time", Excel(name="审核时间", width=30, date_format="yyyy-MM-dd")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["BussTest"]
