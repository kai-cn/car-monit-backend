"""车辆逃费统计 VO（大屏用，``CarStatisticsVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarStatisticsVO.java

``buildPCCarStatisticsVO`` 用 ``resultType`` 自动映射：SQL 里的
``sum(ifnull(dif_amount,0)) escapedAmount`` 与 ``count(distinct car_no) number``
分别落到 ``escapedAmount`` / ``number``。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.common.core.domain.domain_model import DomainModel


class CarStatisticsVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO``."""

    #: 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
    escaped_type: Optional[str] = None
    #: 逃费类型名称
    escaped_type_name: Optional[str] = None
    #: 车辆数量
    number: int = 0
    #: 逃费金额
    escaped_amount: Decimal = Field(default=Decimal("0"))


__all__ = ["CarStatisticsVO"]
