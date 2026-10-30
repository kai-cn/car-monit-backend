"""代码生成业务字段表 mapper.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableColumnMapper.java
# Migrated from: ruoyi-generator/src/main/resources/mapper/generator/GenTableColumnMapper.xml

XML 里 8 条 statement，接口 8 个方法，一一对应，**没有**孤儿语句。

``<sql id="selectGenTableColumnVo">`` 的列序很奇怪
--------------------------------------------------
它把 6 个"关联表"列（``field_map_string`` / ``link_table_id`` /
``single_selection`` / ``multiple_selections`` / ``dialog_search_column_ids`` /
``dialog_list_column_ids``）放在**最前面**，后面才是 ``column_id`` .. ``update_time``
那 22 列。Java 侧靠 ``resultMap`` 按**列名**映射，列序本身不影响结果；但
``/tool/gen/column/{tableId}`` 的响应体字段序由 ``GenTableColumn`` 的**声明序**决定
（不是查询列序），所以这里也按名字映射、不依赖列序。

``selectDbTableColumnsByName`` 一次读出整张表的物理结构
-----------------------------------------------------
三个 ``case when`` 直接把 ``is_required`` / ``is_pk`` / ``is_increment`` 算成
``'1'`` / ``'0'`` / ``null`` 字符串，``ordinal_position`` 直接当 ``sort``。
注意 ``is_required`` 为假时返回的是 **null**（不是 ``'0'``），而 ``is_pk`` /
``is_increment`` 为假时返回 ``'0'`` —— 三种字面量混用，照抄。

``deleteGenTableColumns`` 的 ``<foreach>`` 迭代的是**实体**
----------------------------------------------------------
``collection="list" item="item"`` + ``#{item.columnId}``，所以入参是
``List<GenTableColumn>`` 而不是 id 数组。别把它和 ``deleteGenTableColumnByIds``
（按 ``table_id`` 删）混在一起：两者作用域完全不同。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.config.database import session_scope
from app.generator.domain.gen_table_column import GenTableColumn
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from GenTableColumnMapper.xml -> ``<sql id="selectGenTableColumnVo">``.
#: 28 列，顺序与 XML 完全一致（6 个关列表在前）。
SELECT_GEN_TABLE_COLUMN_VO = """select field_map_string, link_table_id, single_selection, multiple_selections, dialog_search_column_ids, dialog_list_column_ids, column_id, table_id, column_name, column_comment, column_type, java_type, java_field, is_pk, is_increment, is_required, is_insert, is_edit, is_list, is_query, query_type, html_type, dict_type, sort, create_by, create_time, update_by, update_time from gen_table_column"""

#: ``selectGenTableColumnVo`` 投影的 28 列（与 ``GenTableColumnResult`` 的属性同名）。
_COLUMN_VO_COLUMNS: Tuple[str, ...] = (
    "field_map_string",
    "link_table_id",
    "single_selection",
    "multiple_selections",
    "dialog_search_column_ids",
    "dialog_list_column_ids",
    "column_id",
    "table_id",
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
    "sort",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
)

#: ``selectDbTableColumnsByName`` 从 ``information_schema.columns`` 取的列（7 列）。
_DB_COLUMN_COLUMNS: Tuple[str, ...] = (
    "column_name",
    "is_required",
    "is_pk",
    "sort",
    "column_comment",
    "is_increment",
    "column_type",
)

#: Verbatim from ``<select id="selectDbTableColumnsByName">``。
_DB_COLUMN_SQL = """select column_name, (case when (is_nullable = 'no' && column_key != 'PRI') then '1' else null end) as is_required, (case when column_key = 'PRI' then '1' else '0' end) as is_pk, ordinal_position as sort, column_comment, (case when extra = 'auto_increment' then '1' else '0' end) as is_increment, column_type
		from information_schema.columns where table_schema = (select database()) and table_name = (:table_name)
		order by ordinal_position"""

#: ``insertGenTableColumn`` 的动态列，顺序与 XML 一致；第三项是"是否要求非空串"。
#: 只有 ``sort`` 是 ``!= null``（整数列，空串无意义），其余全是 ``!= null and != ''``。
_INSERT_COLUMN_FIELDS: Tuple[Tuple[str, bool], ...] = (
    ("table_id", True),
    ("link_table_id", True),
    ("single_selection", True),
    ("multiple_selections", True),
    ("dialog_search_column_ids", True),
    ("dialog_list_column_ids", True),
    ("field_map_string", True),
    ("column_name", True),
    ("column_comment", True),
    ("column_type", True),
    ("java_type", True),
    ("java_field", True),
    ("is_pk", True),
    ("is_increment", True),
    ("is_required", True),
    ("is_insert", True),
    ("is_edit", True),
    ("is_list", True),
    ("is_query", True),
    ("query_type", True),
    ("html_type", True),
    ("dict_type", True),
    ("sort", False),
    ("create_by", True),
)

#: ``updateGenTableColumn`` 里**无条件**写入的 12 列（XML 第 147-158 行）。
#: 传 ``null`` 就是写 ``NULL`` —— 这是编辑弹窗"清空某列"能生效的原因。
_UPDATE_COLUMN_ALWAYS: Tuple[str, ...] = (
    "column_comment",
    "java_type",
    "java_field",
    "is_insert",
    "is_edit",
    "is_list",
    "is_query",
    "is_required",
    "query_type",
    "html_type",
    "dict_type",
    "sort",
)

#: ``updateGenTableColumn`` 里带 ``<if>`` 的 6 个关列表（``!= null and != ''``）。
_UPDATE_COLUMN_OPTIONAL: Tuple[str, ...] = (
    "link_table_id",
    "single_selection",
    "multiple_selections",
    "dialog_search_column_ids",
    "dialog_list_column_ids",
    "field_map_string",
)


class GenTableColumnMapper:
    """Java: ``interface GenTableColumnMapper``."""

    # Java: List<GenTableColumn> selectDbTableColumnsByName(String tableName)
    def select_db_table_columns_by_name(self, table_name: str) -> List[GenTableColumn]:
        """读物理表的列结构（导入表时用）。

        ``table_name = (#{tableName})`` 括号是 XML 里就有的，照抄 —— MySQL 下
        括号包一个占位符等价于不加括号，但改掉它就是"擅自清理"。
        """
        with session_scope() as session:
            result = session.execute(text(_DB_COLUMN_SQL), {"table_name": table_name})
            keys = list(result.keys())
            rows = result.all()
        return [
            GenTableColumn(**{name: row[keys.index(name)] for name in _DB_COLUMN_COLUMNS if name in keys})
            for row in rows
        ]

    # Java: List<GenTableColumn> selectGenTableColumnListByTableColumnIds(@Param("tableColumnIdList") List<String> tableColumnIdList)
    def select_gen_table_column_list_by_table_column_ids(
        self, table_column_id_list: Sequence[str]
    ) -> List[GenTableColumn]:
        """``<where><if test="tableColumnIdList != null">`` —— ``<if>`` 成立即拼 ``IN``。

        id 列表为空时拼出 ``column_id IN ()``，MySQL 语法错；service 层保证
        不会传空列表过来（空列表直接返回 ``null``），所以这里不做兜底。
        """
        clause, params = _in_clause("column_id", table_column_id_list, "id")
        sql = f"{SELECT_GEN_TABLE_COLUMN_VO}\n        where {clause}\n        order by sort"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.all()
        return [_map_column(row, keys) for row in rows]

    # Java: List<GenTableColumn> selectGenTableColumnList(GenTableColumn genTableColumn)
    def select_gen_table_column_list(
        self, gen_table_column: GenTableColumn
    ) -> List[GenTableColumn]:
        """三个 ``<if>`` + ``ORDER BY sort``。

        ``tableId`` 的判据是 ``!= null and != ''`` —— 对整数来说 ``0`` 会真的去
        ``where table_id = 0``（查不到行），与 ``!= null`` 不同。
        """
        conditions: List[str] = []
        params: Dict[str, Any] = {}

        if gen_table_column.table_id is not None and gen_table_column.table_id != "":
            conditions.append("table_id = :table_id")
            params["table_id"] = gen_table_column.table_id
        if gen_table_column.column_name is not None and gen_table_column.column_name != "":
            conditions.append("`column_name` LIKE CONCAT('%', :column_name, '%%')")
            params["column_name"] = gen_table_column.column_name
        if gen_table_column.java_field is not None and gen_table_column.java_field != "":
            conditions.append("java_field LIKE CONCAT('%', :java_field, '%%')")
            params["java_field"] = gen_table_column.java_field

        sql = SELECT_GEN_TABLE_COLUMN_VO
        if conditions:
            sql = f"{sql}\n        where " + " and ".join(conditions)
        sql = f"{sql}\n        ORDER BY sort"

        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.all()
        return [_map_column(row, keys) for row in rows]

    # Java: List<GenTableColumn> selectGenTableColumnListByTableId(Long tableId)
    def select_gen_table_column_list_by_table_id(
        self, table_id: Optional[int]
    ) -> List[GenTableColumn]:
        sql = f"{SELECT_GEN_TABLE_COLUMN_VO}\n        where table_id = :table_id\n        order by sort"
        with session_scope() as session:
            result = session.execute(text(sql), {"table_id": table_id})
            keys = list(result.keys())
            rows = result.all()
        return [_map_column(row, keys) for row in rows]

    # Java: int insertGenTableColumn(GenTableColumn genTableColumn)
    def insert_gen_table_column(self, gen_table_column: GenTableColumn) -> int:
        """动态列插入，``useGeneratedKeys`` 回写 ``column_id``。"""
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute, require_text in _INSERT_COLUMN_FIELDS:
            value = getattr(gen_table_column, attribute)
            if value is None:
                continue
            if require_text and value == "":
                continue
            columns.append(attribute)
            names.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        names.append("sysdate()")

        sql = (
            f"insert into gen_table_column ({','.join(columns)}) values ({','.join(names)})"
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            # Java: useGeneratedKeys="true" keyProperty="columnId"
            if getattr(result, "lastrowid", None):
                gen_table_column.column_id = int(result.lastrowid)
            return result.rowcount or 0

    # Java: int updateGenTableColumn(GenTableColumn genTableColumn)
    def update_gen_table_column(self, gen_table_column: GenTableColumn) -> int:
        sql, params = _build_update_sql(gen_table_column)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteGenTableColumns(List<GenTableColumn> genTableColumns)
    def delete_gen_table_columns(self, gen_table_columns: Sequence[GenTableColumn]) -> int:
        """``<foreach collection="list" item="item">#{item.columnId}</foreach>``.

        空列表拼出 ``in ()`` -> MySQL 语法错；service 层保证不会传空。
        """
        placeholders = ", ".join(f":p{index}" for index in range(len(gen_table_columns)))
        params = {f"p{index}": item.column_id for index, item in enumerate(gen_table_columns)}
        sql = f"delete from gen_table_column where column_id in ({placeholders})"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteGenTableColumnByIds(Long[] tableIds)
    def delete_gen_table_column_by_ids(self, table_ids: Sequence[int]) -> int:
        """按 **table_id** 批量删（不是 column_id）—— 方法名容易误读，XML 里是
        ``where table_id in (...)``。"""
        clause, params = _in_clause("table_id", table_ids, "p")
        with session_scope() as session:
            return (
                session.execute(text(f"delete from gen_table_column where {clause}"), params).rowcount
                or 0
            )


def _build_update_sql(gen_table_column: GenTableColumn) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update gen_table_column set ... where column_id = :column_id``.

    12 个无条件列即使为 ``None`` 也写进去（``= NULL``），6 个关列表为空时不写。
    ``update_time = sysdate()`` 无条件，所以 ``<set>`` 永不为空。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}

    for attribute in _UPDATE_COLUMN_ALWAYS:
        sets.append(f"{attribute} = :{attribute}")
        params[attribute] = getattr(gen_table_column, attribute)

    for attribute in _UPDATE_COLUMN_OPTIONAL:
        value = getattr(gen_table_column, attribute)
        if value is None or value == "":
            continue
        sets.append(f"{attribute} = :{attribute}")
        params[attribute] = value

    sets.append("update_by = :update_by")
    params["update_by"] = gen_table_column.update_by
    sets.append("update_time = sysdate()")
    params["column_id"] = gen_table_column.column_id

    sql = (
        "update gen_table_column set " + ", ".join(sets) + " where column_id = :column_id"
    )
    return sql, params


def _map_column(row: Any, keys: Sequence[str]) -> GenTableColumn:
    """One result row -> one ``GenTableColumn``（``resultMap="GenTableColumnResult"``）."""
    labels = list(keys)
    values: Mapping[str, Any] = {label: row[labels.index(label)] for label in labels}
    return GenTableColumn(**{name: values[name] for name in _COLUMN_VO_COLUMNS if name in values})


__all__ = ["GenTableColumnMapper", "SELECT_GEN_TABLE_COLUMN_VO"]
