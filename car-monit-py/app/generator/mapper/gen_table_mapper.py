"""代码生成业务表 mapper.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableMapper.java
# Migrated from: ruoyi-generator/src/main/resources/mapper/generator/GenTableMapper.xml

XML 里共 10 条 statement，接口声明 9 个方法 —— 多出来的那条
``<select id="selectTableByName">``（按 ``table_comment <> ''`` 过滤表名）在
``GenTableMapper.java`` 里**没有对应方法**，Java 侧永远走不到。按迁移原则第 4 条
照留成 :data:`_SELECT_TABLE_BY_NAME`，但不能登记成 mapper 方法（否则会多出一条
Python 独有的行为）。注意它和 ``selectGenTableByName`` 完全不是一回事：前者查
``information_schema.tables``（数据库里真实存在的表），后者查 ``gen_table``。

三条"带列"的语句各自的投影**并不一致**
---------------------------------------
``selectGenTableById`` / ``selectGenTableByName`` 投影 ``t.`` 的 **16** 列（没有
``create_by`` / ``create_time`` / ``update_by`` / ``update_time``），
``selectGenTableAll`` 只投影 **14** 列（连 ``gen_type`` / ``gen_path`` 也没有）。
少掉的列在 Java 里就是 ``null``，前端「生成配置」弹窗按 id 取详情时
``createTime`` 是 ``null`` 而不是创建时间 —— 这是本项目现存行为，照抄。

``selectGenTableList`` 的 ``<collection>`` 拿不到任何列
------------------------------------------------------
``resultMap="GenTableResult"`` 里挂了
``<collection property="columns" resultMap="GenTableColumnResult"/>``，但
``selectGenTableList`` 只 ``<include refid="selectGenTableVo"/>``（单表、无 join），
一列 ``c.*`` 都没有。MyBatis 的 ``applyNestedResultMappings`` 逐列比对
``mappedColumnNames``（ResultSet 里真实存在的列名），一列都对不上就**根本不去构造**
嵌套对象，``foundValues`` 恒为 false → ``columns`` 属性**从头到尾没被赋值**，停在
``GenTable`` 的字段初值 ``null``。所以列表接口的每行都是 ``"columns": null``。

注意这跟"空集合"是两回事：``null`` / ``[]`` 在 JSON 里不同，所以这里**不能**"顺手
补成空列表"—— ``_map_gen_table`` 不碰 ``columns`` 就是为了让默认值 ``None`` 露出去。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.generator.domain.gen_table import GenTable
from app.generator.domain.gen_table_column import GenTableColumn
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from GenTableMapper.xml -> ``<sql id="selectGenTableVo">``.
#: 20 列，顺序即 ``GenTableResult`` 的 ``<result>`` 声明顺序。
SELECT_GEN_TABLE_VO = """select table_id, table_name, table_comment, sub_table_name, sub_table_fk_name, class_name, tpl_category, package_name, module_name, business_name, function_name, function_author, gen_type, gen_path, options, create_by, create_time, update_by, update_time, remark from gen_table"""

#: ``selectGenTableVo`` 投影的列 -> ``GenTable`` 属性。列名与属性名在 snake_case 下同形，
#: 保留这张表是为了和 XML 的 ``<resultMap>`` 一一对上，避免"少映射一个字段"。
_GEN_TABLE_COLUMNS: Tuple[str, ...] = (
    "table_id",
    "table_name",
    "table_comment",
    "sub_table_name",
    "sub_table_fk_name",
    "class_name",
    "tpl_category",
    "package_name",
    "module_name",
    "business_name",
    "function_name",
    "function_author",
    "gen_type",
    "gen_path",
    "options",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "remark",
)

#: ``selectGenTableById`` / ``selectGenTableByName`` 的 ``t.`` 投影（16 列）。
#: **没有**四个审计列 —— 见模块 docstring。
_JOIN_TABLE_COLUMNS: Tuple[str, ...] = (
    "table_id",
    "table_name",
    "table_comment",
    "sub_table_name",
    "sub_table_fk_name",
    "class_name",
    "tpl_category",
    "package_name",
    "module_name",
    "business_name",
    "function_name",
    "function_author",
    "gen_type",
    "gen_path",
    "options",
    "remark",
)

#: ``selectGenTableAll`` 的 ``t.`` 投影（14 列，比上面再少 ``gen_type`` / ``gen_path``）。
_ALL_TABLE_COLUMNS: Tuple[str, ...] = (
    "table_id",
    "table_name",
    "table_comment",
    "sub_table_name",
    "sub_table_fk_name",
    "class_name",
    "tpl_category",
    "package_name",
    "module_name",
    "business_name",
    "function_name",
    "function_author",
    "options",
    "remark",
)

#: join 语句里 ``c.`` 的投影（23 列）。**没有** ``table_id``，也**没有**四个审计列。
_JOIN_COLUMN_COLUMNS: Tuple[str, ...] = (
    "column_id",
    "column_name",
    "column_comment",
    "column_type",
    "java_type",
    "java_field",
    "is_pk",
    "is_increment",
    "is_required",
    "is_insert",
    "is_edit",
    "is_list",
    "is_query",
    "query_type",
    "html_type",
    "dict_type",
    "field_map_string",
    "link_table_id",
    "single_selection",
    "multiple_selections",
    "dialog_search_column_ids",
    "dialog_list_column_ids",
    "sort",
)

#: ``selectDbTableList`` / ``selectDbTableListByNames`` / ``selectTableByName``
#: 从 ``information_schema.tables`` 取的 4 列。
_INFO_SCHEMA_COLUMNS: Tuple[str, ...] = (
    "table_name",
    "table_comment",
    "create_time",
    "update_time",
)

#: Verbatim from ``<select id="selectDbTableList">`` 的固定部分（``<if>`` 之外）。
_DB_TABLE_LIST_HEAD = """select table_name, table_comment, create_time, update_time from information_schema.tables
		where table_schema = (select database())
		AND table_name NOT LIKE 'qrtz_%' AND table_name NOT LIKE 'gen_%'
		AND table_name NOT IN (select table_name from gen_table)"""

#: Verbatim from ``<select id="selectDbTableListByNames">`` 的固定部分。
_DB_TABLE_LIST_BY_NAMES_HEAD = """select table_name, table_comment, create_time, update_time from information_schema.tables
		where table_name NOT LIKE 'qrtz_%' and table_name NOT LIKE 'gen_%' and table_schema = (select database())
		and table_name in"""

#: Verbatim from ``<select id="selectTableByName">`` —— **孤儿语句**，接口里没有对应方法。
_SELECT_TABLE_BY_NAME = """select table_name, table_comment, create_time, update_time from information_schema.tables
		where table_comment <> '' and table_schema = (select database())
		and table_name = :table_name"""

#: ``insertGenTable`` 的动态列，顺序与 XML 一致；第三项是"是否要求非空串"。
#: ``table_name`` 只有 ``!= null``（XML 第 149 行），其余都是 ``!= null and != ''``。
_INSERT_GEN_TABLE_COLUMNS: Tuple[Tuple[str, bool], ...] = (
    ("table_name", False),
    ("table_comment", True),
    ("class_name", True),
    ("tpl_category", True),
    ("package_name", True),
    ("module_name", True),
    ("business_name", True),
    ("function_name", True),
    ("function_author", True),
    ("gen_type", True),
    ("gen_path", True),
    ("remark", True),
    ("create_by", True),
)

#: ``updateGenTable`` 的 ``<set>`` 分支，顺序与 XML 一致。
#: ``table_name`` / ``sub_table_name`` / ``sub_table_fk_name`` / ``remark`` 只判 ``!= null``；
#: 其余为 ``!= null and != ''``。
_UPDATE_GEN_TABLE_COLUMNS: Tuple[Tuple[str, bool], ...] = (
    ("table_name", False),
    ("table_comment", True),
    ("sub_table_name", False),
    ("sub_table_fk_name", False),
    ("class_name", True),
    ("function_author", True),
    ("gen_type", True),
    ("gen_path", True),
    ("tpl_category", True),
    ("package_name", True),
    ("module_name", True),
    ("business_name", True),
    ("function_name", True),
    ("options", True),
    ("update_by", True),
    ("remark", False),
)


class GenTableMapper:
    """Java: ``interface GenTableMapper``."""

    # Java: List<GenTable> selectGenTableList(GenTable genTable)
    def select_gen_table_list(self, gen_table: GenTable) -> List[GenTable]:
        """代码生成表列表（``startPage()`` 之后的第一条 select，分页点在这里）。

        ``order by create_time DESC`` 是 XML 里写死的，PageHelper 检测到已有
        ``order by`` 就不追加前端传来的 ``orderByColumn`` —— 与
        ``sys_config`` 那批"无排序"的列表不同。
        """
        data_sql, params = _build_list_sql(gen_table)
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_gen_table(row, list(_GEN_TABLE_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: List<GenTable> selectDbTableList(GenTable genTable)
    def select_db_table_list(self, gen_table: GenTable) -> List[GenTable]:
        """数据库里**尚未导入**的表（``gen_table`` 已有的被 ``NOT IN`` 排除）。

        XML 这条语句**没有** ``order by``，所以 PageHelper 会把前端
        ``orderByColumn`` / ``isAsc`` 追加进来（``gen/index.vue`` 的表头排序依赖它）。
        """
        sql, params = _build_db_table_list_sql(gen_table)
        count_sql = f"select count(0) from ({sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, sql, params, page)
        mapped = [_map_gen_table(row, list(_INFO_SCHEMA_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: List<GenTable> selectDbTableListByNames(String[] tableNames)
    def select_db_table_list_by_names(self, table_names: Sequence[str]) -> List[GenTable]:
        """按表名批量取（``/tool/gen/importTable`` 用）。

        ``<foreach open="(" separator="," close=")">``：空数组会拼出 ``in ()``，
        MySQL 报语法错 —— Java 侧同样如此，不额外兜底。
        """
        # 直接拼括号列表，不走 ``_in_clause`` —— 那条 helper 面向 ``列 in (...)``，
        # 这里的 ``column`` 是空的，借用它的内部格式只会让代码更难读。
        placeholders = "(" + ", ".join(f":name{index}" for index in range(len(table_names))) + ")"
        params: Dict[str, Any] = {
            f"name{index}": value for index, value in enumerate(table_names)
        }
        sql = _DB_TABLE_LIST_BY_NAMES_HEAD + " " + placeholders
        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.all()
        return [_map_gen_table(row, list(_INFO_SCHEMA_COLUMNS), keys) for row in rows]

    # Java: List<GenTable> selectGenTableAll()
    def select_gen_table_all(self) -> List[GenTable]:
        """全部代码生成表（含列），``order by c.sort`` 且**没有 where**。

        投影缺 ``gen_type`` / ``gen_path``，见模块 docstring。
        """
        sql, _ = _build_join_sql(_ALL_TABLE_COLUMNS, _JOIN_COLUMN_COLUMNS, None, None)
        with session_scope() as session:
            result = session.execute(text(sql))
            keys = list(result.keys())
            rows = result.all()
        return _group_joined_rows(rows, keys, _ALL_TABLE_COLUMNS)

    # Java: GenTable selectGenTableById(Long id)
    def select_gen_table_by_id(self, table_id: Optional[int]) -> Optional[GenTable]:
        sql, params = _build_join_sql(
            _JOIN_TABLE_COLUMNS, _JOIN_COLUMN_COLUMNS, "t.table_id = :table_id", {"table_id": table_id}
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.all()
        tables = _group_joined_rows(rows, keys, _JOIN_TABLE_COLUMNS)
        # ``selectOne`` 语义：无行 -> None。table_id 是主键，不可能多行。
        return tables[0] if tables else None

    # Java: GenTable selectGenTableByName(String tableName)
    def select_gen_table_by_name(self, table_name: Optional[str]) -> Optional[GenTable]:
        sql, params = _build_join_sql(
            _JOIN_TABLE_COLUMNS,
            _JOIN_COLUMN_COLUMNS,
            "t.table_name = :table_name",
            {"table_name": table_name},
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.all()
        tables = _group_joined_rows(rows, keys, _JOIN_TABLE_COLUMNS)
        if len(tables) > 1:
            # Java: selectOne 遇到多行抛 TooManyResultsException -> 500
            raise LookupError("selectGenTableByName 返回了多行")
        return tables[0] if tables else None

    # Java: int insertGenTable(GenTable genTable)
    def insert_gen_table(self, gen_table: GenTable) -> int:
        """动态列插入，``useGeneratedKeys`` 回写 ``table_id``。"""
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute, require_text in _INSERT_GEN_TABLE_COLUMNS:
            value = getattr(gen_table, attribute)
            if value is None:
                continue
            if require_text and value == "":
                continue
            columns.append(attribute)
            names.append(f":{attribute}")
            params[attribute] = value

        # XML 里 ``create_time`` 无条件写 ``sysdate()``
        columns.append("create_time")
        names.append("sysdate()")

        sql = f"insert into gen_table ({','.join(columns)}) values ({','.join(names)})"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            # Java: useGeneratedKeys="true" keyProperty="tableId"
            if getattr(result, "lastrowid", None):
                gen_table.table_id = int(result.lastrowid)
            return result.rowcount or 0

    # Java: int updateGenTable(GenTable genTable)
    def update_gen_table(self, gen_table: GenTable) -> int:
        sql, params = _build_update_sql(gen_table)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteGenTableByIds(Long[] ids)
    def delete_gen_table_by_ids(self, table_ids: Sequence[int]) -> int:
        """``<foreach collection="array">`` —— 空数组拼出 ``in ()``（Java 同样语法错）。"""
        clause, params = _in_clause("table_id", table_ids, "p")
        with session_scope() as session:
            return (
                session.execute(text(f"delete from gen_table where {clause}"), params).rowcount or 0
            )


# --------------------------------------------------------------------------- SQL 片段


def _build_list_sql(gen_table: GenTable) -> Tuple[str, Dict[str, Any]]:
    """``selectGenTableList`` 的 ``<where>`` + 写死的 ``ORDER BY``。

    条件判据是 OGNL 的 ``x != null and x != ''``（不是 ``isBlank``），
    所以 ``tableName = " "`` 会真的去 ``like '% %'``。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}
    gen_params: Mapping[str, Any] = gen_table.params or {}

    if gen_table.table_name is not None and gen_table.table_name != "":
        conditions.append("lower(table_name) like lower(concat('%', :table_name, '%'))")
        params["table_name"] = gen_table.table_name
    if gen_table.table_comment is not None and gen_table.table_comment != "":
        conditions.append("lower(table_comment) like lower(concat('%', :table_comment, '%'))")
        params["table_comment"] = gen_table.table_comment
    _append_date_range(conditions, params, gen_params)

    sql = SELECT_GEN_TABLE_VO
    if conditions:
        sql = sql + "\n\t\twhere " + " and ".join(conditions)
    return sql + "\n\t\tORDER BY create_time DESC", params


def _build_db_table_list_sql(gen_table: GenTable) -> Tuple[str, Dict[str, Any]]:
    """``selectDbTableList`` —— 固定 3 个过滤 + 4 个 ``<if>``，**没有** ``order by``。"""
    conditions: List[str] = []
    params: Dict[str, Any] = {}
    gen_params: Mapping[str, Any] = gen_table.params or {}

    if gen_table.table_name is not None and gen_table.table_name != "":
        conditions.append("lower(table_name) like lower(concat('%', :table_name, '%'))")
        params["table_name"] = gen_table.table_name
    if gen_table.table_comment is not None and gen_table.table_comment != "":
        conditions.append("lower(table_comment) like lower(concat('%', :table_comment, '%'))")
        params["table_comment"] = gen_table.table_comment
    _append_date_range(conditions, params, gen_params)

    sql = _DB_TABLE_LIST_HEAD
    if conditions:
        sql = sql + "\n\t\t\tAND " + " AND ".join(conditions)
    return sql, params


def _append_date_range(
    conditions: List[str], params: Dict[str, Any], gen_params: Mapping[str, Any]
) -> None:
    """``<if test="params.beginTime ...">`` / ``endTime`` 两条时间范围条件.

    ``date_format(x,'%y%m%d')`` 是两位年份，照抄 —— 换成 ``%Y%m%d`` 会让
    ``2024-01-01`` 与 ``1924-01-01`` 之外的行为差异在跨世纪数据上暴露。
    """
    begin = gen_params.get("beginTime")
    if begin is not None and begin != "":
        conditions.append("date_format(create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')")
        params["begin_time"] = begin
    end = gen_params.get("endTime")
    if end is not None and end != "":
        conditions.append("date_format(create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')")
        params["end_time"] = end


def _build_join_sql(
    table_columns: Sequence[str],
    column_columns: Sequence[str],
    condition: Optional[str],
    params: Optional[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    """三条 ``t LEFT JOIN gen_table_column c`` 语句共用的拼装.

    列顺序必须与 XML 逐字一致：``selectGenTableById`` / ``ByName`` / ``All`` 的
    ``t.`` 投影**互不相同**（16 / 16 / 14 列），所以列清单由调用方传入。
    """
    select_list = ", ".join(f"t.{name}" for name in table_columns)
    select_list += ", " + ", ".join(f"c.{name}" for name in column_columns)
    sql = (
        f"SELECT {select_list}\n"
        "\t\tFROM gen_table t\n"
        "\t\tLEFT JOIN gen_table_column c ON t.table_id = c.table_id"
    )
    if condition:
        sql = f"{sql}\n\t\twhere {condition}"
    sql = f"{sql} order by c.sort"
    return sql, params or {}


def _build_update_sql(gen_table: GenTable) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update gen_table set ... where table_id = :table_id``（Java: ``<set>``）。

    ``update_time = sysdate()`` 是无条件的，所以 ``<set>`` 永不为空。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute, require_text in _UPDATE_GEN_TABLE_COLUMNS:
        value = getattr(gen_table, attribute)
        if value is None:
            continue
        if require_text and value == "":
            continue
        sets.append(f"{attribute} = :{attribute}")
        params[attribute] = value

    sets.append("update_time = sysdate()")
    params["table_id"] = gen_table.table_id

    return "update gen_table set " + ", ".join(sets) + " where table_id = :table_id", params


# --------------------------------------------------------------------------- 行 -> 对象


def _map_gen_table(
    row: Any, columns: Sequence[str], keys: Optional[Sequence[str]] = None
) -> GenTable:
    """One result row -> one ``GenTable``（Java: ``resultMap="GenTableResult"``）.

    ``columns`` 决定**映射哪些列**（同一条 resultMap 被三条投影不同的语句共用），
    ``keys`` 缺省即 ``columns``。
    """
    labels = list(keys) if keys is not None else list(columns)
    values = {label: row[labels.index(label)] for label in labels}
    fields = {name: values[name] for name in columns if name in values}
    return GenTable(**fields)


def _group_joined_rows(
    rows: Sequence[Any], keys: Sequence[str], table_columns: Sequence[str]
) -> List[GenTable]:
    """把 ``t LEFT JOIN c`` 的行按 ``table_id`` 聚成 ``GenTable`` + ``columns``.

    MyBatis 的 ``<collection>`` 只在该行**至少有一个** column 映射列非空时才创建一个
    元素；``LEFT JOIN`` 打出的全 null 行因此不会产生"空列对象"。这里用
    ``column_id is None and column_name is None`` 判断，与 MyBatis 的
    ``foundValues`` 规则一致（``column_id`` 是 ``<id>``，``column_name`` 是
    ``GenTableColumn`` 的必填业务列）。
    """
    labels = list(keys)
    index_of = {label: position for position, label in enumerate(labels)}

    grouped: Dict[Any, GenTable] = {}
    order: List[Any] = []
    for row in rows:
        values = {label: row[index_of[label]] for label in labels if label in index_of}
        table_key = values.get("table_id")
        table = grouped.get(table_key)
        if table is None:
            fields = {name: values[name] for name in table_columns if name in values}
            table = GenTable(**fields)
            table.columns = []
            grouped[table_key] = table
            order.append(table_key)
        if values.get("column_id") is None and values.get("column_name") is None:
            continue
        table.columns.append(
            GenTableColumn(**{name: values[name] for name in _JOIN_COLUMN_COLUMNS if name in values})
        )
    return [grouped[key] for key in order]


__all__ = ["GenTableMapper", "SELECT_GEN_TABLE_VO", "_SELECT_TABLE_BY_NAME"]
