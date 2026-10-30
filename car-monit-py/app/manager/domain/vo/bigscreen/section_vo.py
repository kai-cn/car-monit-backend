"""路段 VO（大屏用，``SectionVO``）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/SectionVO.java

``/manager/bigScreen/sectionList`` 的返回元素：只带编码与名称两个字段。
首条是硬编码的"全部"（``sectionCode = "all"`` / ``sectionName = "全部"``）。
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class SectionVO(DomainModel):
    """Java: ``com.ruoyi.manager.domain.vo.bigscreen.SectionVO``."""

    #: 所属路段编码
    section_code: Optional[str] = None
    #: 所属路段名称
    section_name: Optional[str] = None


__all__ = ["SectionVO"]
