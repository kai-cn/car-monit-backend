"""补缴处理对象 car_aduit_free.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarAduitFree.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``apply_time1`` / ``apply_time2`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarAduitFree(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarAduitFree``."""

    #: 确认补缴id
    confirm_id: Optional[str] = None
    #: 车辆id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 处理单位id
    org_id: Optional[str] = None
    #: 处理单位
    org_name: Optional[str] = None
    #: 录入人员ids
    user_ids: Optional[str] = None
    #: 处理人员
    user_names: Optional[str] = None
    #: 拆分金额（Java ``BigDecimal``）
    amount: Optional[Decimal] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None
    #: 时间查询
    apply_time1: Optional[str] = None
    apply_time2: Optional[str] = None

    #: ``@Excel`` 注解表（导出走 ``ExcelUtil``，表头顺序即此顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("confirm_id", Excel(name="确认补缴id")),
        ("car_id", Excel(name="车辆id")),
        ("car_no", Excel(name="车牌号")),
        ("car_type", Excel(name="车型")),
        ("car_vehicle", Excel(name="车种")),
        ("org_id", Excel(name="处理单位id")),
        ("org_name", Excel(name="处理单位")),
        ("user_ids", Excel(name="处理人员ids")),
        ("user_names", Excel(name="处理人员")),
        ("amount", Excel(name="拆分金额")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["CarAduitFree"]
