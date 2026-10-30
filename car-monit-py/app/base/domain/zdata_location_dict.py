"""车辆位置字典.

# Migrated from: com/ruoyi/base/domain/ZdataLocationDict.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import Optional

from app.base.domain.ods_types import OdsDate
from app.common.core.domain.domain_model import DomainModel


class ZdataLocationDict(DomainModel):
    """Java: ``com.ruoyi.base.domain.ZdataLocationDict``."""

    id: Optional[int] = None
    type: Optional[str] = None
    name: Optional[str] = None
    raw_code: Optional[str] = None
    standard_code: Optional[str] = None
    roadcode: Optional[str] = None
    roadname: Optional[str] = None
    sectioncode: Optional[str] = None
    sectionname: Optional[str] = None
    tollcode: Optional[str] = None
    tollname: Optional[str] = None
    orgcode: Optional[str] = None
    orgname: Optional[str] = None
    created_at: OdsDate = None
    updated_at: OdsDate = None


__all__ = ["ZdataLocationDict"]
