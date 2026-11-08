"""门架交易查询对象 gantry_trade_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryTradeInfo.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``in_time`` / ``out_time`` 是 ``java.util.Date`` + ``@JsonFormat("yyyy-MM-dd")`` —— 序列化成**日期**字符串，Python 侧同样按 ``date`` 存取。
``apply_time1`` / ``apply_time2`` / ``create_time_str`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.common.core.domain.base_plus_entity import BasePlusEntity


class GantryTradeInfo(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.GantryTradeInfo``."""

    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 轴数
    car_num: Optional[int] = None
    #: 入门架id
    in_station_id: Optional[str] = None
    #: 入门架
    in_station: Optional[str] = None
    #: 入门时间
    in_time: Optional[date] = None
    #: 出口门架id
    out_station_id: Optional[str] = None
    #: 出口门架
    out_station: Optional[str] = None
    #: 出口时间
    out_time: Optional[date] = None
    #: 交易类型（字典：1出口交易2逃费补缴）
    charge_type: Optional[str] = None
    #: 收费金额
    amount: Optional[float] = None
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
    #: 查询时间
    create_time_str: Optional[str] = None


__all__ = ["GantryTradeInfo"]
