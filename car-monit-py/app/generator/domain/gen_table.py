"""代码生成业务表 gen_table.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenTable.java

字段顺序与 Java 声明顺序一致（``columns`` 在 ``pkColumn`` / ``subTable`` 之后），
因为 ``/tool/gen/{tableId}`` 与 ``/tool/gen/list`` 的响应体是**逐字节**给前端用的，
键序一变，``index.vue`` 之外任何按位置下标取值的地方都会跟着变。

Jackson 派生属性
----------------
``isSub()`` / ``isTree()`` / ``isCrud()`` 三个无参 boolean 方法会被 Jackson 当成
属性输出，键名分别是 ``sub`` / ``tree`` / ``crud``。前端的 ``tplCategory`` 下拉框与
``v-if="table.tree"`` 判断都读它们，所以用 ``@computed_field`` 补上。

``isSuperColumn(String)`` 有参数，**不**是 Jackson 属性，不会出现在 JSON 里；
但它被模板（``domain.java.vm`` / ``mapper.xml.vm``）调用，必须保留成方法。

``GEN_TABLE_CONSTRAINTS``
-------------------------
Java 把 8 个 ``@NotBlank`` 挂在**字段**上，由 ``GenController#editSave`` 的
``@Validated @RequestBody`` 触发。这里按源码顺序抄成约束表，由端点显式
:func:`validate`（见 ``app.api.tool.gen_controller``）。
注意 ``columns`` 上有 ``@Valid``（级联校验），所以 **``GenTableColumn`` 的
``javaField`` 约束也会在同一个请求里生效** —— 级联表放在
:data:`app.generator.domain.gen_table_column.GEN_TABLE_COLUMN_CONSTRAINTS`。

命名冲突
--------
Java 允许 ``isSub()`` 与 ``isSub(String)`` 重载共存，Python 不行。这里：
无参方法保留 Java 名字（``is_sub()``），静态重载统一加 ``_for`` 后缀
（``is_sub_for(tpl_category)``）。模板只用到无参那三个与
``isSuperColumn(tplCategory, javaField)`` 的**静态**形式（模板里写成
``$table.isSuperColumn($tplCategory, ...)`` 走的是同名方法），所以再提供一个
``is_super_column(java_field)`` 实例方法 + ``is_super_column_for(tpl_category, java_field)``。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import computed_field

from app.common.constant.gen_constants import BASE_ENTITY, TPL_CRUD, TPL_SUB, TPL_TREE, TREE_ENTITY
from app.common.core.domain.base_entity import BaseEntity
from app.common.utils.bean_validation import Constraint, NotBlank
from app.common.utils.string_utils import in_string_ignore_case

if False:  # pragma: no cover - 只给类型检查器看
    from app.generator.domain.dictionary_info import DictionaryInfo
    from app.generator.domain.gen_column_dialog import GenColumnDialog
    from app.generator.domain.gen_table_column import GenTableColumn
    from app.generator.domain.generate_rich_text_info import GenerateRichTextInfo
    from app.generator.domain.generate_upload_info import GenerateUploadInfo


class GenTable(BaseEntity):
    """Java: ``com.ruoyi.generator.domain.GenTable``."""

    #: 编号
    table_id: Optional[int] = None
    #: 表名称（``@NotBlank(message = "表名称不能为空")``）
    table_name: Optional[str] = None
    #: 表描述（``@NotBlank(message = "表描述不能为空")``）
    table_comment: Optional[str] = None
    #: 关联父表的表名
    sub_table_name: Optional[str] = None
    #: 本表关联父表的外键名
    sub_table_fk_name: Optional[str] = None
    #: 实体类名称(首字母大写)（``@NotBlank``）
    class_name: Optional[str] = None
    #: 使用的模板（crud单表操作 tree树表操作 sub主子表操作）
    tpl_category: Optional[str] = None
    #: 生成包路径（``@NotBlank``）
    package_name: Optional[str] = None
    #: 生成模块名（``@NotBlank``）
    module_name: Optional[str] = None
    #: 生成业务名（``@NotBlank``）
    business_name: Optional[str] = None
    #: 生成功能名（``@NotBlank``）
    function_name: Optional[str] = None
    #: 生成作者（``@NotBlank``）
    function_author: Optional[str] = None
    #: 生成代码方式（0zip压缩包 1自定义路径）
    gen_type: Optional[str] = None
    #: 生成路径（不填默认项目路径）
    gen_path: Optional[str] = None
    #: 主键信息
    pk_column: Optional["GenTableColumn"] = None
    #: 子表信息
    sub_table: Optional["GenTable"] = None
    #: 表列信息
    columns: Optional[List["GenTableColumn"]] = None
    #: 字典信息
    dictionary_info_list: Optional[List["DictionaryInfo"]] = None
    #: 字典键, 逗号拼接
    dictionary_info_string: Optional[str] = None
    #: 其它生成选项
    options: Optional[str] = None
    #: 树编码字段
    tree_code: Optional[str] = None
    #: 树父编码字段
    tree_parent_code: Optional[str] = None
    #: 树名称字段
    tree_name: Optional[str] = None
    #: 上级菜单ID字段
    parent_menu_id: Optional[str] = None
    #: 上级菜单名称字段
    parent_menu_name: Optional[str] = None
    #: 生成代码-字典列表键后缀
    dictionary_list_key_suffix: Optional[str] = None
    #: 上传文件信息
    upload_info: Optional["GenerateUploadInfo"] = None
    #: 富文本信息列表
    rich_text_info: Optional["GenerateRichTextInfo"] = None
    #: 字段对话框信息
    column_dialog_info: Optional["GenColumnDialog"] = None
    #: 已过滤列表信息
    filter_column_list: Optional[List["GenTableColumn"]] = None

    # ------------------------------------------------------------------ 派生属性

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sub(self) -> bool:
        """Java: ``isSub()`` -> Jackson 属性 ``sub``."""
        return self.is_sub()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tree(self) -> bool:
        """Java: ``isTree()`` -> Jackson 属性 ``tree``."""
        return self.is_tree()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def crud(self) -> bool:
        """Java: ``isCrud()`` -> Jackson 属性 ``crud``."""
        return self.is_crud()

    # ------------------------------------------------------------------ 业务方法

    def is_sub(self) -> bool:
        """Java: ``boolean isSub()``."""
        return self.is_sub_for(self.tpl_category)

    @staticmethod
    def is_sub_for(tpl_category: Optional[str]) -> bool:
        """Java: ``static boolean isSub(String tplCategory)``."""
        return tpl_category is not None and tpl_category == TPL_SUB

    def is_tree(self) -> bool:
        """Java: ``boolean isTree()``."""
        return self.is_tree_for(self.tpl_category)

    @staticmethod
    def is_tree_for(tpl_category: Optional[str]) -> bool:
        """Java: ``static boolean isTree(String tplCategory)``."""
        return tpl_category is not None and tpl_category == TPL_TREE

    def is_crud(self) -> bool:
        """Java: ``boolean isCrud()``."""
        return self.is_crud_for(self.tpl_category)

    @staticmethod
    def is_crud_for(tpl_category: Optional[str]) -> bool:
        """Java: ``static boolean isCrud(String tplCategory)``."""
        return tpl_category is not None and tpl_category == TPL_CRUD

    def is_super_column(self, java_field: Optional[str]) -> bool:
        """Java: ``boolean isSuperColumn(String javaField)``."""
        return self.is_super_column_for(self.tpl_category, java_field)

    @staticmethod
    def is_super_column_for(tpl_category: Optional[str], java_field: Optional[str]) -> bool:
        """Java: ``static boolean isSuperColumn(String tplCategory, String javaField)``.

        树表要多排除 ``TREE_ENTITY`` 的字段，且判断走
        ``StringUtils.equalsAnyIgnoreCase``（忽略大小写、对候选 ``trim``）。
        """
        if GenTable.is_tree_for(tpl_category):
            return in_string_ignore_case(java_field, *(list(TREE_ENTITY) + list(BASE_ENTITY)))
        return in_string_ignore_case(java_field, *BASE_ENTITY)


#: Java ``GenTable`` 字段上的 ``@NotBlank``，**顺序与源码声明序一致**
#: （这个顺序决定了多字段同时为空时 ``getFieldError()`` 落在哪一条）。
GEN_TABLE_CONSTRAINTS: Tuple[Constraint, ...] = (
    # Java: @NotBlank(message = "表名称不能为空")
    NotBlank("table_name", "表名称不能为空"),
    # Java: @NotBlank(message = "表描述不能为空")
    NotBlank("table_comment", "表描述不能为空"),
    # Java: @NotBlank(message = "实体类名称不能为空")
    NotBlank("class_name", "实体类名称不能为空"),
    # Java: @NotBlank(message = "生成包路径不能为空")
    NotBlank("package_name", "生成包路径不能为空"),
    # Java: @NotBlank(message = "生成模块名不能为空")
    NotBlank("module_name", "生成模块名不能为空"),
    # Java: @NotBlank(message = "生成业务名不能为空")
    NotBlank("business_name", "生成业务名不能为空"),
    # Java: @NotBlank(message = "生成功能名不能为空")
    NotBlank("function_name", "生成功能名不能为空"),
    # Java: @NotBlank(message = "作者不能为空")
    NotBlank("function_author", "作者不能为空"),
)


__all__ = ["GenTable", "GEN_TABLE_CONSTRAINTS"]
