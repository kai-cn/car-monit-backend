"""可疑车辆对象 car_suspicious.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspicious.java

``extends BasePlusEntityLong implements Custom``（``@TableId`` = ``ASSIGN_ID``，
但 Java 侧主键的**类型仍是 String** —— 见 ``BasePlusEntityLong#id``）。

``@TableField(exist = false)`` 的 21 个字段只出现在 JSON，不进 SQL 投影，
也不在 ``resultMap`` 里；其中 ``checkList`` / ``trailList`` 由 Service 在
``selectCarSuspiciousById`` 里回填。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, List, Optional

from pydantic import field_serializer, field_validator

from app.base.domain.trail_info import TrailInfo
from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntityLong
from app.common.utils.json_utils import format_date_time, parse_date_time
from app.manager.domain.car_suspicious_check import CarSuspiciousCheck


class CarSuspicious(BasePlusEntityLong):
    """Java: ``com.ruoyi.manager.domain.CarSuspicious``."""

    #: 车牌颜色（字典：1白色2黑色）
    plate_color: Optional[str] = None
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
    #: 通行时间
    in_time: Optional[datetime] = None
    #: 出口站id
    out_station_id: Optional[str] = None
    #: 出口站
    out_station: Optional[str] = None
    #: 出口时间
    out_time: Optional[datetime] = None
    #: 门架id
    gantry_station_id: Optional[str] = None
    #: 门架名称（原文的拼写就是 ``gantrytStation``）
    gantryt_station: Optional[str] = None
    #: 经过时间
    gantry_time: Optional[datetime] = None
    #: 图片(附件ids)
    file_ids: Optional[str] = None
    #: 终止门架id
    out_gantry_station_id: Optional[str] = None
    #: 终止门架名称
    out_gantryt_station: Optional[str] = None
    #: 终止经过时间
    out_gantry_time: Optional[datetime] = None
    #: 终止图片(附件ids)
    out_file_ids: Optional[str] = None
    #: 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
    escaped_type: Optional[str] = None
    #: 逃费类型名称
    escaped_type_name: Optional[str] = None
    #: 异常通行门架次数
    escaped_num: Optional[int] = None
    #: 是否为可疑车辆
    is_except: Optional[str] = None
    #: 可疑原因
    except_remark: Optional[str] = None
    #: 可疑材料
    except_file_ids: Optional[str] = None
    #: 核实状态（0未核实1已核实）
    check_status: Optional[str] = None
    #: 管理中心id
    org_id: Optional[str] = None
    #: 管理中心名称
    org_name: Optional[str] = None
    #: 是否在白名单（0否1是）
    is_white: Optional[str] = None
    #: 白名单原因
    white_remark: Optional[str] = None
    #: 白名单材料
    white_file_ids: Optional[str] = None
    #: 所属路线编码
    road_code: Optional[str] = None
    #: 所属路线名称
    road_name: Optional[str] = None
    #: 所属路段编码
    section_code: Optional[str] = None
    #: 所属路段名称
    section_name: Optional[str] = None
    #: 行驶轨迹id
    track_id: Optional[str] = None
    #: 行驶轨迹josn
    track_josn: Optional[str] = None
    #: 轨迹点集合
    track_names: Optional[str] = None
    #: 逃费场景
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None

    # ------------------------------------------------------ @TableField(exist=false)
    #: 车牌号查询
    car_no_query: Optional[str] = None
    #: 时间查询
    apply_time1: Optional[str] = None
    #: ``@TableField(exist = false)``
    apply_time2: Optional[str] = None
    #: 查询时间
    create_time_str: Optional[str] = None
    #: 车辆核实信息
    check_list: Optional[List[CarSuspiciousCheck]] = None
    #: 车俩轨迹
    trail_list: Optional[List[TrailInfo]] = None
    #: 门架编号
    gantry_code: Optional[str] = None
    #: 所属收费站编码
    toll_code: Optional[str] = None
    #: 服务区编码
    fwqbm: Optional[str] = None
    #: 1收费站、2门架、3服务区
    type: Optional[str] = None
    #: 编码
    code: Optional[str] = None
    #: 收费金额
    charge_amount: Optional[str] = None
    #: 应缴金额
    total_amount: Optional[str] = None
    #: 差额
    dif_amount: Optional[str] = None
    #: 经过门架时间
    mj_time: Optional[str] = None
    #: 经过门架地址
    mj_address: Optional[str] = None
    #: 通行时间
    tx_time: Optional[str] = None
    #: 通行时间地址
    tx_address: Optional[str] = None

    @field_serializer("in_time", "out_time", "gantry_time", "out_gantry_time")
    def _serialize_travel_time(
        self, value: Optional[datetime], _info: Any
    ) -> Optional[str]:
        """Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")`` —— 空格分隔，不是 ISO 的 ``T``。"""
        return format_date_time(value)

    @field_validator("in_time", "out_time", "gantry_time", "out_gantry_time", mode="before")
    @classmethod
    def _parse_travel_time(cls, value: Any) -> Optional[datetime]:
        """接受 ``@JsonFormat`` 字符串、ISO-8601 与日期对象。"""
        if value is None or value == "":
            return None
        return parse_date_time(value)

    #: ``@Excel`` 注解表（顺序照抄 Java 字段声明）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("plate_color", Excel(name="车牌颜色", read_converter_exp="字=典：1白色2黑色")),
        ("car_no", Excel(name="车牌号")),
        ("car_type", Excel(name="车型")),
        ("car_vehicle", Excel(name="车种")),
        ("car_num", Excel(name="轴数")),
        ("pass_type", Excel(name="通行标识", read_converter_exp="1=人工2ETC")),
        ("in_station_id", Excel(name="入口站id")),
        ("in_station", Excel(name="入口站")),
        ("in_time", Excel(name="通行时间", width=30, date_format="yyyy-MM-dd")),
        ("out_station_id", Excel(name="出口站id")),
        ("out_station", Excel(name="出口站")),
        ("out_time", Excel(name="出口时间", width=30, date_format="yyyy-MM-dd")),
        ("gantry_station_id", Excel(name="门架id")),
        ("gantryt_station", Excel(name="门架名称")),
        ("gantry_time", Excel(name="经过时间", width=30, date_format="yyyy-MM-dd")),
        ("file_ids", Excel(name="图片(附件ids)")),
        ("out_gantry_station_id", Excel(name="终止门架id")),
        ("out_gantryt_station", Excel(name="终止门架名称")),
        (
            "out_gantry_time",
            Excel(name="终止经过时间", width=30, date_format="yyyy-MM-dd"),
        ),
        ("out_file_ids", Excel(name="终止图片(附件ids)")),
        (
            "escaped_type",
            Excel(name="逃费类型", read_converter_exp="字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂"),
        ),
        ("escaped_type_name", Excel(name="逃费类型名称")),
        ("escaped_num", Excel(name="异常通行门架次数")),
        ("is_except", Excel(name="是否为可疑车辆")),
        ("except_remark", Excel(name="可疑原因")),
        ("except_file_ids", Excel(name="可疑材料")),
        ("check_status", Excel(name="核实状态", read_converter_exp="0=未核实1已核实")),
        ("org_id", Excel(name="管理中心id")),
        ("org_name", Excel(name="管理中心名称")),
        ("is_white", Excel(name="是否在白名单", read_converter_exp="0=否1是")),
        ("white_remark", Excel(name="白名单原因")),
        ("white_file_ids", Excel(name="白名单材料")),
        ("road_code", Excel(name="所属路线编码")),
        ("road_name", Excel(name="所属路线名称")),
        ("section_code", Excel(name="所属路段编码")),
        ("section_name", Excel(name="所属路段名称")),
        ("track_id", Excel(name="行驶轨迹id")),
        ("track_josn", Excel(name="行驶轨迹josn")),
        ("track_names", Excel(name="轨迹点集合")),
        ("back_col1", Excel(name="逃费场景")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["CarSuspicious"]
