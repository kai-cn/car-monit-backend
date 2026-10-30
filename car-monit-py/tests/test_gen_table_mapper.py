# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-generator/src/main/resources/mapper/generator/GenTableMapper.xml
#   ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableMapper.java

"""``GenTableMapper`` —— 10 条 statement 的 SQL 形状.

这一层为什么值钱
----------------
代码生成的读写一旦接上假 Mapper，SQL 就全被遮住了。这里有六处改错**不会报错**、
只会悄悄换结果集：

1. ``selectGenTableList`` 写死了 ``ORDER BY create_time DESC``，而
   ``selectDbTableList`` **没有** ``order by`` —— 后者要靠 PageHelper 追加前端排序。
   顺手"统一一下"会让 ``gen/index.vue`` 的"数据库表"标签页排序失效。
2. 三条 ``t LEFT JOIN gen_table_column c`` 的 ``t.`` 投影**互不相同**：
   ``ById`` / ``ByName`` 16 列、``All`` 14 列（少 ``gen_type`` / ``gen_path``）。
   少掉的列在 Java 里就是 ``null``。
3. ``selectGenTableList`` 的 select 列表里**一个 ``c.`` 都没有**，所以 MyBatis 的
   ``<collection property="columns">`` 根本不会构造 —— 每行 ``columns`` 是 ``null``
   而不是 ``[]``。
4. ``insertGenTable`` 里 ``table_name`` 只判 ``!= null``，其余 12 列判
   ``!= null and != ''``；``updateGenTable`` 里 ``table_name`` / ``sub_table_name`` /
   ``sub_table_fk_name`` / ``remark`` 只判 ``!= null``（所以空串会**清列**）。
5. ``create_time`` / ``update_time`` 是 ``sysdate()`` 字面量，无参可绑。
6. ``<select id="selectTableByName">`` 在接口里**没有对应方法**（孤儿语句），
   既不能登记成 mapper 方法，也不能删。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.generator.domain.gen_table import GenTable
from app.generator.mapper import gen_table_mapper as mapper_module
from app.generator.mapper.gen_table_mapper import (
    SELECT_GEN_TABLE_VO,
    GenTableMapper,
    _SELECT_TABLE_BY_NAME,
)

# --------------------------------------------------------------------------- fakes


class _Result:
    """One ``CursorResult``-shaped answer."""

    def __init__(
        self,
        rows: Optional[Sequence[Any]] = None,
        keys: Optional[Sequence[str]] = None,
        scalar_value: Any = None,
        rowcount: int = 0,
        lastrowid: Optional[int] = None,
    ) -> None:
        self._rows = list(rows or [])
        self._keys = list(keys or [])
        self._scalar = scalar_value
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def keys(self) -> List[str]:
        return list(self._keys)

    def all(self) -> List[Any]:
        return list(self._rows)

    def scalar(self) -> Any:
        return self._scalar


class _RecordingSession:
    def __init__(self, results: List[_Result]) -> None:
        self._results = list(results)
        self.statements: List[str] = []
        self.params: List[Dict[str, Any]] = []

    def execute(self, statement: Any, params: Optional[Dict[str, Any]] = None) -> _Result:
        self.statements.append(_flat(str(statement)))
        self.params.append(dict(params or {}))
        if not self._results:
            raise AssertionError(f"unexpected extra statement: {statement}")
        return self._results.pop(0)


class _SessionScope:
    def __init__(self, session: _RecordingSession) -> None:
        self._session = session

    def __enter__(self) -> _RecordingSession:
        return self._session

    def __exit__(self, *_exc: Any) -> bool:
        return False


class _SessionFactory:
    """Stands in for ``app.config.database.session_scope``."""

    def __init__(self, *results: _Result) -> None:
        self._results = list(results)
        self.sessions: List[_RecordingSession] = []

    def __call__(self) -> _SessionScope:
        session = _RecordingSession(self._results)
        self.sessions.append(session)
        return _SessionScope(session)

    @property
    def statements(self) -> List[str]:
        return [statement for session in self.sessions for statement in session.statements]

    @property
    def params(self) -> List[Dict[str, Any]]:
        return [params for session in self.sessions for params in session.params]


def _flat(sql: str) -> str:
    return " ".join(sql.split())


@pytest.fixture(autouse=True)
def _clear_page_state() -> Any:
    clear_page()
    yield
    clear_page()


@pytest.fixture()
def factory(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Returns a callable ``factory(*results) -> _SessionFactory`` and patches the module."""

    def _install(*results: _Result) -> _SessionFactory:
        installed = _SessionFactory(*results)
        monkeypatch.setattr(mapper_module, "session_scope", installed)
        return installed

    return _install


# --------------------------------------------------------------------------- 列清单

#: ``selectGenTableVo`` 的 20 列，顺序与 XML 一致。
_VO_KEYS: Sequence[str] = (
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
_JOIN_TABLE_KEYS: Sequence[str] = (
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

#: ``selectGenTableAll`` 的 ``t.`` 投影（14 列）。
_ALL_TABLE_KEYS: Sequence[str] = (
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

#: join 语句里 ``c.`` 的投影（23 列）。
_JOIN_COLUMN_KEYS: Sequence[str] = (
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

#: ``information_schema.tables`` 的 4 列。
_INFO_KEYS: Sequence[str] = ("table_name", "table_comment", "create_time", "update_time")


def _vo_row(table_id: int = 1, table_name: str = "sys_user") -> tuple:
    values: Dict[str, Any] = {key: None for key in _VO_KEYS}
    values["table_id"] = table_id
    values["table_name"] = table_name
    values["table_comment"] = "用户表"
    values["class_name"] = "SysUser"
    values["tpl_category"] = "crud"
    values["create_by"] = "admin"
    return tuple(values[key] for key in _VO_KEYS)


def _column_row(column_id: int, column_name: str, sort: int) -> Dict[str, Any]:
    values: Dict[str, Any] = {key: None for key in _JOIN_COLUMN_KEYS}
    values["column_id"] = column_id
    values["column_name"] = column_name
    values["java_field"] = column_name
    values["column_type"] = "bigint(20)"
    values["java_type"] = "Long"
    values["sort"] = sort
    return values


def _joined_row(
    table_keys: Sequence[str], table_id: int, column: Optional[Dict[str, Any]]
) -> tuple:
    """一行 ``t LEFT JOIN c``。``column is None`` 即 LEFT JOIN 没匹配上的全 null 行."""
    values: Dict[str, Any] = {key: None for key in table_keys}
    values.update({key: None for key in _JOIN_COLUMN_KEYS})
    values["table_id"] = table_id
    values["table_name"] = "sys_user"
    values["class_name"] = "SysUser"
    values.update(column or {})
    return tuple(values[key] for key in list(table_keys) + list(_JOIN_COLUMN_KEYS))


# --------------------------------------------------------------------------- 常量

def test_select_gen_table_vo_is_verbatim() -> None:
    """``<sql id="selectGenTableVo">`` 20 列，逐字照抄（列序 = resultMap 声明序）."""
    assert SELECT_GEN_TABLE_VO == (
        "select table_id, table_name, table_comment, sub_table_name, sub_table_fk_name, "
        "class_name, tpl_category, package_name, module_name, business_name, function_name, "
        "function_author, gen_type, gen_path, options, create_by, create_time, update_by, "
        "update_time, remark from gen_table"
    )
    assert len(_VO_KEYS) == 20


def test_select_table_by_name_is_orphan_statement() -> None:
    """``selectTableByName`` 在 ``GenTableMapper.java`` 里没有方法 —— 只能是常量."""
    assert "table_comment <> ''" in _SELECT_TABLE_BY_NAME
    assert "table_name = :table_name" in _SELECT_TABLE_BY_NAME
    assert not hasattr(GenTableMapper, "select_table_by_name")


# --------------------------------------------------------------------------- 列表

def test_select_gen_table_list_without_conditions(factory: Any) -> None:
    session = factory(_Result(rows=[_vo_row()], keys=_VO_KEYS))

    rows = GenTableMapper().select_gen_table_list(GenTable())

    assert session.statements == [
        _flat(SELECT_GEN_TABLE_VO + "\n\t\tORDER BY create_time DESC")
    ]
    assert session.params == [{}]
    assert len(rows) == 1
    assert rows[0].table_id == 1
    assert rows[0].table_name == "sys_user"
    assert rows[0].table_comment == "用户表"


def test_select_gen_table_list_columns_stay_none(factory: Any) -> None:
    """select 列表里没有 ``c.*`` -> MyBatis 不构造 collection -> ``columns`` 是 null."""
    factory(_Result(rows=[_vo_row()], keys=_VO_KEYS))

    rows = GenTableMapper().select_gen_table_list(GenTable())

    assert rows[0].columns is None
    # ``None`` 与 ``[]`` 在 JSON 里不同，这条不能被"顺手补成空列表"破坏
    assert rows[0].to_json_dict()["columns"] is None


def test_select_gen_table_list_conditions(factory: Any) -> None:
    session = factory(_Result(rows=[], keys=_VO_KEYS))
    gen_table = GenTable(
        table_name="sys",
        table_comment="用",
        params={"beginTime": "2024-01-01", "endTime": "2024-01-31"},
    )

    GenTableMapper().select_gen_table_list(gen_table)

    sql = session.statements[0]
    assert "where lower(table_name) like lower(concat('%', :table_name, '%'))" in sql
    assert "and lower(table_comment) like lower(concat('%', :table_comment, '%'))" in sql
    # 两位年份 %y%m%d —— 不是 %Y
    assert "date_format(create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')" in sql
    assert "date_format(create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')" in sql
    assert sql.endswith("ORDER BY create_time DESC")
    assert session.params[0] == {
        "table_name": "sys",
        "table_comment": "用",
        "begin_time": "2024-01-01",
        "end_time": "2024-01-31",
    }


def test_select_gen_table_list_whitespace_is_not_blank(factory: Any) -> None:
    """``<if test="tableName != null and tableName != ''">`` —— 空格算"有值"."""
    session = factory(_Result(rows=[], keys=_VO_KEYS))

    GenTableMapper().select_gen_table_list(GenTable(table_name=" "))

    assert "like lower(concat('%', :table_name, '%'))" in session.statements[0]
    assert session.params[0] == {"table_name": " "}


def test_select_gen_table_list_paged_count_first(factory: Any) -> None:
    """``startPage()`` 之后的**第一条** select 被分页：先 count，再 LIMIT."""
    session = factory(
        _Result(scalar_value=3),
        _Result(rows=[_vo_row(1), _vo_row(2, "sys_role")], keys=_VO_KEYS),
    )
    start_page()

    rows = GenTableMapper().select_gen_table_list(GenTable())

    assert len(session.statements) == 2
    count_sql = session.statements[0]
    assert count_sql.startswith("select count(0) from (select table_id")
    assert count_sql.endswith(") table_count")
    assert "order by" not in count_sql.lower()
    assert "order by create_time desc" in session.statements[1].lower()
    assert isinstance(rows, PageList)
    assert rows.total == 3
    assert rows.page_num == 1
    assert rows.page_size == 10
    assert len(rows) == 2


# --------------------------------------------------------------------------- 数据库表

def test_select_db_table_list_has_no_order_by(factory: Any) -> None:
    """这条**故意**没有 ``order by`` —— 留给 PageHelper 追加前端排序."""
    session = factory(_Result(rows=[("sys_user", "用户表", None, None)], keys=_INFO_KEYS))

    rows = GenTableMapper().select_db_table_list(GenTable())

    sql = session.statements[0]
    assert "order by" not in sql.lower()
    assert "AND table_name NOT LIKE 'qrtz_%'" in sql
    assert "AND table_name NOT LIKE 'gen_%'" in sql
    assert "AND table_name NOT IN (select table_name from gen_table)" in sql
    assert rows[0].table_name == "sys_user"
    # information_schema 没有 class_name 这一列
    assert rows[0].class_name is None


def test_select_db_table_list_filters_use_and(factory: Any) -> None:
    session = factory(_Result(rows=[], keys=_INFO_KEYS))

    GenTableMapper().select_db_table_list(
        GenTable(table_name="sys", params={"beginTime": "2024-01-01"})
    )

    sql = session.statements[0]
    assert "AND lower(table_name) like lower(concat('%', :table_name, '%'))" in sql
    assert "AND date_format(create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')" in sql
    assert session.params[0] == {"table_name": "sys", "begin_time": "2024-01-01"}


def test_select_db_table_list_by_names_placeholders(factory: Any) -> None:
    session = factory(
        _Result(
            rows=[("sys_user", "用户表", None, None), ("sys_role", "角色表", None, None)],
            keys=_INFO_KEYS,
        )
    )

    rows = GenTableMapper().select_db_table_list_by_names(["sys_user", "sys_role"])

    sql = session.statements[0]
    assert sql.endswith("and table_name in (:name0, :name1)")
    assert session.params[0] == {"name0": "sys_user", "name1": "sys_role"}
    assert [row.table_name for row in rows] == ["sys_user", "sys_role"]


def test_select_db_table_list_by_names_empty_is_broken_sql(factory: Any) -> None:
    """空数组拼出 ``in ()``，MySQL 报语法错 —— Java 侧同样如此，不兜底."""
    session = factory(_Result(rows=[], keys=_INFO_KEYS))

    GenTableMapper().select_db_table_list_by_names([])

    assert session.statements[0].endswith("and table_name in ()")
    assert session.params[0] == {}


# --------------------------------------------------------------------------- join 语句

def test_select_gen_table_all_projection_and_order(factory: Any) -> None:
    """``selectGenTableAll`` 少 ``gen_type`` / ``gen_path``，且**没有 where**."""
    session = factory(
        _Result(
            rows=[_joined_row(_ALL_TABLE_KEYS, 7, _column_row(11, "user_id", 1))],
            keys=list(_ALL_TABLE_KEYS) + list(_JOIN_COLUMN_KEYS),
        )
    )

    rows = GenTableMapper().select_gen_table_all()

    sql = session.statements[0]
    assert sql.startswith("SELECT t.table_id,")
    assert "t.gen_type" not in sql
    assert "t.gen_path" not in sql
    assert "order by c.sort" in sql
    assert "where" not in sql.lower()
    assert len(rows) == 1
    assert rows[0].table_id == 7
    assert [column.column_id for column in rows[0].columns] == [11]


def test_select_gen_table_by_id_groups_columns(factory: Any) -> None:
    keys = list(_JOIN_TABLE_KEYS) + list(_JOIN_COLUMN_KEYS)
    session = factory(
        _Result(
            rows=[
                _joined_row(_JOIN_TABLE_KEYS, 7, _column_row(11, "user_id", 1)),
                _joined_row(_JOIN_TABLE_KEYS, 7, _column_row(12, "user_name", 2)),
            ],
            keys=keys,
        )
    )

    table = GenTableMapper().select_gen_table_by_id(7)

    sql = session.statements[0]
    assert sql.startswith("SELECT t.table_id,")
    assert "t.gen_type" in sql
    assert "where t.table_id = :table_id order by c.sort" in sql
    assert session.params[0] == {"table_id": 7}
    assert table is not None
    assert [column.column_name for column in table.columns] == ["user_id", "user_name"]


def test_select_gen_table_by_id_left_join_null_row(factory: Any) -> None:
    """LEFT JOIN 打出的全 null 行不产生"空列对象"（``foundValues`` 规则）."""
    session = factory(
        _Result(
            rows=[_joined_row(_JOIN_TABLE_KEYS, 7, None)],
            keys=list(_JOIN_TABLE_KEYS) + list(_JOIN_COLUMN_KEYS),
        )
    )

    table = GenTableMapper().select_gen_table_by_id(7)

    assert session.statements[0].endswith("order by c.sort")
    assert table is not None
    assert table.columns == []


def test_select_gen_table_by_id_missing_returns_none(factory: Any) -> None:
    factory(_Result(rows=[], keys=list(_JOIN_TABLE_KEYS) + list(_JOIN_COLUMN_KEYS)))

    assert GenTableMapper().select_gen_table_by_id(999) is None


def test_select_gen_table_by_name_too_many_rows_raises(factory: Any) -> None:
    """``selectOne`` 遇到多行抛 ``TooManyResultsException`` -> 500."""
    factory(
        _Result(
            rows=[
                _joined_row(_JOIN_TABLE_KEYS, 7, _column_row(11, "user_id", 1)),
                _joined_row(_JOIN_TABLE_KEYS, 8, _column_row(12, "role_id", 1)),
            ],
            keys=list(_JOIN_TABLE_KEYS) + list(_JOIN_COLUMN_KEYS),
        )
    )

    with pytest.raises(LookupError):
        GenTableMapper().select_gen_table_by_name("sys_user")


def test_select_gen_table_by_name_where_clause(factory: Any) -> None:
    session = factory(
        _Result(
            rows=[_joined_row(_JOIN_TABLE_KEYS, 7, _column_row(11, "user_id", 1))],
            keys=list(_JOIN_TABLE_KEYS) + list(_JOIN_COLUMN_KEYS),
        )
    )

    table = GenTableMapper().select_gen_table_by_name("sys_user")

    assert "where t.table_name = :table_name order by c.sort" in session.statements[0]
    assert session.params[0] == {"table_name": "sys_user"}
    assert table is not None and table.table_id == 7


# --------------------------------------------------------------------------- 写

def test_insert_gen_table_dynamic_columns(factory: Any) -> None:
    session = factory(_Result(rowcount=1, lastrowid=42))
    gen_table = GenTable(
        table_name="sys_user",
        table_comment="",  # 空串 -> 不写这一列
        class_name="SysUser",
        tpl_category="crud",
        package_name="com.ruoyi.system",
        module_name="system",
        business_name="user",
        function_name="用户",
        function_author="ruoyi",
        gen_type="0",
        gen_path="/",
        remark=None,
        create_by="admin",
    )

    rowcount = GenTableMapper().insert_gen_table(gen_table)

    sql = session.statements[0]
    assert sql.startswith("insert into gen_table (")
    assert "table_comment" not in sql
    assert "remark" not in sql
    assert "create_time" in sql
    assert "sysdate()" in sql
    assert session.params[0]["table_name"] == "sys_user"
    assert session.params[0]["create_by"] == "admin"
    # useGeneratedKeys 回写
    assert gen_table.table_id == 42
    assert rowcount == 1


def test_insert_gen_table_keeps_empty_table_name(factory: Any) -> None:
    """``table_name`` 只判 ``!= null`` —— 空串照样进 SQL."""
    session = factory(_Result(rowcount=1, lastrowid=1))

    GenTableMapper().insert_gen_table(GenTable(table_name=""))

    assert session.statements[0].startswith("insert into gen_table (table_name,")
    assert session.params[0] == {"table_name": ""}


def test_insert_gen_table_without_lastrowid(factory: Any) -> None:
    factory(_Result(rowcount=0))

    gen_table = GenTable(table_name="t")

    assert GenTableMapper().insert_gen_table(gen_table) == 0
    assert gen_table.table_id is None


def test_update_gen_table_null_only_columns(factory: Any) -> None:
    """``remark`` / ``sub_table_name`` 只判 ``!= null`` —— 空串会**清列**."""
    session = factory(_Result(rowcount=1))
    gen_table = GenTable(
        table_id=7,
        table_name="",
        table_comment="",
        sub_table_name="",
        sub_table_fk_name=None,
        class_name="SysUser",
        remark="",
    )

    GenTableMapper().update_gen_table(gen_table)

    sql = session.statements[0]
    assert sql.startswith("update gen_table set ")
    # 只判 != null 的四列：空串保留、None 丢弃
    assert "table_name = :table_name" in sql
    assert "sub_table_name = :sub_table_name" in sql
    assert "remark = :remark" in sql
    assert "sub_table_fk_name" not in sql
    # 判 != null and != '' 的列：空串丢弃
    assert "table_comment" not in sql
    assert sql.endswith("update_time = sysdate() where table_id = :table_id")
    assert session.params[0]["table_name"] == ""
    assert session.params[0]["remark"] == ""
    assert session.params[0]["table_id"] == 7


def test_delete_gen_table_by_ids_placeholders(factory: Any) -> None:
    session = factory(_Result(rowcount=2))

    rowcount = GenTableMapper().delete_gen_table_by_ids([3, 5])

    assert session.statements[0] == "delete from gen_table where table_id in (:p0, :p1)"
    assert session.params[0] == {"p0": 3, "p1": 5}
    assert rowcount == 2


def test_delete_gen_table_by_ids_empty_is_broken_sql(factory: Any) -> None:
    session = factory(_Result(rowcount=0))

    GenTableMapper().delete_gen_table_by_ids([])

    assert session.statements[0] == "delete from gen_table where table_id in ()"
