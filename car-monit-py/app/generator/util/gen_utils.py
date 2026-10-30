"""代码生成器 工具类.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/util/GenUtils.java

两个函数：
* :func:`init_table` —— 导入数据库表时按 ``generator.yml`` 的偏好回填类名/包名/业务名；
* :func:`init_column_field` —— 按列类型与列名后缀推断 ``javaType`` / ``htmlType`` /
  ``queryType``，并决定 ``is_insert`` / ``is_edit`` / ``is_list`` / ``is_query``。

``init_column_field`` 的结果会**落库**（``gen_table_column`` 的 9 个字段），也会
直接出现在 ``/tool/gen/column/{tableId}`` 的响应里，所以每一条推断规则都必须照抄，
包括那些看起来不够聪明的分支：

* ``javaType`` 先置成 ``String`` 再在数字分支里覆盖 —— 于是 ``bit`` 之类会走到
  ``Long`` 而不是 ``Boolean``；
* ``decimal(10)``（1 段）→ ``Integer``、``decimal(10,0)``（2 段但小数为 0）→ 落到
  ``else`` → ``Long``；
* 后缀判断是 ``else if`` 链，``xxx_status`` 只会变成 ``radio``，不会同时变成 ``select``。
"""

from __future__ import annotations

import re
from typing import List, Optional, Sequence

from app.common.constant.gen_constants import (
    COLUMNNAME_NOT_EDIT,
    COLUMNNAME_NOT_LIST,
    COLUMNNAME_NOT_QUERY,
    COLUMNTYPE_NUMBER,
    COLUMNTYPE_STR,
    COLUMNTYPE_TEXT,
    COLUMNTYPE_TIME,
    HTML_DATETIME,
    HTML_EDITOR,
    HTML_FILE_UPLOAD,
    HTML_IMAGE_UPLOAD,
    HTML_INPUT,
    HTML_RADIO,
    HTML_SELECT,
    HTML_TEXTAREA,
    QUERY_LIKE,
    REQUIRE,
    TYPE_BIGDECIMAL,
    TYPE_DATE,
    TYPE_INTEGER,
    TYPE_LONG,
    TYPE_STRING,
)
from app.common.utils.string_utils import (
    convert_to_camel_case,
    ends_with_ignore_case,
    is_empty,
    is_not_empty,
    split,
    substring,
    substring_before,
    substring_between,
    to_camel_case,
)
from app.generator.config.gen_config import GenConfig
from app.generator.domain.gen_table import GenTable
from app.generator.domain.gen_table_column import GenTableColumn

#: Java: ``RegExUtils.replaceAll(text, "(?:表|若依)", "")``
_FUNCTION_NAME_NOISE = re.compile("(?:表|若依)")


def init_table(gen_table: GenTable, oper_name: Optional[str]) -> None:
    """Java: ``static void initTable(GenTable genTable, String operName)``."""
    gen_table.class_name = convert_class_name(gen_table.table_name)
    gen_table.package_name = GenConfig.get_package_name()
    gen_table.module_name = get_module_name(GenConfig.get_package_name())
    gen_table.business_name = get_business_name(gen_table.table_name)
    gen_table.function_name = replace_text(gen_table.table_comment)
    gen_table.function_author = GenConfig.get_author()
    gen_table.create_by = oper_name


def init_column_field(column: GenTableColumn, table: GenTable) -> None:
    """Java: ``static void initColumnField(GenTableColumn column, GenTable table)``."""
    data_type = get_db_type(column.column_type)
    column_name = column.column_name
    column.table_id = table.table_id
    column.create_by = table.create_by
    # 设置java字段名
    column.java_field = to_camel_case(column_name)
    # 设置默认类型
    column.java_type = TYPE_STRING

    if arrays_contains(COLUMNTYPE_STR, data_type) or arrays_contains(COLUMNTYPE_TEXT, data_type):
        # 字符串长度超过500设置为文本域
        column_length = get_column_length(column.column_type)
        column.html_type = (
            HTML_TEXTAREA
            if column_length >= 500 or arrays_contains(COLUMNTYPE_TEXT, data_type)
            else HTML_INPUT
        )
    elif arrays_contains(COLUMNTYPE_TIME, data_type):
        column.java_type = TYPE_DATE
        column.html_type = HTML_DATETIME
    elif arrays_contains(COLUMNTYPE_NUMBER, data_type):
        column.html_type = HTML_INPUT

        # 如果是浮点型 统一用BigDecimal
        # Java: StringUtils.split(substringBetween(columnType, "(", ")"), ",")
        str_array = split(substring_between(column.column_type, "(", ")"), ",")
        if str_array is not None and len(str_array) == 2 and int(str_array[1]) > 0:
            column.java_type = TYPE_BIGDECIMAL
        # 如果是整形
        elif str_array is not None and len(str_array) == 1 and int(str_array[0]) <= 10:
            column.java_type = TYPE_INTEGER
        # 长整形
        else:
            column.java_type = TYPE_LONG

    # 插入字段（默认所有字段都需要插入）
    column.is_insert = REQUIRE

    # 编辑字段
    if not arrays_contains(COLUMNNAME_NOT_EDIT, column_name) and not column.is_primary_key():
        column.is_edit = REQUIRE
    # 列表字段
    if not arrays_contains(COLUMNNAME_NOT_LIST, column_name) and not column.is_primary_key():
        column.is_list = REQUIRE
    # 查询字段
    if not arrays_contains(COLUMNNAME_NOT_QUERY, column_name) and not column.is_primary_key():
        column.is_query = REQUIRE

    # 查询字段类型
    if ends_with_ignore_case(column_name, "name"):
        column.query_type = QUERY_LIKE
    # 状态字段设置单选框
    if ends_with_ignore_case(column_name, "status"):
        column.html_type = HTML_RADIO
    # 类型&性别字段设置下拉框
    elif ends_with_ignore_case(column_name, "type") or ends_with_ignore_case(column_name, "sex"):
        column.html_type = HTML_SELECT
    # 图片字段设置图片上传控件
    elif ends_with_ignore_case(column_name, "image"):
        column.html_type = HTML_IMAGE_UPLOAD
    # 文件字段设置文件上传控件
    elif ends_with_ignore_case(column_name, "file"):
        column.html_type = HTML_FILE_UPLOAD
    # 内容字段设置富文本控件
    elif ends_with_ignore_case(column_name, "content"):
        column.html_type = HTML_EDITOR


def arrays_contains(array: Optional[Sequence[str]], target_value: Optional[str]) -> bool:
    """Java: ``static boolean arraysContains(String[] arr, String targetValue)``.

    Java 走 ``Arrays.asList(arr).contains(...)`` —— **大小写敏感**、不做 trim。
    ``data_type`` 来自 ``get_db_type``，MySQL 里恒为小写，所以这里不需要额外兼容。
    """
    if array is None:
        return False
    return target_value in array


def get_module_name(package_name: Optional[str]) -> Optional[str]:
    """Java: ``static String getModuleName(String packageName)``.

    ``com.ruoyi.manager`` -> ``manager``；没有点号时 ``lastIndexOf`` 返回 -1，
    ``substring(packageName, 0, length)`` 返回原串。
    """
    assert package_name is not None
    last_index = package_name.rfind(".")
    return substring(package_name, last_index + 1, len(package_name))


def get_business_name(table_name: Optional[str]) -> Optional[str]:
    """Java: ``static String getBusinessName(String tableName)``.

    ``sys_user`` -> ``user``；无下划线时返回原串。
    """
    assert table_name is not None
    last_index = table_name.rfind("_")
    return substring(table_name, last_index + 1, len(table_name))


def convert_class_name(table_name: Optional[str]) -> str:
    """Java: ``static String convertClassName(String tableName)``."""
    auto_remove_pre = GenConfig.get_auto_remove_pre()
    table_prefix = GenConfig.get_table_prefix()
    if auto_remove_pre and is_not_empty(table_prefix):
        search_list = split(table_prefix, ",")
        table_name = replace_first(table_name, search_list or [])
    assert table_name is not None
    return convert_to_camel_case(table_name)


def replace_first(replacement: Optional[str], search_list: Sequence[str]) -> Optional[str]:
    """Java: ``static String replaceFirst(String replacementm, String[] searchList)``.

    命中前缀后调的是 ``String.replaceFirst(searchString, "")`` —— 也就是把
    ``searchString`` 当**正则**用。``sys_`` 没有元字符，效果与字面量替换相同；
    照抄正则语义以保持一致（若有人把 ``tablePrefix`` 配成 ``sys_.*_``，两侧行为仍一致）。
    """
    text = replacement
    if replacement is None:
        return None
    for search_string in search_list:
        if replacement.startswith(search_string):
            text = re.sub(search_string, "", replacement, count=1)
            break
    return text


def replace_text(text: Optional[str]) -> Optional[str]:
    """Java: ``static String replaceText(String text)`` —— 去掉"表"/"若依"两个字."""
    if text is None:
        return None
    return _FUNCTION_NAME_NOISE.sub("", text)


def get_db_type(column_type: Optional[str]) -> Optional[str]:
    """Java: ``static String getDbType(String columnType)``.

    ``varchar(64)`` -> ``varchar``；``text``（无括号）原样返回。
    注意判据是 ``indexOf("(") > 0`` —— 括号恰好在第 0 位时不截断。
    """
    if column_type is None:
        return None
    if column_type.find("(") > 0:
        return substring_before(column_type, "(")
    return column_type


def get_column_length(column_type: Optional[str]) -> int:
    """Java: ``static Integer getColumnLength(String columnType)``.

    ``varchar(500)`` -> 500；无括号 -> 0。``decimal(10,2)`` 会抛
    ``NumberFormatException``（Java 一样），但只有 ``COLUMNTYPE_STR/TEXT`` 分支会调它，
    所以实际不会碰到。
    """
    if column_type is None:
        return 0
    if column_type.find("(") > 0:
        length = substring_between(column_type, "(", ")")
        return int(length)  # type: ignore[arg-type]
    return 0


__all__ = [
    "init_table",
    "init_column_field",
    "arrays_contains",
    "get_module_name",
    "get_business_name",
    "convert_class_name",
    "replace_first",
    "replace_text",
    "get_db_type",
    "get_column_length",
]
