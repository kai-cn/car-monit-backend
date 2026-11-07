"""PC 端可疑车辆统计 VO（``PCCarStatisticsVO`` + ``PCCarStatisticsDetailVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCCarStatisticsVO.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCCarStatisticsDetailVO.java

``PCCarStatisticsVO`` 的 12 个统计字段都有**非 null 初值**（``0`` / ``BigDecimal.ZERO``），
所以 ``buildPCCarStatisticsVO`` 即使一条 SQL 结果都没有，响应体里也是满屏的 ``0``
—— 不要把它们改成 ``Optional``。

``PCCarStatisticsDetailVO`` 的 ``orgName`` 在 SQL 里**没有被查询**（注释掉的
``left join car_confim_free``），恒为 ``null``；``escapedAmount`` 是
``e.dif_amount`` 的别名。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import Field, field_serializer

from app.common.core.domain.domain_model import DomainModel, JavaDecimal
from app.common.utils.json_utils import format_date_time


class PCCarStatisticsDetailVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.PCCarStatisticsDetailVO``."""

    plate_color: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
    escaped_type: Optional[str] = None
    #: 逃费金额 —— SQL 别名 ``escapedAmount``
    escaped_amount: JavaDecimal = Field(default=Decimal("0"))
    #: 录入单位 —— 列表 SQL 没有查这一列，恒为 ``None``
    org_name: Optional[str] = None
    #: 创建时间
    create_time: Optional[datetime] = None

    @field_serializer("create_time")
    def _serialize_create_time(
        self, value: Optional[datetime], _info: object
    ) -> Optional[str]:
        """Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``."""
        return format_date_time(value)


class PCCarStatisticsVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.PCCarStatisticsVO``."""

    #: 录入单位
    org_id: Optional[str] = None
    #: 录入单位
    org_name: Optional[str] = None

    escaped_type10_num: int = 0
    escaped_type10_amount: JavaDecimal = Field(default=Decimal("0"))
    escaped_type20_num: int = 0
    escaped_type20_amount: JavaDecimal = Field(default=Decimal("0"))
    escaped_type30_num: int = 0
    escaped_type30_amount: JavaDecimal = Field(default=Decimal("0"))
    escaped_type40_num: int = 0
    escaped_type40_amount: JavaDecimal = Field(default=Decimal("0"))
    escaped_type50_num: int = 0
    escaped_type50_amount: JavaDecimal = Field(default=Decimal("0"))
    escaped_type60_num: int = 0
    escaped_type60_amount: JavaDecimal = Field(default=Decimal("0"))

    total_num: int = 0
    total_amount: JavaDecimal = Field(default=Decimal("0"))

    #: 明细列表。Java 字段名 ``detailVOList``，getter 是 ``getDetailVOList()``，Jackson 的
    #: Bean 命名规则把 ``DetailVOList`` 首字母降格后得到 ``detailVOList``（``VO`` 保持大写）。
    #: ``to_camel`` 生成的是 ``detailVoList``，所以必须显式指定 —— 否则前端拿不到明细。
    detail_vo_list: Optional[List[PCCarStatisticsDetailVO]] = Field(
        default=None, alias="detailVOList"
    )


__all__ = ["PCCarStatisticsDetailVO", "PCCarStatisticsVO"]
