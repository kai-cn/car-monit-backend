"""车辆信息对象 car_info.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarInfo.java

``extends BasePlusEntityInputNew``（``@TableId`` = ``INPUT``）。
``last_pass_time`` / ``next_pass_time`` 是 ``java.util.Date`` + ``@JsonFormat("yyyy-MM-dd")`` —— 序列化成**日期**字符串，Python 侧同样按 ``date`` 存取。
``apply_time1`` / ``apply_time2`` / ``car_no_query`` / ``create_time_str`` / ``create_info`` / ``trail_list`` / ``flag`` 是 ``@TableField(exist = false)`` 的查询入参（区间查询 / 未落库的展示字段），不出现在 ``resultMap`` 里，因此也不会出现在响应体中。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, ClassVar, List, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.base_plus_entity import BasePlusEntityInputNew


class CarInfo(BasePlusEntityInputNew):
    """Java: ``com.ruoyi.manager.domain.CarInfo``."""

    #: 车牌号
    car_no: Optional[str] = None
    #: 车型
    car_type: Optional[str] = None
    #: 车种
    car_vehicle: Optional[str] = None
    #: 轴数
    car_num: Optional[int] = None
    #: 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
    escaped_type: Optional[str] = None
    #: 逃费类型名称
    escaped_type_name: Optional[str] = None
    #: 逃费金额（元）
    #:
    #: 五列金额在 Java 侧都是 ``BigDecimal``、库里是 ``decimal(19,2)``。标度（两位小数）
    #: 只在 ``Decimal`` 上存在，而 EasyPOI 模板导出写的是 ``String.valueOf(getter())``
    #: —— 用 ``float`` 会把 ``16075.00`` 塌成 ``16075.0``，导出的格子就跟 Java 不一致。
    escaped_amount: Optional[Decimal] = None
    #: 逃费次数(反改)
    escaped_num: Optional[int] = None
    #: 累计追缴金额（元）
    return_amount: Optional[Decimal] = None
    #: 应缴金额
    total_amount: Optional[Decimal] = None
    #: 收费金额
    charge_amount: Optional[Decimal] = None
    #: 差额
    dif_amount: Optional[Decimal] = None
    #: 处理单位id
    auit_org_id: Optional[str] = None
    #: 处理单位
    auit_org_name: Optional[str] = None
    #: 是否在白名单（0否1是）
    is_white: Optional[str] = None
    #: 白名单原因
    white_remark: Optional[str] = None
    #: 图片(附件ids)
    file_ids: Optional[str] = None
    #: 车辆品牌
    brand: Optional[str] = None
    #: 车牌颜色（字典：1白色2黑色）
    plate_color: Optional[str] = None
    #: 车牌类型
    plate_type: Optional[str] = None
    #: 车辆颜色（字典：1白色2黑色）
    car_color: Optional[str] = None
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
    #: 驾驶(1上行2下行3未知)
    last_pass_cardirection: Optional[str] = None
    #: 管理中心路段id
    road_section_id: Optional[str] = None
    #: 所属路段编码
    section_code: Optional[str] = None
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
    #: 行驶轨迹id
    track_id: Optional[str] = None
    #: 行驶轨迹josn
    track_josn: Optional[str] = None
    #: 管理中心id
    org_id: Optional[str] = None
    #: 所属管理中心机构编码
    org_code: Optional[str] = None
    #: 管理中心名称
    org_name: Optional[str] = None
    #: 门架编号（分离）
    gantry_code: Optional[str] = None
    #: 所属路线编码
    road_code: Optional[str] = None
    #: 所属路线名称
    road_name: Optional[str] = None
    #: 所属收费站编码
    toll_code: Optional[str] = None
    #: 所属收费站名称
    toll_name: Optional[str] = None
    #: 司机名称
    link_name: Optional[str] = None
    #: 联系方式
    link_phone: Optional[str] = None
    #: 服务区编码
    fwqbm: Optional[str] = None
    #: 服务区名称
    fwqmc: Optional[str] = None
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
    #: 车牌号查询
    car_no_query: Optional[str] = None
    #: 查询时间
    create_time_str: Optional[str] = None
    #: 录入单位以及用户
    create_info: Optional[str] = None
    #: 车俩轨迹
    trail_list: Optional[List[Any]] = None
    #: 标识
    flag: Optional[str] = None

    #: ``@Excel`` 注解表（导出走 ``ExcelUtil``，表头顺序即此顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("car_no", Excel(name="车牌号")),
        ("car_type", Excel(name="车型")),
        ("car_vehicle", Excel(name="车种")),
        ("car_num", Excel(name="轴数")),
        ("escaped_type", Excel(name="逃费类型", read_converter_exp="字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂")),
        ("escaped_type_name", Excel(name="逃费类型名称")),
        ("escaped_amount", Excel(name="逃费金额", read_converter_exp="元=")),
        ("escaped_num", Excel(name="逃费次数(反改)")),
        ("return_amount", Excel(name="累计追缴金额", read_converter_exp="元=")),
        ("total_amount", Excel(name="应缴金额")),
        ("charge_amount", Excel(name="收费金额")),
        ("dif_amount", Excel(name="差额")),
        ("auit_org_id", Excel(name="处理单位id")),
        ("auit_org_name", Excel(name="处理单位")),
        ("is_white", Excel(name="是否在白名单", read_converter_exp="0=否1是")),
        ("white_remark", Excel(name="白名单原因")),
        ("file_ids", Excel(name="图片(附件ids)")),
        ("brand", Excel(name="车辆品牌")),
        ("plate_color", Excel(name="车牌颜色", read_converter_exp="字=典：1白色2黑色")),
        ("plate_type", Excel(name="车牌类型")),
        ("car_color", Excel(name="车辆颜色", read_converter_exp="字=典：1白色2黑色")),
        ("data_source", Excel(name="数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)")),
        ("data_source_name", Excel(name="来源名称")),
        ("last_pass_time", Excel(name="最后通行时间", width=30, date_format="yyyy-MM-dd")),
        ("last_pass_picture", Excel(name="最后通行图片")),
        ("last_pass_type", Excel(name="最后通行类型(1?架2收费拍)3服务区)")),
        ("last_pass_address", Excel(name="最后通行地址")),
        ("last_pass_longitude", Excel(name="最后通行经度")),
        ("last_pass_latitude", Excel(name="最后通行维度")),
        ("last_pass_cardirection", Excel(name="驾驶(1上行2下行3未知)")),
        ("road_section_id", Excel(name="管理中心路段id")),
        ("section_code", Excel(name="所属路段编码")),
        ("road_section_name", Excel(name="管理中心路段名称")),
        ("next_pass_time", Excel(name="预计下一个通行时间", width=30, date_format="yyyy-MM-dd")),
        ("next_pass_type", Excel(name="预计下一个通行类型")),
        ("next_pass_address", Excel(name="预计下一个通行地址")),
        ("next_pass_longitude", Excel(name="预计下一个通行经度")),
        ("next_pass_latitude", Excel(name="预计下一个通行维度")),
        ("track_id", Excel(name="行驶轨迹id")),
        ("track_josn", Excel(name="行驶轨迹josn")),
        ("org_id", Excel(name="管理中心id")),
        ("org_code", Excel(name="所属管理中心机构编码")),
        ("org_name", Excel(name="管理中心名称")),
        ("gantry_code", Excel(name="门架编号", read_converter_exp="分=离")),
        ("road_code", Excel(name="所属路线编码")),
        ("road_name", Excel(name="所属路线名称")),
        ("toll_code", Excel(name="所属收费站编码")),
        ("toll_name", Excel(name="所属收费站名称")),
        ("link_name", Excel(name="司机名称")),
        ("link_phone", Excel(name="联系方式")),
        ("fwqbm", Excel(name="服务区编码")),
        ("fwqmc", Excel(name="服务区名称")),
        ("back_col1", Excel(name="备用字段1")),
        ("back_col2", Excel(name="备用字段2")),
        ("status", Excel(name="状态", read_converter_exp="0=正常1停用")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["CarInfo"]
