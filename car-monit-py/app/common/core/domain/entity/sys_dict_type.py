# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDictType.java
"""字典类型表 sys_dict_type / dictionary type.

放在 ``common.core.domain.entity`` 而不是 ``system.domain``
----------------------------------------------------------
Java 把 ``SysDictType`` 声明在 ``ruoyi-common`` 的 ``entity`` 包里（和 ``SysUser`` /
``SysRole`` / ``SysMenu`` / ``SysDept`` 一起），因为 ``ruoyi-common`` 的
``ExcelUtil`` / ``DictUtils`` 也要引用它。目录位置照抄，所以本文件不在
``app/system/domain`` 下。

只有 4 个自有字段
-----------------
``dictId`` / ``dictName`` / ``dictType`` / ``status``。其余（``createBy`` /
``createTime`` / ``updateBy`` / ``updateTime`` / ``remark`` / ``params``）全部来自
:class:`app.common.core.domain.base_entity.BaseEntity`。

``remark`` 投影里有、resultMap 里没有
-------------------------------------
``<sql id="selectDictTypeVo">`` 的列清单**包含** ``remark``，而
``SysDictTypeResult`` **没有**声明它 —— 靠 MyBatis 的
``autoMappingBehavior=PARTIAL``（默认）把未声明的列自动映射到同名属性，所以
``remark`` 照样有值。Python 侧不需要"声明"，见
:mod:`app.system.mapper.sys_dict_type_mapper`。

``DICT_TYPE_CONSTRAINTS``
-------------------------
Java 把 ``@NotBlank`` / ``@Size`` 挂在 **getter** 上，由 ``SysDictTypeController`` 的
``@Validated @RequestBody`` 触发（``add`` / ``edit`` 两个端点）。顺序与源码一致：
``getDictName`` -> ``getDictType``，这个顺序决定多字段同时违规时
``getFieldError()`` 落在哪一条 —— 也就是客户端看到的那条 ``msg``。

``status`` **没有**任何约束（下拉框只会有 0/1）。
"""

from __future__ import annotations

from typing import ClassVar, Optional, Tuple

from app.common.annotation.excel import ColumnType, Excel, ExcelFields
from app.common.core.domain.base_entity import BaseEntity
from app.common.utils.bean_validation import Constraint, NotBlank, Size


class SysDictType(BaseEntity):
    """字典类型对象 sys_dict_type / dict type."""

    #: 字典主键
    dict_id: Optional[int] = None
    #: 字典名称
    dict_name: Optional[str] = None
    #: 字典类型
    dict_type: Optional[str] = None
    #: 状态（0正常 1停用）
    status: Optional[str] = None

    #: ``@Excel`` 注解表 —— 就是这 4 个字段，``BaseEntity`` 上没有注解。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("dict_id", Excel(name="字典主键", cell_type=ColumnType.NUMERIC)),
        ("dict_name", Excel(name="字典名称")),
        ("dict_type", Excel(name="字典类型")),
        ("status", Excel(name="状态", read_converter_exp="0=正常,1=停用")),
    )


#: ``@Validated @RequestBody SysDictType`` 的校验项，顺序与 Java 里 getter 的声明顺序一致。
DICT_TYPE_CONSTRAINTS: Tuple[Constraint, ...] = (
    # Java: @NotBlank(message = "字典名称不能为空") @Size(min = 0, max = 100, ...)
    NotBlank("dict_name", "字典名称不能为空"),
    Size("dict_name", max=100, message="字典类型名称长度不能超过100个字符"),
    # Java: @NotBlank(message = "字典类型不能为空") @Size(min = 0, max = 100, ...)
    # 注意文案里多了一个"类型"：原文是"字典类型类型长度不能超过100个字符"
    NotBlank("dict_type", "字典类型不能为空"),
    Size("dict_type", max=100, message="字典类型类型长度不能超过100个字符"),
)


__all__ = ["SysDictType", "DICT_TYPE_CONSTRAINTS"]
