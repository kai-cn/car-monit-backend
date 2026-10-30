"""常用路线对象 car_route_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteInfo.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``apply_time1`` / ``apply_time2`` / ``create_time_str`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarRouteInfo(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarRouteInfo``."""

    #: 车辆id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 轴数
    car_num: Optional[int] = None
    #: 起点通行地址
    start_address: Optional[str] = None
    #: 最后通行经度
    start_longitude: Optional[str] = None
    #: 起点通行维度
    start_latitude: Optional[str] = None
    #: 终点通行地址
    end_address: Optional[str] = None
    #: 终点通行经度
    end_longitude: Optional[str] = None
    #: 终点通行维度
    end_latitude: Optional[str] = None
    #: 路线明细JOSN
    route_detail: Optional[str] = None
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


__all__ = ["CarRouteInfo"]
