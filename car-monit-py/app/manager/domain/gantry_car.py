"""门架拍识查询对象 gantry_car.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryCar.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``in_time`` / ``gantry_time`` 是 ``java.util.Date`` + ``@JsonFormat("yyyy-MM-dd")`` —— 序列化成**日期**字符串，Python 侧同样按 ``date`` 存取。
``apply_time1`` / ``apply_time2`` / ``create_time_str`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar, Optional

from app.common.core.domain.base_plus_entity import BasePlusEntity


class GantryCar(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.GantryCar``."""

    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 轴数
    car_num: Optional[int] = None
    #: 入口站id
    in_station_id: Optional[str] = None
    #: 入口站
    in_station: Optional[str] = None
    #: 通行时间
    in_time: Optional[date] = None
    #: 门架id
    gantry_station_id: Optional[str] = None
    #: 门架名称
    gantryt_station: Optional[str] = None
    #: 经过时间
    gantry_time: Optional[date] = None
    #: 图片(附件ids)
    file_ids: Optional[str] = None
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


__all__ = ["GantryCar"]
