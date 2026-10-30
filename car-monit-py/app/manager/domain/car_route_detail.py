"""常用路线明细对象 car_route_detail.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteDetail.java

``extends BasePlusEntity``（``@TableId`` = ``ASSIGN_UUID``）。
``last_pass_time`` / ``next_pass_time`` 是 ``java.util.Date`` + ``@JsonFormat("yyyy-MM-dd")`` —— 序列化成**日期**字符串，Python 侧同样按 ``date`` 存取。
``apply_time1`` / ``apply_time2`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntity


class CarRouteDetail(BasePlusEntity):
    """Java: ``com.ruoyi.manager.domain.CarRouteDetail``."""

    #: 路线d
    route_id: Optional[str] = None
    #: 车辆id
    car_id: Optional[str] = None
    #: 车牌号
    car_no: Optional[str] = None
    #: 数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)
    data_source: Optional[str] = None
    #: 来源名称
    data_source_name: Optional[str] = None
    #: 最后通行时间
    last_pass_time: Optional[date] = None
    #: 最后通行图片
    last_pass_picture: Optional[str] = None
    #: 最后通行类型(1?架2收费拍)3服务区)
    last_pass_type: Optional[str] = None
    #: 最后通行地址
    last_pass_address: Optional[str] = None
    #: 最后通行经度
    last_pass_longitude: Optional[str] = None
    #: 最后通行维度
    last_pass_latitude: Optional[str] = None
    #: ⾏驶⽅向(1上行2下行3未知)
    last_pass_cardirection: Optional[str] = None
    #: 管理中心路段id
    road_section_id: Optional[str] = None
    #: 管理中心路段名称
    road_section_name: Optional[str] = None
    #: 预计下一个通行时间
    next_pass_time: Optional[date] = None
    #: 预计下一个通行类型
    next_pass_type: Optional[str] = None
    #: 预计下一个通行地址
    next_pass_address: Optional[str] = None
    #: 预计下一个通行经度
    next_pass_longitude: Optional[str] = None
    #: 预计下一个通行维度
    next_pass_latitude: Optional[str] = None
    #: 管理中心id
    org_id: Optional[str] = None
    #: 管理中心名称
    org_name: Optional[str] = None
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

    #: ``@Excel`` 注解表（导出走 ``ExcelUtil``，表头顺序即此顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("route_id", Excel(name="路线d")),
        ("car_id", Excel(name="车辆id")),
        ("car_no", Excel(name="车牌号")),
        ("data_source", Excel(name="数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)")),
        ("data_source_name", Excel(name="来源名称")),
        ("last_pass_time", Excel(name="最后通行时间", width=30, date_format="yyyy-MM-dd")),
        ("last_pass_picture", Excel(name="最后通行图片")),
        ("last_pass_type", Excel(name="最后通行类型(1?架2收费拍)3服务区)")),
        ("last_pass_address", Excel(name="最后通行地址")),
        ("last_pass_longitude", Excel(name="最后通行经度")),
        ("last_pass_latitude", Excel(name="最后通行维度")),
        ("last_pass_cardirection", Excel(name="⾏驶⽅向(1上行2下行3未知)")),
        ("road_section_id", Excel(name="管理中心路段id")),
        ("road_section_name", Excel(name="管理中心路段名称")),
        ("next_pass_time", Excel(name="预计下一个通行时间", width=30, date_format="yyyy-MM-dd")),
        ("next_pass_type", Excel(name="预计下一个通行类型")),
        ("next_pass_address", Excel(name="预计下一个通行地址")),
        ("next_pass_longitude", Excel(name="预计下一个通行经度")),
        ("next_pass_latitude", Excel(name="预计下一个通行维度")),
        ("org_id", Excel(name="管理中心id")),
        ("org_name", Excel(name="管理中心名称")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["CarRouteDetail"]
