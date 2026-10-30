"""确认补缴对象 car_confim_free.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarConfimFree.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``car_aduit_free_list`` / ``car_except_record_list`` / ``total_amount`` / ``charge_amount`` / ``dif_amount`` / ``apply_time1`` / ``apply_time2`` / ``apply_time3`` / ``apply_time4`` / ``car_no_query`` / ``confim_free_num`` / ``confim_free_amount`` / ``escaped_type`` / ``comfim_free_type`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, List, Optional

from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarConfimFree(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarConfimFree``."""

    #: 车辆id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 司机名称
    link_name: Optional[str] = None
    #: 联系方式
    link_phone: Optional[str] = None
    #: 录入单位id
    org_id: Optional[str] = None
    #: 录入单位
    org_name: Optional[str] = None
    #: 录入人员ids
    user_ids: Optional[str] = None
    #: 录入人员
    user_names: Optional[str] = None
    #: 拆分金额（Java ``BigDecimal``）
    amount: Optional[Decimal] = None
    #: 处理金额（Java ``BigDecimal``）
    aduit_amount: Optional[Decimal] = None
    #: 异常流水ids
    except_ids: Optional[str] = None
    #: 逃费类型s
    escaped_types: Optional[str] = None
    #: 比例
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None
    car_aduit_free_list: Optional[List[Any]] = None
    car_except_record_list: Optional[List[Any]] = None
    #: 应缴金额（Java ``BigDecimal``）
    total_amount: Optional[Decimal] = None
    #: 收费金额（Java ``BigDecimal``）
    charge_amount: Optional[Decimal] = None
    #: 差额（Java ``BigDecimal``）
    dif_amount: Optional[Decimal] = None
    #: 时间查询 :入口时间
    apply_time1: Optional[str] = None
    apply_time2: Optional[str] = None
    #: 时间查询 :入口时间
    apply_time3: Optional[str] = None
    apply_time4: Optional[str] = None
    #: 车牌号查询
    car_no_query: Optional[str] = None
    #: 异常流水次数
    confim_free_num: Optional[int] = None
    #: 异常流水金额（Java ``BigDecimal``）
    confim_free_amount: Optional[Decimal] = None
    escaped_type: Optional[str] = None
    comfim_free_type: Optional[str] = None
    #: 车辆数量 —— Java 初值 ``0``（``getPCCarStatistics`` 的 ``count(distinct car_no) number``）
    number: int = 0
    #: 逃费金额 —— Java 初值 ``BigDecimal.ZERO``（``sum(ifnull(dif_amount,0)) escapedAmount``）
    escaped_amount: Decimal = Decimal("0")


__all__ = ["CarConfimFree"]
