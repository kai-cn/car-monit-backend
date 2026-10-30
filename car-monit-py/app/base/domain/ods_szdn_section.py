"""路段信息.

# Migrated from: com/ruoyi/base/domain/OdsSzdnSection.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.base.domain.ods_types import OdsDate
from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.domain_model import DomainModel


class OdsSzdnSection(DomainModel):
    """Java: ``com.ruoyi.base.domain.OdsSzdnSection``."""

    id: Optional[str] = None
    road_code: Optional[str] = None
    road_name: Optional[str] = None
    section_code: Optional[str] = None
    section_name: Optional[str] = None
    start_pile_no: Optional[int] = None
    end_pile_no: Optional[int] = None
    org_code: Optional[str] = None
    org_name: Optional[str] = None
    org_level_code: Optional[str] = None
    org_category: Optional[str] = None
    mileage: Optional[int] = None
    open_date: OdsDate = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("road_code", Excel(name="路线编码")),
        ("road_name", Excel(name="路线名称")),
        ("section_code", Excel(name="路段编码")),
        ("section_name", Excel(name="路段名称")),
        ("start_pile_no", Excel(name="起点桩号")),
        ("end_pile_no", Excel(name="终点桩号")),
        ("org_code", Excel(name="机构代码")),
        ("org_name", Excel(name="机构名称")),
        ("org_level_code", Excel(name="层级代码")),
        ("org_category", Excel(name="机构分类")),
        ("mileage", Excel(name="里程")),
        ("open_date", Excel(name="通车日期", width=30, date_format="yyyy-MM-dd")),
    )


__all__ = ["OdsSzdnSection"]
