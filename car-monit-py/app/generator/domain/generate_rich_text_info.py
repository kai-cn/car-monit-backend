"""富文本信息.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenerateRichTextInfo.java
"""

from __future__ import annotations

from typing import List, Optional

from app.common.core.domain.domain_model import DomainModel

if False:  # pragma: no cover - 只给类型检查器看
    from app.generator.domain.gen_table_column import GenTableColumn


class GenerateRichTextInfo(DomainModel):
    """Java: ``com.ruoyi.generator.domain.GenerateRichTextInfo``."""

    #: 富文本组件数量
    rich_text_count: Optional[int] = None
    #: 富文本组件字段列表
    column_list: Optional[List["GenTableColumn"]] = None


__all__ = ["GenerateRichTextInfo"]
