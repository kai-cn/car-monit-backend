"""车辆简表 VO（大屏用，``CarInfoVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarInfoVO.java

``selectCarVoList`` 的 SQL 还多选了 ``t.id`` 与 ``t.escaped_type_name``，
但 ``CarInfoVO`` 没有这两个属性（``resultType`` 按列名映射，匹配不到就丢弃），
所以响应体里只有下面 4 个字段。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class CarInfoVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.CarInfoVO``."""

    #: 车牌号（同时作为 ``isExitsCar`` 的查询条件）
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
    escaped_type: Optional[str] = None
    #: 逃费金额（元）
    escaped_amount: Optional[float] = None


__all__ = ["CarInfoVO"]
