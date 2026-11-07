"""异常车辆流水对象 car_except_record.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarExceptRecord.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。

``supplementaryStatus`` 在 Java 里带着**非 null 初值** ``"0"`` —— 所以新建
实体的 JSON 里一定有 ``"supplementaryStatus": "0"``，照抄。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import field_serializer, field_validator

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity
from app.common.core.domain.domain_model import JavaDecimal
from app.common.utils.json_utils import format_date_time, parse_date_time


class CarExceptRecord(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarExceptRecord``."""

    #: 车辆id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 轴数
    car_num: Optional[int] = None
    #: 通行标识（1人工2ETC）
    pass_type: Optional[str] = None
    #: 入口站id
    in_station_id: Optional[str] = None
    #: 入口站
    in_station: Optional[str] = None
    #: 入口时间
    in_time: Optional[datetime] = None
    #: 出口站id
    out_station_id: Optional[str] = None
    #: 出口站
    out_station: Optional[str] = None
    #: 出口时间
    out_time: Optional[datetime] = None
    #: 应缴金额
    total_amount: Optional[JavaDecimal] = None
    #: 收费金额
    charge_amount: Optional[JavaDecimal] = None
    #: 差额
    dif_amount: Optional[JavaDecimal] = None
    #: 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
    escaped_type: Optional[str] = None
    #: 备注
    remark: Optional[str] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0未补交1全部补交）
    status: Optional[str] = None

    # ------------------------------------------------------ @TableField(exist=false)
    #: 时间查询：入口时间
    apply_time1: Optional[str] = None
    #: ``@TableField(exist = false)``
    apply_time2: Optional[str] = None
    #: 时间查询：出口时间
    apply_time3: Optional[str] = None
    #: ``@TableField(exist = false)``
    apply_time4: Optional[str] = None
    #: 查询时间
    create_time_str: Optional[str] = None
    #: 录入单位
    org_id: Optional[str] = None
    #: 补缴状态 0未补缴 —— Java 有非 null 初值
    supplementary_status: Optional[str] = "0"
    #: 异常流水ids
    except_ids: Optional[str] = None
    #: 车俩查询
    car_no_query: Optional[str] = None
    #: 录入单位以及用户
    create_info: Optional[str] = None
    #: 异常流水次数
    except_num: Optional[int] = None
    #: 异常流水金额
    except_amount: Optional[JavaDecimal] = None
    #: 查询时间
    in_time_str: Optional[str] = None
    #: 查询时间
    out_time_str: Optional[str] = None

    @field_serializer("in_time", "out_time")
    def _serialize_travel_time(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        """Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")`` —— 空格分隔，不是 ISO 的 ``T``。"""
        return format_date_time(value)

    @field_validator("in_time", "out_time", mode="before")
    @classmethod
    def _parse_travel_time(cls, value: Any) -> Optional[datetime]:
        """接受 ``@JsonFormat`` 字符串、ISO-8601 与日期对象。"""
        if value is None or value == "":
            return None
        return parse_date_time(value)

    #: ``@Excel`` 注解表（顺序照抄 Java 字段声明）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("car_id", Excel(name="车辆id")),
        ("car_no", Excel(name="车牌号")),
        ("car_type", Excel(name="车型")),
        ("car_vehicle", Excel(name="车种")),
        ("car_num", Excel(name="轴数")),
        ("pass_type", Excel(name="通行标识", read_converter_exp="1=人工2ETC")),
        ("in_station_id", Excel(name="入口站id")),
        ("in_station", Excel(name="入口站")),
        ("in_time", Excel(name="入口时间", width=30, date_format="yyyy-MM-dd")),
        ("out_station_id", Excel(name="出口站id")),
        ("out_station", Excel(name="出口站")),
        ("out_time", Excel(name="出口时间", width=30, date_format="yyyy-MM-dd")),
        ("total_amount", Excel(name="应缴金额")),
        ("charge_amount", Excel(name="收费金额")),
        ("dif_amount", Excel(name="差额")),
        (
            "escaped_type",
            Excel(name="逃费类型", read_converter_exp="字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂"),
        ),
        ("remark", Excel(name="备注")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=未补交1全部补交")),
        ("except_ids", Excel(name="异常流水ids")),
        ("car_no_query", Excel(name="车俩查询")),
    )


__all__ = ["CarExceptRecord"]
