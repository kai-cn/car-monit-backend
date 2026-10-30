"""代码生成通用常量.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/constant/GenConstants.java

Java 用 ``public static final`` 字段存放这些值；Python 没有常量语义，这里只做一个
**命名空间**。所有字面量逐字照抄，理由：它们的值会进入 ``gen_table`` /
``gen_table_column`` 落库（``tpl_category`` / ``java_type`` / ``html_type`` /
``query_type``），一旦改动，历史行与新建行的语义就会分叉，代码生成结果随之改变。

``COLUMNTYPE_*`` / ``COLUMNNAME_*`` / ``BASE_ENTITY`` / ``TREE_ENTITY`` 在 Java 里是
``String[]``，在 Python 里对应 ``List[str]``（顺序有意义：``initColumnField`` 只是
包含判断，顺序不影响结果，但保持原序便于逐行对照）。

``StringUtils.equalsAnyIgnoreCase(javaField, BASE_ENTITY...)`` 用的是**忽略大小写**
比较，Python 侧用 :func:`app.common.utils.string_utils.in_string_ignore_case`
（同样忽略大小写、且对候选做 ``trim``）。
"""

from __future__ import annotations

from typing import Final, List

# --------------------------------------------------------------------------- 模板类别

#: 单表（增删改查）
TPL_CRUD: Final[str] = "crud"
#: 树表（增删改查）
TPL_TREE: Final[str] = "tree"
#: 主子表（增删改查）
TPL_SUB: Final[str] = "sub"

# --------------------------------------------------------------------------- 树 / 菜单

#: 树编码字段
TREE_CODE: Final[str] = "treeCode"
#: 树父编码字段
TREE_PARENT_CODE: Final[str] = "treeParentCode"
#: 树名称字段
TREE_NAME: Final[str] = "treeName"
#: 上级菜单ID字段
PARENT_MENU_ID: Final[str] = "parentMenuId"
#: 上级菜单名称字段
PARENT_MENU_NAME: Final[str] = "parentMenuName"

# --------------------------------------------------------------------------- 数据库列类型

#: 数据库字符串类型
COLUMNTYPE_STR: Final[List[str]] = ["char", "varchar", "nvarchar", "varchar2"]
#: 数据库文本类型
COLUMNTYPE_TEXT: Final[List[str]] = ["tinytext", "text", "mediumtext", "longtext"]
#: 数据库时间类型
COLUMNTYPE_TIME: Final[List[str]] = ["datetime", "time", "date", "timestamp"]
#: 数据库数字类型
COLUMNTYPE_NUMBER: Final[List[str]] = [
    "tinyint",
    "smallint",
    "mediumint",
    "int",
    "number",
    "integer",
    "bit",
    "bigint",
    "float",
    "double",
    "decimal",
]

# --------------------------------------------------------------------------- 列名黑名单

#: 页面不需要编辑字段
COLUMNNAME_NOT_EDIT: Final[List[str]] = ["id", "create_by", "create_time", "del_flag"]
#: 页面不需要显示的列表字段
COLUMNNAME_NOT_LIST: Final[List[str]] = [
    "id",
    "create_by",
    "create_time",
    "del_flag",
    "update_by",
    "update_time",
]
#: 页面不需要查询字段
COLUMNNAME_NOT_QUERY: Final[List[str]] = [
    "id",
    "create_by",
    "create_time",
    "del_flag",
    "update_by",
    "update_time",
    "remark",
]

# --------------------------------------------------------------------------- 基类字段

#: Entity基类字段
BASE_ENTITY: Final[List[str]] = ["createBy", "createTime", "updateBy", "updateTime", "remark"]
#: Tree基类字段
TREE_ENTITY: Final[List[str]] = ["parentName", "parentId", "orderNum", "ancestors", "children"]

# --------------------------------------------------------------------------- 控件类型

#: 文本框
HTML_INPUT: Final[str] = "input"
#: 文本域
HTML_TEXTAREA: Final[str] = "textarea"
#: 下拉框
HTML_SELECT: Final[str] = "select"
#: 单选框
HTML_RADIO: Final[str] = "radio"
#: 复选框
HTML_CHECKBOX: Final[str] = "checkbox"
#: 日期控件
HTML_DATETIME: Final[str] = "datetime"
#: 图片上传控件
HTML_IMAGE_UPLOAD: Final[str] = "imageUpload"
#: 文件上传控件
HTML_FILE_UPLOAD: Final[str] = "fileUpload"
#: 富文本控件
HTML_EDITOR: Final[str] = "editor"

# --------------------------------------------------------------------------- Java 类型

#: 字符串类型
TYPE_STRING: Final[str] = "String"
#: 整型
TYPE_INTEGER: Final[str] = "Integer"
#: 长整型
TYPE_LONG: Final[str] = "Long"
#: 浮点型
TYPE_DOUBLE: Final[str] = "Double"
#: 高精度计算类型
TYPE_BIGDECIMAL: Final[str] = "BigDecimal"
#: 时间类型
TYPE_DATE: Final[str] = "Date"

# --------------------------------------------------------------------------- 查询方式

#: 模糊查询
QUERY_LIKE: Final[str] = "LIKE"
#: 相等查询
QUERY_EQ: Final[str] = "EQ"

#: 需要
REQUIRE: Final[str] = "1"


__all__ = [
    "TPL_CRUD",
    "TPL_TREE",
    "TPL_SUB",
    "TREE_CODE",
    "TREE_PARENT_CODE",
    "TREE_NAME",
    "PARENT_MENU_ID",
    "PARENT_MENU_NAME",
    "COLUMNTYPE_STR",
    "COLUMNTYPE_TEXT",
    "COLUMNTYPE_TIME",
    "COLUMNTYPE_NUMBER",
    "COLUMNNAME_NOT_EDIT",
    "COLUMNNAME_NOT_LIST",
    "COLUMNNAME_NOT_QUERY",
    "BASE_ENTITY",
    "TREE_ENTITY",
    "HTML_INPUT",
    "HTML_TEXTAREA",
    "HTML_SELECT",
    "HTML_RADIO",
    "HTML_CHECKBOX",
    "HTML_DATETIME",
    "HTML_IMAGE_UPLOAD",
    "HTML_FILE_UPLOAD",
    "HTML_EDITOR",
    "TYPE_STRING",
    "TYPE_INTEGER",
    "TYPE_LONG",
    "TYPE_DOUBLE",
    "TYPE_BIGDECIMAL",
    "TYPE_DATE",
    "QUERY_LIKE",
    "QUERY_EQ",
    "REQUIRE",
]
