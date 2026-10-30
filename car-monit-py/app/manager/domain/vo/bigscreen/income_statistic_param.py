"""大屏收入统计查询入参（``IncomeStatisticParam``）与结果（``incomeStatisticVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/IncomeStatisticParam.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/incomeStatisticVO.java

``queryDateType`` 是"所/站"开关（``suo`` / ``zhan``），直接参与 SQL 的
``<if test="queryDateType == 'suo'">`` 字符串比较；``orgCode`` 那个 ``<if>``
在 XML 里被注释掉了，所以字段留着但**不影响查询**。

``incomeStatisticVO`` 在 Java 里是**小写开头**的类名，Python 侧按 PEP 8 写成
``IncomeStatisticVO``，字段与 JSON 属性名一字不差。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class IncomeStatisticParam(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam``."""

    org_code: Optional[str] = None
    #: suo 查询所，zhan 查询站
    query_date_type: Optional[str] = None
    year: Optional[str] = None
    month: Optional[str] = None
    start_date: Optional[str] = None
    #: 时间查询
    apply_time1: Optional[str] = None
    apply_time2: Optional[str] = None
    org_id: Optional[str] = None
    escaped_type: Optional[str] = None


class IncomeStatisticVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.incomeStatisticVO``."""

    #: 机构名称
    org_name: Optional[str] = None
    #: 金额
    amount: Optional[Decimal] = None
    #: 车辆数量
    car_num: Optional[int] = None


__all__ = ["IncomeStatisticParam", "IncomeStatisticVO"]
