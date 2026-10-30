"""预警规则对象 car_warning_rule.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningRule.java

``extends BasePlusEntity``（``@TableId ASSIGN_UUID``）—— ``save`` 时不传 ``id``
就由 ``insert`` 生成 32 位 hex；传了 ``id`` 走更新。

``applyTime1`` / ``applyTime2`` / ``createTimeStr`` 带
``@TableField(exist = false)``：只出现在 JSON（查询条件 / 导出用），不进 SQL 投影。
其中 ``createTimeStr`` 只在导出里被赋值（``createTime`` 的 ``yyyy-MM-dd HH:mm:ss``
字符串），列表接口不会返回它。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarWarningRule(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarWarningRule``."""

    #: 规则名称
    rule_name: Optional[str] = None
    #: 预警范围id(包含的路段范围)
    notice_range_id: Optional[str] = None
    #: 预警范围(包含的路段范围)
    notice_range_anme: Optional[str] = None
    #: 通知
    notice: Optional[str] = None
    #: 通知方式
    notice_type: Optional[str] = None
    #: 通知人员id
    notice_user_id: Optional[str] = None
    #: 通知人员
    notice_user_name: Optional[str] = None
    #: 所属站/所
    org_id: Optional[str] = None
    #: 所属站/所
    org_name: Optional[str] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None
    #: 时间查询 —— ``@TableField(exist = false)``
    apply_time1: Optional[str] = None
    #: ``@TableField(exist = false)``
    apply_time2: Optional[str] = None
    #: 查询时间（导出用） —— ``@TableField(exist = false)``
    create_time_str: Optional[str] = None

    #: ``@Excel`` 注解表（``BasePlusEntity`` 上没有 ``@Excel``）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("rule_name", Excel(name="规则名称")),
        ("notice_range_id", Excel(name="预警范围id(包含的路段范围)")),
        ("notice_range_anme", Excel(name="预警范围(包含的路段范围)")),
        ("notice", Excel(name="通知")),
        ("notice_type", Excel(name="通知方式")),
        ("notice_user_id", Excel(name="通知人员id")),
        ("notice_user_name", Excel(name="通知人员")),
        ("org_id", Excel(name="所属站/所")),
        ("org_name", Excel(name="所属站/所")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["CarWarningRule"]
