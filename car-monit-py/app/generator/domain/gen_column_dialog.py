"""列表对话框信息.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenColumnDialog.java

纯 ``@Data`` 搬运对象，没有派生属性，也没有 getter 改写 —— 9 个字段的 JSON 键
与字段名一一对应（``dialogNumber`` / ``checkboxNumber`` / ``radioNumber`` /
``dialogColumnList`` / ``checkBoxColumnList`` / ``radioColumnList`` /
``tableFieldList`` / ``customFieldList`` / ``fieldList``）。

注意 ``checkBoxColumnList`` 的 ``Box`` 是**大写 B** —— Lombok 由字段
``checkBoxColumnList`` 生成 ``getCheckBoxColumnList()``，Jackson 由此得到
``checkBoxColumnList``。若写成 ``checkboxColumnList``，``index.vue`` 里
``columnDialogInfo.checkBoxColumnList`` 会取不到值。
"""

from __future__ import annotations

from typing import List, Optional

from app.common.core.domain.domain_model import DomainModel

if False:  # pragma: no cover - 只给类型检查器看
    from app.generator.domain.gen_table_column import GenTableColumn
    from app.generator.domain.link_table_field import LinkTableField


class GenColumnDialog(DomainModel):
    """Java: ``com.ruoyi.generator.domain.GenColumnDialog``."""

    #: 列表对话框数量
    dialog_number: Optional[int] = None
    #: 多选对话框数量
    checkbox_number: Optional[int] = None
    #: 单选对话框数量
    radio_number: Optional[int] = None
    #: 对话框列表
    dialog_column_list: Optional[List["GenTableColumn"]] = None
    #: 多选对话框列表
    check_box_column_list: Optional[List["GenTableColumn"]] = None
    #: 单选对话框列表
    radio_column_list: Optional[List["GenTableColumn"]] = None
    #: 全部-表字段列表
    table_field_list: Optional[List["LinkTableField"]] = None
    #: 全部-自定义字段列表
    custom_field_list: Optional[List["LinkTableField"]] = None
    #: 全部-字段列表信息
    field_list: Optional[List["LinkTableField"]] = None


__all__ = ["GenColumnDialog"]
