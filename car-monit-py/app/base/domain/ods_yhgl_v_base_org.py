"""机构信息.

# Migrated from: com/ruoyi/base/domain/OdsYhglVBaseOrg.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.base.domain.ods_types import OdsDate
from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.domain_model import DomainModel


class OdsYhglVBaseOrg(DomainModel):
    """Java: ``com.ruoyi.base.domain.OdsYhglVBaseOrg``."""

    big_id: Optional[str] = None
    org_code: Optional[str] = None
    org_name: Optional[str] = None
    org_short_name: Optional[str] = None
    org_parent_id: Optional[str] = None
    org_level_code: Optional[str] = None
    org_is_virtual: Optional[str] = None
    org_maintenance: Optional[str] = None
    org_sequence: Optional[int] = None
    org_is_manager: Optional[str] = None
    org_is_deleted: Optional[str] = None
    org_category: Optional[str] = None
    org_is_authorized: Optional[str] = None
    org_address: Optional[str] = None
    org_is_yh_autarky: Optional[str] = None
    load_time: OdsDate = None
    grade_level: Optional[int] = None
    parent_id: Optional[int] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("org_code", Excel(name="机构代码")),
        ("org_name", Excel(name="机构名称")),
        ("org_short_name", Excel(name="机构简称")),
        ("org_parent_id", Excel(name="上级机构ID")),
        ("org_level_code", Excel(name="层级代码")),
        ("org_is_virtual", Excel(name="是否虚机构 1：虚机构，0：非需机构")),
        ("org_maintenance", Excel(name="是否是养护类", read_converter_exp="1=：是，0否")),
        ("org_sequence", Excel(name="机构顺序")),
        ("org_is_manager", Excel(name="是否管理单位，主要指是否是路段管理单位(1：是,0：否)")),
        ("org_is_deleted", Excel(name="是否删除 1：是 0：否")),
        (
            "org_category",
            Excel(
                name="机构分类： 01集团 02公司 03管理中心 10部门 11所 12服务区 13养护区 14站 15项目办 16信息中心 17项目部  99其它",
                width=30,
                date_format="yyyy-MM-dd",
            ),
        ),
        ("org_is_authorized", Excel(name="是否授权机构 1：是 0：否")),
        ("org_address", Excel(name="机构地址")),
        ("org_is_yh_autarky", Excel(name="是自营养护单位")),
        ("load_time", Excel(name="加载时间", width=30, date_format="yyyy-MM-dd")),
        ("grade_level", Excel(name="分类分级")),
    )


__all__ = ["OdsYhglVBaseOrg"]
