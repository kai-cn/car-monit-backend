"""模板处理工具类.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityUtils.java

``prepareContext`` 往 :class:`~app.generator.util.velocity_engine.VelocityContext`
里塞 21~27 个变量，模板里所有 ``$xxx`` 都来自这里。缺一个变量不会报错 ——
Velocity 会把 ``$xxx`` 原样输出到生成的代码里，所以这份清单要和 Java 逐条对齐。

两个"顺序敏感"的地方
---------------------
1. ``importList`` 在 Java 里是 ``HashSet<String>``，``domain.java.vm`` 用
   ``#foreach ($import in $importList)`` 直接遍历。Java ``HashSet`` 的迭代顺序是
   **桶序**（容量 16 时按 ``spread(hash) & 15``），不是插入序 —— 于是生成出来的
   ``import`` 行顺序取决于字符串哈希。:class:`JavaHashSet` 复刻了这个顺序，
   否则同一张表在 Java/Python 两侧的 ``domain.java.vm`` 输出会差两行的位置。
2. ``getTemplateList`` 的模板顺序决定 ``previewCode`` 返回的 ``LinkedHashMap`` 键序，
   也就决定了 ``/tool/gen/preview/{tableId}`` 响应 JSON 的键序。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence

from app.common.constant.gen_constants import (
    BASE_ENTITY,
    PARENT_MENU_ID,
    TPL_CRUD,
    TPL_SUB,
    TPL_TREE,
    TREE_CODE,
    TREE_ENTITY,
    TREE_NAME,
    TREE_PARENT_CODE,
    TYPE_BIGDECIMAL,
    TYPE_DATE,
)
from app.common.utils.string_utils import (
    capitalize,
    format as string_format,
    in_string_ignore_case,
    is_empty,
    is_not_empty,
    is_not_null,
    substring,
    to_camel_case,
    convert_to_camel_case,
    uncapitalize,
)
from app.generator.domain.gen_table import GenTable
from app.generator.domain.gen_table_column import GenTableColumn
from app.generator.util.velocity_engine import VelocityContext

#: Java: ``private static final String PROJECT_PATH = "main/java"``
PROJECT_PATH = "main/java"
#: Java: ``private static final String MYBATIS_PATH = "main/resources/mapper"``
MYBATIS_PATH = "main/resources/mapper"
#: Java: ``private static final String DEFAULT_PARENT_MENU_ID = "3"``（系统工具）
DEFAULT_PARENT_MENU_ID = "3"

#: Java: ``StringUtils.EMPTY``
EMPTY = ""
#: Java: 功能名称为空时的占位符（注意是全角方括号）
DEFAULT_FUNCTION_NAME = "【请填写功能名称】"


# --------------------------------------------------------------------------- Java HashSet


def _java_string_hash(value: str) -> int:
    """Java: ``String.hashCode()`` —— 有符号 32 位."""
    result = 0
    for char in value:
        result = (result * 31 + ord(char)) & 0xFFFFFFFF
    return result - 0x100000000 if result >= 0x80000000 else result


def _spread(value: int) -> int:
    """Java 8: ``HashMap.hash(Object)`` —— ``h ^ (h >>> 16)``."""
    unsigned = value & 0xFFFFFFFF
    return (unsigned ^ (unsigned >> 16)) & 0xFFFFFFFF


class JavaHashSet:
    """``java.util.HashSet<String>`` 的**迭代顺序**.

    只覆盖本项目用到的规模：``getImportList`` 最多塞 4 个字符串，远低于
    ``HashSet`` 的扩容阈值（默认容量 16 × 0.75 = 12），所以容量恒为 16、桶内是
    链表（不会树化）。迭代顺序 = 桶下标从小到大，桶内按插入顺序。

    换成 Python ``set`` 会得到**另一个**顺序 —— 生成的 ``import`` 行就会换位置。
    """

    __slots__ = ("_items",)

    #: Java ``HashSet.DEFAULT_INITIAL_CAPACITY``
    CAPACITY = 16

    def __init__(self, items: Optional[Iterable[str]] = None) -> None:
        self._items: List[str] = []
        for item in items or ():
            self.add(item)

    def add(self, value: str) -> None:
        """Java: ``boolean add(E e)``."""
        if value not in self._items:
            self._items.append(value)

    def contains(self, value: str) -> bool:
        """Java: ``boolean contains(Object o)``."""
        return value in self._items

    def size(self) -> int:
        """Java: ``int size()``."""
        return len(self._items)

    def is_empty(self) -> bool:
        """Java: ``boolean isEmpty()``."""
        return not self._items

    def __iter__(self) -> Iterator[str]:
        buckets: Dict[int, List[str]] = {}
        for item in self._items:
            index = _spread(_java_string_hash(item)) & (self.CAPACITY - 1)
            buckets.setdefault(index, []).append(item)
        ordered: List[str] = []
        for index in range(self.CAPACITY):
            ordered.extend(buckets.get(index, ()))
        return iter(ordered)

    def to_list(self) -> List[str]:
        """按 Java 迭代顺序返回列表（测试与调试用）."""
        return list(iter(self))

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"JavaHashSet({self.to_list()!r})"


# --------------------------------------------------------------------------- 上下文


def prepare_context(gen_table: GenTable) -> VelocityContext:
    """Java: ``static VelocityContext prepareContext(GenTable genTable)``."""
    module_name = gen_table.module_name
    business_name = gen_table.business_name
    package_name = gen_table.package_name
    tpl_category = gen_table.tpl_category
    function_name = gen_table.function_name

    context = VelocityContext()
    context.put("tplCategory", gen_table.tpl_category)
    context.put("tableName", gen_table.table_name)
    context.put("functionName", function_name if is_not_empty(function_name) else DEFAULT_FUNCTION_NAME)
    context.put("ClassName", gen_table.class_name)
    context.put("className", uncapitalize(gen_table.class_name))
    context.put("moduleName", gen_table.module_name)
    context.put("BusinessName", capitalize(gen_table.business_name))
    context.put("businessName", gen_table.business_name)
    context.put("basePackage", get_package_prefix(package_name))
    context.put("packageName", package_name)
    context.put("author", gen_table.function_author)
    # Java: DateUtils.getDate() -> yyyy-MM-dd（不是时间戳，也不是 locale 格式）
    from app.common.utils.date_utils import get_date

    context.put("datetime", get_date())
    context.put("pkColumn", gen_table.pk_column)
    context.put("importList", get_import_list(gen_table))
    context.put("permissionPrefix", get_permission_prefix(module_name, business_name))
    context.put("columns", gen_table.columns)
    context.put("table", gen_table)
    context.put("dictionaryListKeySuffix", gen_table.dictionary_list_key_suffix)
    context.put("dictionaryInfoList", gen_table.dictionary_info_list)
    context.put("dictionaryInfoString", gen_table.dictionary_info_string)
    context.put("uploadInfo", gen_table.upload_info)
    context.put("richTextInfo", gen_table.rich_text_info)
    context.put("columnDialogInfo", gen_table.column_dialog_info)
    context.put("filterColumnList", gen_table.filter_column_list)
    set_menu_velocity_context(context, gen_table)
    if TPL_TREE == tpl_category:
        set_tree_velocity_context(context, gen_table)
    if TPL_SUB == tpl_category:
        set_sub_velocity_context(context, gen_table)
    return context


def set_menu_velocity_context(context: VelocityContext, gen_table: GenTable) -> None:
    """Java: ``static void setMenuVelocityContext(VelocityContext, GenTable)``."""
    params_obj = _parse_object(gen_table.options)
    context.put("parentMenuId", get_parent_menu_id(params_obj))


def set_tree_velocity_context(context: VelocityContext, gen_table: GenTable) -> None:
    """Java: ``static void setTreeVelocityContext(VelocityContext, GenTable)``."""
    params_obj = _parse_object(gen_table.options)
    context.put("treeCode", get_treecode(params_obj))
    context.put("treeParentCode", get_tree_parent_code(params_obj))
    context.put("treeName", get_tree_name(params_obj))
    context.put("expandColumn", get_expand_column(gen_table))
    assert params_obj is not None
    if TREE_PARENT_CODE in params_obj:
        context.put("tree_parent_code", params_obj[TREE_PARENT_CODE])
    if TREE_NAME in params_obj:
        context.put("tree_name", params_obj[TREE_NAME])


def set_sub_velocity_context(context: VelocityContext, gen_table: GenTable) -> None:
    """Java: ``static void setSubVelocityContext(VelocityContext, GenTable)``.

    ``gen_table.sub_table.class_name`` 直接解引用 —— 主子表但 ``subTableName`` 填错时
    Java 会 NPE，这里同样抛 ``AttributeError``（行为一致，不用 try 包起来）。
    """
    sub_table = gen_table.sub_table
    sub_table_name = gen_table.sub_table_name
    sub_table_fk_name = gen_table.sub_table_fk_name
    sub_class_name = gen_table.sub_table.class_name  # type: ignore[union-attr]
    sub_table_fk_class_name = convert_to_camel_case(sub_table_fk_name)

    context.put("subTable", sub_table)
    context.put("subTableName", sub_table_name)
    context.put("subTableFkName", sub_table_fk_name)
    context.put("subTableFkClassName", sub_table_fk_class_name)
    context.put("subTableFkclassName", uncapitalize(sub_table_fk_class_name))
    context.put("subClassName", sub_class_name)
    context.put("subclassName", uncapitalize(sub_class_name))
    context.put("subImportList", get_import_list(sub_table))  # type: ignore[arg-type]


# --------------------------------------------------------------------------- 模板与文件名


def get_template_list(tpl_category: Optional[str], is_mybatis_plus: bool) -> List[str]:
    """Java: ``static List<String> getTemplateList(String tplCategory, boolean isMybatisPlus)``.

    顺序即 ``previewCode`` 的返回键序，也与 ``downloadCode`` 的 zip 条目顺序一致。
    """
    vm = "vmplus" if is_mybatis_plus else "vm"
    templates: List[str] = [
        vm + "/java/domain.java.vm",
        vm + "/java/mapper.java.vm",
        vm + "/java/service.java.vm",
        vm + "/java/serviceImpl.java.vm",
        vm + "/java/controller.java.vm",
        vm + "/xml/mapper.xml.vm",
        vm + "/sql/sql.vm",
        vm + "/js/api.js.vm",
    ]
    if TPL_CRUD == tpl_category:
        templates.append(vm + "/vue/index.vue.vm")
        templates.append(vm + "/vue/index-form.vue.vm")
    elif TPL_TREE == tpl_category:
        templates.append(vm + "/vue/index-tree.vue.vm")
    elif TPL_SUB == tpl_category:
        templates.append(vm + "/vue/index.vue.vm")
        templates.append(vm + "/java/sub-domain.java.vm")
    return templates


def get_file_name(template: str, gen_table: GenTable) -> str:
    """Java: ``static String getFileName(String template, GenTable genTable)``.

    照抄了 Java 的 ``if ... if/else-if`` 结构：第一个 ``if`` 是独立的，
    ``sub-domain.java.vm`` 那一支才开启 ``else if`` 链。所以
    ``vm/java/domain.java.vm`` 命中第一个 ``if`` 之后，会继续往下走一连串
    ``else if``（都不命中），文件名保持不变。
    """
    file_name = ""
    package_name = gen_table.package_name
    module_name = gen_table.module_name
    class_name = gen_table.class_name
    business_name = gen_table.business_name

    java_path = PROJECT_PATH + "/" + _replace(package_name, ".", "/")
    mybatis_path = MYBATIS_PATH + "/" + str(module_name)
    vue_path = "vue"

    if "domain.java.vm" in template:
        file_name = string_format("{}/domain/{}.java", java_path, class_name)

    if "sub-domain.java.vm" in template and TPL_SUB == gen_table.tpl_category:
        file_name = string_format(
            "{}/domain/{}.java", java_path, gen_table.sub_table.class_name  # type: ignore[union-attr]
        )
    elif "mapper.java.vm" in template:
        file_name = string_format("{}/mapper/{}Mapper.java", java_path, class_name)
    elif "service.java.vm" in template:
        file_name = string_format("{}/service/I{}Service.java", java_path, class_name)
    elif "serviceImpl.java.vm" in template:
        file_name = string_format("{}/service/impl/{}ServiceImpl.java", java_path, class_name)
    elif "controller.java.vm" in template:
        file_name = string_format("{}/controller/{}Controller.java", java_path, class_name)
    elif "mapper.xml.vm" in template:
        file_name = string_format("{}/{}Mapper.xml", mybatis_path, class_name)
    elif "sql.vm" in template:
        file_name = str(business_name) + "Menu.sql"
    elif "api.js.vm" in template:
        file_name = string_format("{}/api/{}/{}.js", vue_path, module_name, business_name)
    elif "index.vue.vm" in template:
        file_name = string_format("{}/views/{}/{}/index.vue", vue_path, module_name, business_name)
    elif "index-form.vue.vm" in template:
        file_name = string_format(
            "{}/views/{}/{}/index-form.vue", vue_path, module_name, business_name
        )
    elif "index-tree.vue.vm" in template:
        file_name = string_format("{}/views/{}/{}/index.vue", vue_path, module_name, business_name)
    return file_name


def get_package_prefix(package_name: Optional[str]) -> str:
    """Java: ``static String getPackagePrefix(String packageName)``."""
    assert package_name is not None
    last_index = package_name.rfind(".")
    return substring(package_name, 0, last_index) or EMPTY


def get_import_list(gen_table: GenTable) -> JavaHashSet:
    """Java: ``static HashSet<String> getImportList(GenTable genTable)``."""
    columns = gen_table.columns or []
    sub_gen_table = gen_table.sub_table
    import_list = JavaHashSet()
    if is_not_null(sub_gen_table):
        import_list.add("java.util.List")
    for column in columns:
        # Java: !column.isSuperColumn() && TYPE_DATE.equals(column.getJavaType())
        if not column.is_super_column() and TYPE_DATE == column.java_type:
            import_list.add("java.util.Date")
            import_list.add("com.fasterxml.jackson.annotation.JsonFormat")
        elif not column.is_super_column() and TYPE_BIGDECIMAL == column.java_type:
            import_list.add("java.math.BigDecimal")
    return import_list


def get_permission_prefix(module_name: Optional[str], business_name: Optional[str]) -> Optional[str]:
    """Java: ``static String getPermissionPrefix(String moduleName, String businessName)``."""
    return string_format("{}:{}", module_name, business_name)


def get_parent_menu_id(params_obj: Optional[Dict[str, Any]]) -> str:
    """Java: ``static String getParentMenuId(JSONObject paramsObj)``."""
    if is_not_empty(params_obj) and PARENT_MENU_ID in (params_obj or {}):
        return str(params_obj[PARENT_MENU_ID])  # type: ignore[index]
    return DEFAULT_PARENT_MENU_ID


def get_treecode(params_obj: Optional[Dict[str, Any]]) -> str:
    """Java: ``static String getTreecode(JSONObject paramsObj)``."""
    if params_obj is not None and TREE_CODE in params_obj:
        return to_camel_case(params_obj[TREE_CODE]) or EMPTY
    return EMPTY


def get_tree_parent_code(params_obj: Optional[Dict[str, Any]]) -> str:
    """Java: ``static String getTreeParentCode(JSONObject paramsObj)``."""
    if params_obj is not None and TREE_PARENT_CODE in params_obj:
        return to_camel_case(params_obj[TREE_PARENT_CODE]) or EMPTY
    return EMPTY


def get_tree_name(params_obj: Optional[Dict[str, Any]]) -> str:
    """Java: ``static String getTreeName(JSONObject paramsObj)``."""
    if params_obj is not None and TREE_NAME in params_obj:
        return to_camel_case(params_obj[TREE_NAME]) or EMPTY
    return EMPTY


def get_expand_column(gen_table: GenTable) -> int:
    """Java: ``static int getExpandColumn(GenTable genTable)``.

    数到"列表列里第一个等于树名称字段"为止（含该列），返回计数。
    ``treeName`` 取不到时为 ``None``，于是 ``columnName == treeName`` 永远不成立，
    循环跑完所有列表列 —— 与 Java 的 ``columnName.equals(null) == false`` 一致。
    """
    params_obj = _parse_object(gen_table.options)
    tree_name = params_obj.get(TREE_NAME) if params_obj else None
    num = 0
    for column in gen_table.columns or []:
        if column.list:
            num += 1
            if column.column_name == tree_name:
                break
    return num


# --------------------------------------------------------------------------- 内部


def _replace(value: Optional[str], search: str, replacement: str) -> str:
    """Java: ``StringUtils.replace(String, String, String)``，null 视为空串."""
    if not value:
        return EMPTY
    return value.replace(search, replacement)


def _parse_object(options: Optional[str]) -> Optional[Dict[str, Any]]:
    """Java: ``JSONObject.parseObject(String)`` —— 空/空串返回 ``None``."""
    if is_empty(options):
        return None
    assert options is not None
    parsed = json.loads(options)
    return parsed if isinstance(parsed, dict) else None


__all__ = [
    "PROJECT_PATH",
    "MYBATIS_PATH",
    "DEFAULT_PARENT_MENU_ID",
    "DEFAULT_FUNCTION_NAME",
    "JavaHashSet",
    "prepare_context",
    "set_menu_velocity_context",
    "set_tree_velocity_context",
    "set_sub_velocity_context",
    "get_template_list",
    "get_file_name",
    "get_package_prefix",
    "get_import_list",
    "get_permission_prefix",
    "get_parent_menu_id",
    "get_treecode",
    "get_tree_parent_code",
    "get_tree_name",
    "get_expand_column",
]
