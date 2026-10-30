"""车辆地图描点 VO（``CarLocationVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarLocationVO.java

``lon`` / ``lat`` 是 ``BigDecimal``（Java 侧由 ``lonStr`` / ``latStr`` 转换而来）；
``lonStr`` / ``latStr`` 是数据库里的字符串原值。两者**同时**出现在响应体里。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class CarLocationVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.CarLocationVO``."""

    #: 主键 id
    id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 最后通行经度
    lon: Optional[float] = None
    #: 最后通行维度（原文）
    lat: Optional[float] = None
    #: 最后通行经度（字符串）
    lon_str: Optional[str] = None
    #: 最后通行维度（字符串）
    lat_str: Optional[str] = None
    #: 车辆状态
    status: Optional[str] = None
    #: 服务器类型
    last_pass_type: Optional[str] = None


__all__ = ["CarLocationVO"]
