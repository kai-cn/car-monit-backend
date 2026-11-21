"""追缴汇总 VO（大屏用，``CarAuditVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarAuditVO.java

``/manager/bigScreen/carAudit`` 的返回体，由两个统计结果拼出来：

* ``totalCount`` / ``totalAmount`` ← ``carAduitFreeService.getCarAudit``
  （逃费费用：异常流水）
* ``finishedCount`` / ``finishedAmount`` ← ``carConfimFreeService.getCarConfirm``
  （确认追缴）

Java 的四个字段都有**非 null 初值**（``0`` / ``0`` / ``BigDecimal.ZERO``），
两个来源任意一方为 ``null`` 时保留初值 —— 所以这里的默认值同样是零而不是 ``None``。
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from app.common.core.domain.domain_model import DomainModel, JavaDecimal


class CarAuditVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.CarAuditVO``."""

    #: 追缴总次数
    total_count: int = 0
    #: 追缴已完成次数
    finished_count: int = 0
    #: 追缴费用（元）
    total_amount: JavaDecimal = Field(default=Decimal("0"))
    #: 追缴已完成费用（元）
    finished_amount: JavaDecimal = Field(default=Decimal("0"))


__all__ = ["CarAuditVO"]
