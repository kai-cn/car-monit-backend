"""代码生成器领域对象.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/domain

7 个 Java 类的落点：

    ==========================  ==========================================
    Java 类                     Python 模块
    ==========================  ==========================================
    ``GenTable``                :mod:`gen_table`
    ``GenTableColumn``          :mod:`gen_table_column`
    ``GenColumnDialog``         :mod:`gen_column_dialog`
    ``DictionaryInfo``          :mod:`dictionary_info`
    ``GenerateUploadInfo``      :mod:`generate_upload_info`
    ``GenerateRichTextInfo``    :mod:`generate_rich_text_info`
    ``LinkTableField``          :mod:`link_table_field`
    ==========================  ==========================================

为什么要在这里统一 ``model_rebuild()``
------------------------------------
这 7 个类**互相引用**（``GenTable.columns -> GenTableColumn ->
GenTableColumn.linkTable -> GenTable``、``LinkTableField.tableFileInfo ->
GenTableColumn`` …），而且都在 ``if False:`` 块里写的 ``import``，只服务于类型
检查器。pydantic 在**定义**时不会解析这些前向引用，必须等到所有类都定义完
再统一 ``model_rebuild`` 一次，否则第一次 ``GenTable.model_validate(...)``
会抛 ``PydanticUndefinedAnnotation``。

集中放在包的 ``__init__`` 里，调用方只要 ``import app.generator.domain``
就拿到"已解析完"的类，不必自己记得 rebuild 顺序。
"""

from __future__ import annotations

from typing import Any, Dict

from app.generator.domain.dictionary_info import DictionaryInfo
from app.generator.domain.gen_column_dialog import GenColumnDialog
from app.generator.domain.gen_table import GenTable
from app.generator.domain.gen_table_column import GenTableColumn
from app.generator.domain.generate_rich_text_info import GenerateRichTextInfo
from app.generator.domain.generate_upload_info import GenerateUploadInfo
from app.generator.domain.link_table_field import LinkTableField, LinkTableFiledTypeEnum

#: 前向引用的解析命名空间 —— 所有互相引用的类都必须在这里。
_NAMESPACE: Dict[str, Any] = {
    "GenTable": GenTable,
    "GenTableColumn": GenTableColumn,
    "GenColumnDialog": GenColumnDialog,
    "DictionaryInfo": DictionaryInfo,
    "GenerateUploadInfo": GenerateUploadInfo,
    "GenerateRichTextInfo": GenerateRichTextInfo,
    "LinkTableField": LinkTableField,
}

for _model in (
    GenTable,
    GenTableColumn,
    GenColumnDialog,
    DictionaryInfo,
    GenerateUploadInfo,
    GenerateRichTextInfo,
    LinkTableField,
):
    _model.model_rebuild(_types_namespace=_NAMESPACE)

__all__ = [
    "GenTable",
    "GenTableColumn",
    "GenColumnDialog",
    "DictionaryInfo",
    "GenerateUploadInfo",
    "GenerateRichTextInfo",
    "LinkTableField",
    "LinkTableFiledTypeEnum",
]
