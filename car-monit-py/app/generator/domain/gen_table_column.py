"""代码生成业务字段表 gen_table_column.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenTableColumn.java

字段名与 JSON 键一一对应
------------------------
``@Data`` 风格的手写 getter/setter + Jackson 默认命名：字段 ``columnId`` ->
``columnId``，字段 ``isPk`` -> ``isPk``。Python 侧 ``is_pk`` 由
``alias_generator=to_camel`` 得到 ``isPk``，一致。

**Jackson 还会额外输出 10 个"派生属性"** —— 这一点最容易漏：

    ==============================  ==========================================
    派生 JSON 键                    Java 来源
    ==============================  ==========================================
    ``pk``                          ``boolean isPk()``
    ``increment``                   ``boolean isIncrement()``
    ``required``                    ``boolean isRequired()``
    ``insert``                      ``boolean isInsert()``
    ``edit``                        ``boolean isEdit()``
    ``list``                        ``boolean isList()``
    ``query``                       ``boolean isQuery()``
    ``superColumn``                 ``boolean isSuperColumn()``
    ``usableColumn``                ``boolean isUsableColumn()``
    ``capJavaField``                ``String getCapJavaField()``
    ==============================  ==========================================

``pk`` 与 ``isPk`` 同时存在并不冲突：Jackson 由 ``isPk()`` 得到 ``pk``、由
``getIsPk()`` 得到 ``isPk``，是两个不同的属性名。前端（``views/tool/gen/index.vue``）
正是按 ``pk`` / ``insert`` / ``edit`` / ``list`` / ``query`` / ``superColumn`` 这些
**布尔**键来决定列是否显示，所以这 10 个键必须照发。

``generateLinkTableFlag`` 的 getter 会在空值时返回 ``"0"``
----------------------------------------------------------
``getGenerateLinkTableFlag()`` 在字段为 ``null`` / 空白时返回 ``"0"``，于是 JSON 里
这个键永远是字符串（``"0"`` 或 ``"1"``），不会是 ``null``。用 ``field_serializer``
复刻。

方法名的处理
------------
Java 允许字段与无参方法同名（``isPk`` 字段 + ``isPk()`` 方法），Python 里字段占了
``is_pk``，所以无参判定方法改名为 ``is_primary_key()``；带参数的重载
（``isPk(String)``）统一收到 ``*_flag(value)`` 静态方法上。模板只用到
``pk``/``insert``/``edit``/``list``/``query``/``superColumn``/``usableColumn`` 这几个
**派生属性**和 ``readConverterExp()``，改名不影响渲染结果。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import computed_field, field_serializer

from app.common.core.domain.base_entity import BaseEntity
from app.common.utils.bean_validation import Constraint, NotBlank
from app.common.utils.string_utils import capitalize, in_string_ignore_case, is_empty, substring_between

if False:  # pragma: no cover - 只给类型检查器看
    from app.generator.domain.gen_table import GenTable
    from app.generator.domain.link_table_field import LinkTableField

#: Java: ``isSuperColumn(String)`` 的白名单 —— BaseEntity + TreeEntity 字段.
_SUPER_COLUMN_NAMES = (
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "parentName",
    "parentId",
    "orderNum",
    "ancestors",
)

#: Java: ``isUsableColumn(String)`` 的白名单.
_USABLE_COLUMN_NAMES = ("parentId", "orderNum", "remark")


class GenTableColumn(BaseEntity):
    """Java: ``com.ruoyi.generator.domain.GenTableColumn``."""

    #: 编号
    column_id: Optional[int] = None
    #: 归属表编号
    table_id: Optional[int] = None
    #: 列名称
    column_name: Optional[str] = None
    #: 列描述
    column_comment: Optional[str] = None
    #: 列类型
    column_type: Optional[str] = None
    #: JAVA类型
    java_type: Optional[str] = None
    #: JAVA字段名（``@NotBlank(message = "Java属性不能为空")``）
    java_field: Optional[str] = None
    #: 是否主键（1是）
    is_pk: Optional[str] = None
    #: 是否自增（1是）
    is_increment: Optional[str] = None
    #: 是否必填（1是）
    is_required: Optional[str] = None
    #: 是否为插入字段（1是）
    is_insert: Optional[str] = None
    #: 是否编辑字段（1是）
    is_edit: Optional[str] = None
    #: 是否列表字段（1是）
    is_list: Optional[str] = None
    #: 是否查询字段（1是）
    is_query: Optional[str] = None
    #: 查询方式（EQ等于、NE不等于、GT大于、LT小于、LIKE模糊、BETWEEN范围）
    query_type: Optional[str] = None
    #: 显示类型（input/textarea/select/checkbox/radio/datetime/imageUpload/fileUpload/editor）
    html_type: Optional[str] = None
    #: 字典类型, 里面保存字典的key
    dict_type: Optional[str] = None
    #: 字典类型-驼峰
    dict_type_camel_case: Optional[str] = None
    #: 排序
    sort: Optional[int] = None
    #: 是否生成关联表信息 "0" => 不生成, "1" => 生成
    generate_link_table_flag: Optional[str] = None
    #: 关联表id
    link_table_id: Optional[int] = None
    #: 关联表信息
    link_table: Optional["GenTable"] = None
    #: 是否生成 单选 Dialog  0 => 不生成, 1 => 生成
    single_selection: Optional[str] = None
    #: 是否生成 多选 Dialog  0 => 不生成, 1 => 生成
    multiple_selections: Optional[str] = None
    #: dialog 搜索字段ids, 多个使用逗号拼接
    dialog_search_column_ids: Optional[str] = None
    #: dialog 列表字段ids, 多个使用逗号拼接
    dialog_list_column_ids: Optional[str] = None
    #: dialog 搜索字段列表
    dialog_search_column_list: Optional[List["GenTableColumn"]] = None
    #: dialog 展示字段列表
    dialog_show_column_list: Optional[List["GenTableColumn"]] = None
    #: dialog 搜索字段名称, 多个使用逗号拼接
    dialog_search_column_names: Optional[str] = None
    #: dialog 列表字段名称, 多个使用逗号拼接
    dialog_list_column_names: Optional[str] = None
    #: 字段映射, json数组
    field_map_string: Optional[str] = None
    #: 表字段列表
    table_field_list: Optional[List["LinkTableField"]] = None
    #: 自定义字段列表
    custom_field_list: Optional[List["LinkTableField"]] = None
    #: 主要的映射关系
    major_link_field_info: Optional["LinkTableField"] = None

    # ------------------------------------------------------------------ 派生属性

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cap_java_field(self) -> Optional[str]:
        """Java: ``getCapJavaField()`` -> ``StringUtils.capitalize(javaField)``."""
        return capitalize(self.java_field)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pk(self) -> bool:
        """Java: ``isPk()``."""
        return self.is_primary_key()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def increment(self) -> bool:
        """Java: ``isIncrement()``."""
        return _is_one(self.is_increment)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def required(self) -> bool:
        """Java: ``isRequired()``."""
        return _is_one(self.is_required)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def insert(self) -> bool:
        """Java: ``isInsert()``."""
        return _is_one(self.is_insert)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def edit(self) -> bool:
        """Java: ``isEdit()`` —— 注意 Java 原实现调用的是 ``isInsert(this.isEdit)``.

        也就是说 ``edit`` 的判定**复用了 insert 的判断函数**，只是传入
        ``this.isEdit``。两者实现恰好相同（都是 ``"1".equals(x) && x != null``），
        所以结果一致；这里仍然分开写清楚，避免把"看起来像笔误"的地方悄悄改掉。
        """
        return _is_one(self.is_edit)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def list(self) -> bool:
        """Java: ``isList()``."""
        return _is_one(self.is_list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def query(self) -> bool:
        """Java: ``isQuery()``."""
        return _is_one(self.is_query)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def super_column(self) -> bool:
        """Java: ``isSuperColumn()``（无参重载）."""
        return self.is_super_column_name(self.java_field)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def usable_column(self) -> bool:
        """Java: ``isUsableColumn()``（无参重载）."""
        return self.is_usable_column_name(self.java_field)

    # ------------------------------------------------------------------ 业务方法

    def is_primary_key(self) -> bool:
        """Java: ``boolean isPk()`` —— 无参重载（字段名被 Python 占用，故改名）."""
        return _is_one(self.is_pk)

    def is_primary_key_flag(self, value: Optional[str]) -> bool:
        """Java: ``boolean isPk(String isPk)`` —— 带参重载."""
        return _is_one(value)

    def is_super_column(self) -> bool:
        """Java: ``boolean isSuperColumn()`` —— 无参重载."""
        return self.is_super_column_name(self.java_field)

    @staticmethod
    def is_super_column_name(java_field: Optional[str]) -> bool:
        """Java: ``static boolean isSuperColumn(String javaField)``."""
        return in_string_ignore_case(java_field, *_SUPER_COLUMN_NAMES)

    def is_usable_column(self) -> bool:
        """Java: ``boolean isUsableColumn()`` —— 无参重载."""
        return self.is_usable_column_name(self.java_field)

    @staticmethod
    def is_usable_column_name(java_field: Optional[str]) -> bool:
        """Java: ``static boolean isUsableColumn(String javaField)``."""
        return in_string_ignore_case(java_field, *_USABLE_COLUMN_NAMES)

    def read_converter_exp(self) -> Optional[str]:
        """Java: ``String readConverterExp()``.

        从列注释里 ``（...）`` 中按**空格**切出若干 ``1=男`` 形式的映射；取不到括号
        内容时**直接返回整段注释**。三个照抄点：

        * ``StringUtils.isNotEmpty(remarks)`` 在 RuoYi 里会 ``trim``，所以
          ``"（）"``（括号内全是空格）走 else 分支，返回原始注释；
        * 每个 token 取首个字符做 key、其余做 value，**不校验**长度；
        * 结尾用 ``deleteCharAt(len-1)`` 去掉最后一个逗号。
        """
        remarks = substring_between(self.column_comment, "（", "）")
        if is_empty(remarks):
            return self.column_comment
        assert remarks is not None
        buffer: List[str] = []
        for value in _java_split_space(remarks):
            if is_empty(value):
                continue
            buffer.append(f"{value[0]}={value[1:]},")
        if not buffer:
            # Java: sb 为空时 deleteCharAt(-1) 会抛 StringIndexOutOfBoundsException。
            # 只有在 remarks 非空但全是空格时才会到这里，而 isEmpty 已经挡掉，
            # 所以这段是防御性代码，不会在正常输入下执行。
            return self.column_comment
        return "".join(buffer)[:-1]

    # ------------------------------------------------------------------ 序列化

    @field_serializer("generate_link_table_flag")
    def _serialize_generate_link_table_flag(self, value: Optional[str]) -> str:
        """Java: ``getGenerateLinkTableFlag()`` —— 空值返回 ``"0"``."""
        if is_empty(value):
            return "0"
        assert value is not None
        return value


def _is_one(value: Optional[str]) -> bool:
    """Java: ``isPk != null && StringUtils.equals("1", isPk)``."""
    return value is not None and value == "1"


def _java_split_space(value: str) -> List[str]:
    """Java: ``value.split(" ")`` —— 保留中间空串、**丢弃尾部空串**."""
    parts = value.split(" ")
    while parts and parts[-1] == "":
        parts.pop()
    return parts


#: Java ``GenTableColumn`` 上唯一的校验注解：
#: ``@NotBlank(message = "Java属性不能为空") private String javaField;``
#: 它通过 ``GenTable.columns`` 上的 ``@Valid`` **级联**生效，所以
#: ``PUT /tool/gen`` 里任意一列 ``javaField`` 为空都会拒掉整个请求。
GEN_TABLE_COLUMN_CONSTRAINTS: Tuple[Constraint, ...] = (
    NotBlank("java_field", "Java属性不能为空"),
)


__all__ = ["GenTableColumn", "GEN_TABLE_COLUMN_CONSTRAINTS"]
