"""车辆预警配置.

# Migrated from: com/ruoyi/base/domain/CarWarningConfig.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.domain_model import DomainModel


class CarWarningConfig(DomainModel):
    """Java: ``com.ruoyi.base.domain.CarWarningConfig``."""

    id: Optional[str] = None
    gantry_code_in: Optional[str] = None
    gantry_name_in: Optional[str] = None
    gantry_code_out: Optional[str] = None
    gantry_name_out: Optional[str] = None
    time_span: Optional[int] = None
    fwqbm: Optional[str] = None
    fwqmc: Optional[str] = None
    lon: Optional[str] = None
    lat: Optional[str] = None
    road_code: Optional[str] = None
    section_code: Optional[str] = None
    pile_no: Optional[str] = None
    remark: Optional[str] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("gantry_code_in", Excel(name="进入门架编号", read_converter_exp="分=离")),
        ("gantry_name_in", Excel(name="进入门架名称")),
        ("gantry_code_out", Excel(name="出去门架编号", read_converter_exp="分=离")),
        ("gantry_name_out", Excel(name="出去门架名称")),
        ("time_span", Excel(name="判定时间间隔", read_converter_exp="分=钟")),
        ("fwqbm", Excel(name="判定进入的服务区编码")),
        ("fwqmc", Excel(name="判定进入的服务区名称")),
        ("lon", Excel(name="经度")),
        ("lat", Excel(name="维度")),
        ("road_code", Excel(name="路线编码")),
        ("section_code", Excel(name="路段编码")),
        ("pile_no", Excel(name="桩号")),
        ("remark", Excel(name="备注")),
    )


__all__ = ["CarWarningConfig"]
