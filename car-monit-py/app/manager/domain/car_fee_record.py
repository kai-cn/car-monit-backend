"""收费流水对象 car_fee_record.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarFeeRecord.java

``extends BasePlusEntity``。``inTime`` / ``outTime`` 是 ``java.util.Date`` +
``@JsonFormat("yyyy-MM-dd")`` —— 序列化成**日期**（不是时间戳），Python 侧同样
按 ``date`` 存取。
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarFeeRecord(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarFeeRecord``."""

    #: 车辆id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 入口站id
    in_station_id: Optional[str] = None
    #: 入口站
    in_station: Optional[str] = None
    #: 入口时间
    in_time: Optional[date] = None
    #: 出口站id
    out_station_id: Optional[str] = None
    #: 出口站
    out_station: Optional[str] = None
    #: 出口时间
    out_time: Optional[date] = None
    #: 交易类型（字典：1出口交易2逃费补缴）
    charge_type: Optional[str] = None
    #: 收费金额
    amount: Optional[float] = None
    #: 异常流水id
    except_id: Optional[str] = None
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

    #: ``@Excel`` 注解表（导出走 ``ExcelUtil``，表头顺序即此顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("car_id", Excel(name="车辆id")),
        ("car_no", Excel(name="车牌号")),
        ("car_type", Excel(name="车型")),
        ("car_vehicle", Excel(name="车种")),
        ("in_station_id", Excel(name="入口站id")),
        ("in_station", Excel(name="入口站")),
        ("in_time", Excel(name="入口时间", width=30, date_format="yyyy-MM-dd")),
        ("out_station_id", Excel(name="出口站id")),
        ("out_station", Excel(name="出口站")),
        ("out_time", Excel(name="出口时间", width=30, date_format="yyyy-MM-dd")),
        ("charge_type", Excel(name="交易类型", read_converter_exp="字=典：1出口交易2逃费补缴")),
        ("amount", Excel(name="收费金额")),
        ("except_id", Excel(name="异常流水id")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["CarFeeRecord"]
