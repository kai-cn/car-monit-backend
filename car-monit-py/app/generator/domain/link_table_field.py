"""关联表字段映射信息.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/LinkTableField.java
# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/util/enumeration/LinkTableFiledTypeEnum.java

``LinkTableFiledTypeEnum`` 只有两个成员（``TABLE("10")`` / ``CUSTOM_FIELD("20")``），
而且**只**被 ``GenTableServiceImpl#initLinkTableInfo`` 用来做 ``fieldType`` 相等判断。
它按 Java 的包路径放在 :mod:`app.generator.util.enumeration` 下（不在这里重复定义），
本模块只是再导出一次，方便按领域对象聚合着引用。

``getCustomFileComment()`` 的"空串兜底"
-----------------------------------------
Java 的 getter 在字段为 ``null`` 或 ``""`` 时返回 ``Constants.CHAR_BLANK``（空串），
所以 **JSON 里 ``customFileComment`` 永远是字符串，不会是 null**。这条用
``field_serializer`` 复刻，否则生成 Vue 模板里的 ``<el-table-column label="...">``
会渲染成 ``undefined``。
"""

from __future__ import annotations

from typing import Optional

from pydantic import field_serializer

from app.common.constant.constants import CHAR_BLANK
from app.common.core.domain.domain_model import DomainModel
from app.generator.util.enumeration.link_table_filed_type_enum import LinkTableFiledTypeEnum

if False:  # pragma: no cover - 只给类型检查器看
    from app.generator.domain.gen_table_column import GenTableColumn


class LinkTableField(DomainModel):
    """Java: ``com.ruoyi.generator.domain.LinkTableField``."""

    #: 字段类型。``"10"`` 取 ``currentTableFileId``，``"20"`` 取 ``customFieldName``
    field_type: Optional[str] = None
    #: 当前表字段id
    current_table_file_id: Optional[int] = None
    #: 关联表字段id
    link_table_field_id: Optional[int] = None
    #: 自定义字段名称
    custom_field_name: Optional[str] = None
    #: 自定义字段注释
    custom_file_comment: Optional[str] = None
    #: 表字段别名, 将id转换成name
    table_file_alias: Optional[str] = None
    #: 表字段信息
    table_file_info: Optional["GenTableColumn"] = None
    #: 关联表字段信息
    link_table_field_info: Optional["GenTableColumn"] = None

    def get_custom_file_comment(self) -> str:
        """Java: ``getCustomFileComment()`` —— 空值兜底成空串（**不是** null）."""
        if self.custom_file_comment is None or self.custom_file_comment == "":
            return CHAR_BLANK
        return self.custom_file_comment

    @field_serializer("custom_file_comment")
    def _serialize_custom_file_comment(self, _value: Optional[str]) -> str:
        """Jackson 走 getter，所以序列化结果永远是 getter 的返回值."""
        return self.get_custom_file_comment()


__all__ = ["LinkTableField", "LinkTableFiledTypeEnum"]
