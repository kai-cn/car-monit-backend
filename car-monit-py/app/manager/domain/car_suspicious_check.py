"""可疑车辆人工核实对象 car_suspicious_check.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousCheck.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``apply_time1`` / ``apply_time2`` / ``create_time_str`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.base_plus_entity import BasePlusEntity
from app.common.core.domain.domain_model import JavaDecimal


class CarSuspiciousCheck(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarSuspiciousCheck``."""

    #: 车辆id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 是否为可疑车辆
    suspicous_flag: Optional[str] = None
    #: 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
    escaped_type: Optional[str] = None
    #: 收费金额
    charge_amount: Optional[JavaDecimal] = None
    #: 应缴金额
    total_amount: Optional[JavaDecimal] = None
    #: 差额
    dif_amount: Optional[JavaDecimal] = None
    #: 附件
    attachments: Optional[str] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None
    #: 时间查询
    apply_time1: Optional[str] = None
    apply_time2: Optional[str] = None
    #: 查询时间
    create_time_str: Optional[str] = None


__all__ = ["CarSuspiciousCheck"]
