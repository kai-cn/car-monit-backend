"""上传组件信息.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenerateUploadInfo.java

``@Data + @Accessors(chain = true)``：``initUploadInfo`` 里是链式赋值，
Python 侧拆成三行（语义一致）。字段名 ``uploadFiledNames`` 里的 ``Filed`` 是 Java
原文的**笔误**（应为 ``Field``），照抄 —— 它会作为 JSON 键出现在
``/tool/gen/{tableId}`` 的响应里。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.core.domain.domain_model import DomainModel

# 前置声明，避免与 GenTableColumn 形成 import 环（pydantic 只在类型检查时求值）
if False:  # pragma: no cover - TYPE_CHECKING 的等价写法，见下方 model_rebuild
    from app.generator.domain.gen_table_column import GenTableColumn


class GenerateUploadInfo(DomainModel):
    """Java: ``com.ruoyi.generator.domain.GenerateUploadInfo``."""

    #: 上传组件个数
    upload_count: Optional[int] = None
    #: 上传组件的列信息
    upload_column: Optional[List["GenTableColumn"]] = None
    #: 上传组件的字段名称, 如果存在多个, 则使用,号拼接（Java 原文 uploadFiledNames）
    upload_filed_names: Optional[str] = None


__all__ = ["GenerateUploadInfo"]
