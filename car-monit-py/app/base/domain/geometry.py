"""几何对象.

# Migrated from: com/ruoyi/base/domain/Geometry.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.domain_model import DomainModel


class Geometry(DomainModel):
    """Java: ``com.ruoyi.base.domain.Geometry``."""

    id: Optional[int] = None
    lxbh: Optional[str] = None
    lxfx: Optional[str] = None
    qdzh: Optional[int] = None
    zdzh: Optional[int] = None
    paths: Optional[str] = None
    zh_str: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("lxbh", Excel(name="路线编号")),
        ("lxfx", Excel(name="路线方向")),
        ("qdzh", Excel(name="起点桩号")),
        ("zdzh", Excel(name="终点桩号")),
        ("paths", Excel(name="经纬度")),
    )


__all__ = ["Geometry"]
