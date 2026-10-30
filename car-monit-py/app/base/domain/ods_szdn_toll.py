"""收费站信息.

# Migrated from: com/ruoyi/base/domain/OdsSzdnToll.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import ClassVar, List, Optional

from app.base.domain.ods_types import OdsDate
from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.domain_model import DomainModel


class OdsSzdnToll(DomainModel):
    """Java: ``com.ruoyi.base.domain.OdsSzdnToll``."""

    id: Optional[str] = None
    road_code: Optional[str] = None
    id_card: Optional[str] = None
    toll_code: Optional[str] = None
    toll_name: Optional[str] = None
    pile_no: Optional[str] = None
    org_name: Optional[str] = None
    hex_code: Optional[str] = None
    state_code: Optional[str] = None
    org_code: Optional[str] = None
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    open_date: OdsDate = None
    toll_alias_name: Optional[str] = None
    in_monitor_resource: Optional[str] = None
    lane_monitor_resource: Optional[str] = None
    square_monitor_resource: Optional[str] = None
    dynamic_monitor_resource: Optional[str] = None
    toll_code_merge: Optional[str] = None
    state_code_merge: Optional[str] = None
    toll_name_merge: Optional[str] = None
    section_code: Optional[str] = None
    toll_org_code: Optional[str] = None
    is_access: Optional[str] = None
    #: 路线数组 —— ``@TableField(exist = false)``，只做查询入参，不进 SQL 的 select 列表
    section_code_list: Optional[List[str]] = None
    section_name: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("road_code", Excel(name="路线编号")),
        ("id_card", Excel(name="收费站业务唯一编码")),
        ("toll_code", Excel(name="收费站编号", read_converter_exp="内=部")),
        ("toll_name", Excel(name="收费站名称", read_converter_exp="内=部")),
        ("pile_no", Excel(name="桩号")),
        ("org_name", Excel(name="所属机构名称")),
        ("hex_code", Excel(name="收费站HEX编码")),
        ("state_code", Excel(name="国网编号", read_converter_exp="内=部")),
        ("org_code", Excel(name="机构编码")),
        ("longitude", Excel(name="经度")),
        ("latitude", Excel(name="纬度")),
        ("open_date", Excel(name="开通日期", width=30, date_format="yyyy-MM-dd")),
        ("toll_alias_name", Excel(name="收费站别名")),
        ("in_monitor_resource", Excel(name="入口治超监控资源，多个以英文逗号分割")),
        ("lane_monitor_resource", Excel(name="车道抓拍监控资源，多个以英文逗号分割")),
        ("square_monitor_resource", Excel(name="广场监控资源，多个以英文逗号分割")),
        ("dynamic_monitor_resource", Excel(name="动环监控资源，多个以英文逗号分割")),
        ("toll_code_merge", Excel(name="收费站编号")),
        ("state_code_merge", Excel(name="国网编号")),
        ("toll_name_merge", Excel(name="收费站名称")),
        ("section_code", Excel(name="所属路段编码")),
        ("toll_org_code", Excel(name="收费站对应机构编码")),
        ("is_access", Excel(name="流水是否接入")),
    )


__all__ = ["OdsSzdnToll"]
