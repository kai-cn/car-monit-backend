"""车辆行驶轨迹对象 car_track_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarTrackInfo.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``snap_time`` / ``receive_time`` 是 ``java.util.Date`` + ``@JsonFormat("yyyy-MM-dd")``
—— 序列化成**日期**字符串，Python 侧同样按 ``date`` 存取。

``apply_time1`` / ``apply_time2`` / ``longitude_dec`` / ``latitude_dec`` /
``page_num`` / ``page_size`` 都带 ``@TableField(exist = false)``：只出现在 JSON，
不进 SQL 投影，也不在 ``resultMap`` 里（因此响应体中只有 Service 显式回填的
``longitudeDec`` / ``latitudeDec`` 有值）。
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarTrackInfo(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarTrackInfo``."""

    #: 车辆id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 经度
    longitude: Optional[str] = None
    #: 维度（原文就是"维度"）
    latitude: Optional[str] = None
    #: 设备类型
    device_type: Optional[str] = None
    #: 设备编号
    device_no: Optional[str] = None
    #: 车道编号
    lane_no: Optional[str] = None
    #: 抓拍时间
    snap_time: Optional[date] = None
    #: 接收时间
    receive_time: Optional[date] = None
    #: 抓拍图片
    snap_pic: Optional[str] = None
    #: 管理中心路段id
    road_section_id: Optional[str] = None
    #: 管理中心路段名称
    road_section_name: Optional[str] = None
    #: 行驶轨迹id
    track_id: Optional[str] = None
    #: 行驶轨迹josn
    track_josn: Optional[str] = None
    #: 备用字段1
    back_col1: Optional[str] = None
    #: 备用字段2
    back_col2: Optional[str] = None
    #: 状态（0正常1停用）
    status: Optional[str] = None
    #: 备注
    remark: Optional[str] = None
    #: 时间查询 —— ``@TableField(exist = false)``
    apply_time1: Optional[str] = None
    #: ``@TableField(exist = false)``
    apply_time2: Optional[str] = None
    #: 经度 —— ``@TableField(exist = false)``（``BigDecimal`` -> ``float``）
    longitude_dec: Optional[float] = None
    #: 维度 —— ``@TableField(exist = false)``（``BigDecimal`` -> ``float``）
    latitude_dec: Optional[float] = None
    #: 当前页面 —— ``@TableField(exist = false)``
    page_num: Optional[int] = None
    #: 分页大小 —— ``@TableField(exist = false)``
    page_size: Optional[int] = None

    #: ``@Excel`` 注解表（``BasePlusEntity`` 上没有 ``@Excel``）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("car_id", Excel(name="车辆id")),
        ("car_no", Excel(name="车牌号")),
        ("longitude", Excel(name="经度")),
        ("latitude", Excel(name="维度")),
        ("device_type", Excel(name="设备类型")),
        ("device_no", Excel(name="设备编号")),
        ("lane_no", Excel(name="车道编号")),
        ("snap_time", Excel(name="抓拍时间", width=30, date_format="yyyy-MM-dd")),
        ("receive_time", Excel(name="接收时间", width=30, date_format="yyyy-MM-dd")),
        ("snap_pic", Excel(name="抓拍图片")),
        ("road_section_id", Excel(name="管理中心路段id")),
        ("road_section_name", Excel(name="管理中心路段名称")),
        ("track_id", Excel(name="行驶轨迹id")),
        ("track_josn", Excel(name="行驶轨迹josn")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
        ("longitude_dec", Excel(name="经度")),
        ("latitude_dec", Excel(name="维度")),
    )


__all__ = ["CarTrackInfo"]
