"""预警车辆对象 car_warning_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningInfo.java

``extends BasePlusEntityNew``（``@TableId`` = ``ASSIGN_UUID``）。
``gantry_time_str`` / ``apply_time1`` / ``apply_time2`` / ``escaped_type`` / ``escaped_amount`` / ``car_no_query`` / ``create_time_str`` / ``in_time_str`` / ``flag`` / ``flag_time`` / ``query_rante`` / ``gantry_code`` / ``toll_code`` / ``fwqbm`` / ``type`` / ``code`` / ``plate_color`` / ``trail_fwq_list`` / ``section_code_list`` / ``code_list`` / ``need_to_warn_str`` / ``next_pass_time_str`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from app.common.core.domain.base_plus_entity import BasePlusEntityNew


class CarWarningInfo(BasePlusEntityNew):
    """Java: ``com.ruoyi.manager.domain.CarWarningInfo``."""

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
    #: 入口站id
    in_station_id: Optional[str] = None
    #: 入口站
    in_station: Optional[str] = None
    #: 入口时间
    in_time: Optional[datetime] = None
    #: 门架id
    gantry_station_id: Optional[str] = None
    #: 门架名称
    gantryt_station: Optional[str] = None
    #: 经过时间
    gantry_time: Optional[datetime] = None
    #: 图片(附件ids)
    file_ids: Optional[str] = None
    #: 预计下一个通行时间
    next_pass_time: Optional[datetime] = None
    #: 预计下一个通行类型
    next_pass_type: Optional[str] = None
    #: 预计下一个通行地址
    next_pass_address: Optional[str] = None
    #: 预计下一个通行经度
    next_pass_longitude: Optional[str] = None
    #: 预计下一个通行维度
    next_pass_latitude: Optional[str] = None
    #: 所属路线编码
    road_code: Optional[str] = None
    #: 所属路线名称
    road_name: Optional[str] = None
    #: 所属路段编码
    section_code: Optional[str] = None
    #: 所属路段名称
    section_name: Optional[str] = None
    #: 行驶轨迹id
    track_id: Optional[str] = None
    #: 行驶轨迹josn
    track_josn: Optional[str] = None
    #: 轨迹点集合
    track_names: Optional[str] = None
    #: 同步日期
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    gantry_time_str: Optional[str] = None
    #: 时间查询
    apply_time1: Optional[str] = None
    apply_time2: Optional[str] = None
    escaped_type: Optional[str] = None
    escaped_amount: Optional[float] = None
    #: 车牌号查询
    car_no_query: Optional[str] = None
    #: 查询时间
    create_time_str: Optional[str] = None
    #: 入口时间
    in_time_str: Optional[str] = None
    #: 标识
    flag: Optional[str] = None
    #: 标识查询时间
    flag_time: Optional[str] = None
    #: 查询范围
    query_rante: Optional[str] = None
    gantry_code: Optional[str] = None
    toll_code: Optional[str] = None
    fwqbm: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    plate_color: Optional[str] = None
    trail_fwq_list: Optional[List[Any]] = None
    section_code_list: Optional[List[str]] = None
    code_list: Optional[List[str]] = None
    #: 需要告警标志 0 否1 是
    need_to_warn_str: Optional[str] = None
    #: 下一个时间
    next_pass_time_str: Optional[str] = None


__all__ = ["CarWarningInfo"]
