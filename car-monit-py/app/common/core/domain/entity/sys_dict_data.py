# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDictData.java
"""字典数据表 sys_dict_data / dictionary item.

多出来一个 JSON 键：``default``
-------------------------------
Java 除了 ``getIsDefault()``（-> ``"isDefault"``）之外还有一个**计算属性**：

    public boolean getDefault()
    {
        return UserConstants.YES.equals(this.isDefault) ? true : false;
    }

Jackson 把它当成一个只读属性，于是**每一个** ``SysDictData`` 的 JSON 里都会多出一个
``"default": true/false``（``isDefault == "Y"`` 时为 ``true``，``null`` / ``""`` /
``"N"`` / 大小写不符的 ``"y"`` 都是 ``false``）。

Python 侧用 pydantic 的 ``@computed_field`` 复刻：它同样只出现在输出里、不接受入参，
且排在普通字段之后 —— 与 Jackson"先字段、后 getter-only 属性"的顺序一致。

这个键前端**在用**（``v-model`` 绑定下拉框的默认项），删掉会静默失效。

``dictSort`` 是 ``Long``
------------------------
不像 ``SysPost.postSort`` / ``SysMenu.orderNum``（varchar），``dictSort`` 在 Java 里是
``Long``，列类型也是 ``bigint``，所以这里用 ``Optional[int]``，**不是** ``JavaString``。

``DICT_DATA_CONSTRAINTS``
-------------------------
顺序照抄 getter 声明顺序：``dictLabel`` -> ``dictValue`` -> ``dictType`` -> ``cssClass``。
``cssClass`` 只有 ``@Size``，**没有** ``@NotBlank``；``list_class`` / ``isDefault`` /
``status`` / ``dictSort`` 完全没有约束。
"""

from __future__ import annotations

from typing import ClassVar, Optional, Tuple

from pydantic import computed_field

from app.common.annotation.excel import ColumnType, Excel, ExcelFields
from app.common.constant.user_constants import YES
from app.common.core.domain.base_entity import BaseEntity
from app.common.utils.bean_validation import Constraint, NotBlank, Size


class SysDictData(BaseEntity):
    """字典数据对象 sys_dict_data / dict item."""

    #: 字典编码
    dict_code: Optional[int] = None
    #: 字典排序 -- bigint，不是 varchar
    dict_sort: Optional[int] = None
    #: 字典标签
    dict_label: Optional[str] = None
    #: 字典键值
    dict_value: Optional[str] = None
    #: 字典类型
    dict_type: Optional[str] = None
    #: 样式属性（其他样式扩展）
    css_class: Optional[str] = None
    #: 表格字典样式
    list_class: Optional[str] = None
    #: 是否默认（Y是 N否）
    is_default: Optional[str] = None
    #: 状态（0正常 1停用）
    status: Optional[str] = None

    #: ``@Excel`` 注解表 —— ``cssClass`` / ``listClass`` 在 Java 里没有注解，
    #: 所以虽然类上有 9 个字段，导出只有 7 列。列序按 Java 声明顺序。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("dict_code", Excel(name="字典编码", cell_type=ColumnType.NUMERIC)),
        ("dict_sort", Excel(name="字典排序", cell_type=ColumnType.NUMERIC)),
        ("dict_label", Excel(name="字典标签")),
        ("dict_value", Excel(name="字典键值")),
        ("dict_type", Excel(name="字典类型")),
        ("is_default", Excel(name="是否默认", read_converter_exp="Y=是,N=否")),
        ("status", Excel(name="状态", read_converter_exp="0=正常,1=停用")),
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def default(self) -> bool:
        """Java: ``public boolean getDefault()`` —— 由 ``isDefault`` 推导的只读属性。

        严格等值比较 ``"Y"``：小写 ``"y"``、``"1"``、``"true"`` 一律 ``False``
        （``UserConstants.YES.equals(...)`` 是大小写敏感的）。
        """
        return YES == self.is_default


#: ``@Validated @RequestBody SysDictData`` 的校验项，顺序与 Java 里 getter 的声明顺序一致。
DICT_DATA_CONSTRAINTS: Tuple[Constraint, ...] = (
    # Java: @NotBlank(message = "字典标签不能为空") @Size(min = 0, max = 100, ...)
    NotBlank("dict_label", "字典标签不能为空"),
    Size("dict_label", max=100, message="字典标签长度不能超过100个字符"),
    # Java: @NotBlank(message = "字典键值不能为空") @Size(min = 0, max = 100, ...)
    NotBlank("dict_value", "字典键值不能为空"),
    Size("dict_value", max=100, message="字典键值长度不能超过100个字符"),
    # Java: @NotBlank(message = "字典类型不能为空") @Size(min = 0, max = 100, ...)
    NotBlank("dict_type", "字典类型不能为空"),
    Size("dict_type", max=100, message="字典类型长度不能超过100个字符"),
    # Java: 只有 @Size(min = 0, max = 100, ...) —— **没有** @NotBlank
    Size("css_class", max=100, message="样式属性长度不能超过100个字符"),
)


__all__ = ["SysDictData", "DICT_DATA_CONSTRAINTS"]
