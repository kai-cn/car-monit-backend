"""门架信息.

# Migrated from: com/ruoyi/base/domain/OdsSzdnGantry.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.core.domain.domain_model import DomainModel


class OdsSzdnGantry(DomainModel):
    """Java: ``com.ruoyi.base.domain.OdsSzdnGantry``."""

    id: Optional[str] = None
    gantry_code: Optional[str] = None
    gantry_name: Optional[str] = None
    road_code: Optional[str] = None
    section_code: Optional[str] = None
    toll_code: Optional[str] = None
    org_code: Optional[str] = None
    hex_code: Optional[str] = None
    direction: Optional[str] = None
    pile_no: Optional[str] = None
    lon: Optional[str] = None
    lat: Optional[str] = None
    is_virtual: Optional[str] = None
    mileage: Optional[str] = None
    boundary_gantry_type: Optional[str] = None
    gantry_type: Optional[str] = None
    city_code: Optional[str] = None
    district_name: Optional[str] = None
    belong_group: Optional[str] = None
    gantry_code_merge: Optional[str] = None
    gantry_name_alias: Optional[str] = None
    remark: Optional[str] = None
    #: 路线数组 —— ``@TableField(exist = false)``，只做查询入参，不进 SQL 的 select 列表
    section_code_list: Optional[List[str]] = None
    is_data: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    road_name: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    section_name: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    toll_name: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL
    org_name: Optional[str] = None  # @TableField(exist = false) —— 只出现在 JSON，不进 SQL


__all__ = ["OdsSzdnGantry"]
