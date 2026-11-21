"""PC 端堵漏增收统计 VO（``PCIncomeStaticsVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCIncomeStaticsVO.java

``resultType`` 自动映射，SQL 别名与属性名一一对应：``amount`` / ``carNum`` /
``orgId`` / ``orgName``。四个字段在 Java 里都是可空引用（没有初值），所以这里
一律 ``Optional`` —— 一个部门都没统计到时返回的是 ``null`` 而不是 ``0``。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel, JavaDecimal


class PCIncomeStaticsVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.PCIncomeStaticsVO``."""

    org_id: Optional[str] = None
    #: 机构名称
    org_name: Optional[str] = None
    #: 金额
    amount: Optional[JavaDecimal] = None
    #: 车辆数量
    car_num: Optional[int] = None


__all__ = ["PCIncomeStaticsVO"]
