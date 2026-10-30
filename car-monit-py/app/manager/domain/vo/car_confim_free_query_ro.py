"""确认补缴 / 补缴处理统计的查询入参（``CarConfimFreeQueryRo``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/CarConfimFreeQueryRo.java

这是 ``/manager/confimfree/carStatics`` / ``exportCarStatics`` 与
``/manager/aduitfree/incomeStatics`` 系列接口的**查询参数对象**（不是 ``BaseEntity``
的子类，也没有 ``params`` 之类的扩展字段）。Controller 里没有 ``@RequestBody``，
所以走 Spring 的"无注解 bean 参数"绑定 —— Python 侧对应
:func:`~app.common.core.controller.base_controller.bind_query_params`。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class CarConfimFreeQueryRo(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.CarConfimFreeQueryRo``."""

    org_id: Optional[str] = None
    #: 录入单位id —— Java 的注释与字段名对不上，但字段就叫 ``carNo``（车牌号）
    car_no: Optional[str] = None
    org_name: Optional[str] = None
    #: 逃费类型
    escaped_type: Optional[str] = None
    #: 时间查询 :入口时间
    apply_time1: Optional[str] = None
    apply_time2: Optional[str] = None


__all__ = ["CarConfimFreeQueryRo"]
