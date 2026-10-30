"""车辆简表 VO（``CarVO``）—— Redis 缓存 ``car_list_jc`` 的元素.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/domain/CarVO.java

只在 :meth:`app.manager.service.car_info_service.CarInfoService.update_redis_car_list`
里被填充两个字段（``carId`` / ``carNo``），其余保持 ``null``。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class CarVO(DomainModel):
    """Java: ``com.ruoyi.base.domain.CarVO``."""

    #: 车牌 id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 行驶轨迹 id
    track_id: Optional[str] = None
    #: 行驶轨迹 json
    track_josn: Optional[str] = None
    #: 是否有数据
    flag: Optional[str] = None


__all__ = ["CarVO"]
