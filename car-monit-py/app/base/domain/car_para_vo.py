"""车辆轨迹查询入参 VO（``CarParaVO``）—— 转发给外部轨迹服务的请求体.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/CarParaVO.java

只在 ``HttpSysUtilApiService.carTrackQueryByCarNo`` 里用到。Java 里是普通 POJO，
字段全是可空的包装类型；``pageNum`` / ``pageSize`` 在 controller 里被硬编码为
``1`` / ``20``。
"""

from __future__ import annotations

from typing import List, Optional

from app.base.domain.car_vo import CarVO
from app.common.core.domain.domain_model import DomainModel


class CarParaVO(DomainModel):
    """Java: ``com.ruoyi.base.domain.CarParaVO``."""

    #: 车辆列表
    carlist: Optional[List[CarVO]] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 时间查询（起）
    apply_time1: Optional[str] = None
    #: 时间查询（止）
    apply_time2: Optional[str] = None
    #: 车辆编号数组
    car_no_list: Optional[List[str]] = None
    #: 当前页面
    page_num: Optional[int] = None
    #: 分页大小
    page_size: Optional[int] = None
    #: 起始界面
    start_num: Optional[int] = None
    #: 最后的界面
    end_num: Optional[int] = None
    #: 起始天数
    star_time: Optional[int] = None
    #: 最后的天数
    end_time: Optional[int] = None
    #: 标识位
    flag: Optional[str] = None


__all__ = ["CarParaVO"]
