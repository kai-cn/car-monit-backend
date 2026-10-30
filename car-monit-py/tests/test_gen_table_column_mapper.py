# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-generator/src/main/resources/mapper/generator/GenTableColumnMapper.xml
#   ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableColumnMapper.java

"""``GenTableColumnMapper`` —— 8 条 statement，接口 8 个方法，一一对应.

这一层为什么值钱
----------------
三处改错**不会报错**、只会悄悄改数据：

1. ``deleteGenTableColumnByIds`` 删的是 **``table_id``**（不是 ``column_id``），
   而 ``deleteGenTableColumns`` 删的是 ``column_id`` 且入参是**实体列表**
   （``#{item.columnId}``）。两个方法名长得像，作用域完全不同 —— 混用会一次删掉
   整张表的所有字段配置。
2. ``updateGenTableColumn`` 前 12 列**无条件**写（传 ``null`` 就是 ``= NULL``），
   后 6 个关列表才带 ``<if>``。这是编辑弹窗"清空某列"能生效的原因；把 12 列也加上
   ``<if>`` 会让"清空"变成"保持原值"。
3. ``insertGenTableColumn`` 只有 ``sort`` 判 ``!= null``，其余 23 列判
   ``!= null and != ''``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.generator.domain.gen_table_column import GenTableColumn
from app.generator.mapper import gen_table_column_mapper as mapper_module
from app.generator.mapper.gen_table_column_mapper import (
    SELECT_GEN_TABLE_COLUMN_VO,
    GenTableColumnMapper,
)

# --------------------------------------------------------------------------- fakes


class _Result:
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


@pytest.fixture()
def factory(monkeypatch: pytest.MonkeyPatch) -> Any:
    def _install(*results: _Result) -> _SessionFactory:
        installed = _SessionFactory(*results)
        monkeypatch.setattr(mapper_module, "session_scope", installed)
        return installed

    return _install


# --------------------------------------------------------------------------- 列清单

#: ``selectGenTableColumnVo`` 的 28 列（6 个关列表在前，顺序即 XML 列序）。
_VO_KEYS: Sequence[str] = (
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

#: ``selectDbTableColumnsByName`` 的 7 列。
_DB_KEYS: Sequence[str] = (
    "column_name",
    "is_required",
    "is_pk",
    "sort",
    "column_comment",
    "is_increment",
    "column_type",
)


def _vo_row(column_id: int = 11, column_name: str = "user_id", sort: int = 1) -> tuple:
    values: Dict[str, Any] = {key: None for key in _VO_KEYS}
    values["column_id"] = column_id
    values["table_id"] = 7
    values["column_name"] = column_name
    values["column_comment"] = "用户ID"
    values["column_type"] = "bigint(20)"
    values["java_type"] = "Long"
    values["java_field"] = column_name
    values["is_pk"] = "1"
    values["sort"] = sort
    return tuple(values[key] for key in _VO_KEYS)


# --------------------------------------------------------------------------- 常量

def test_select_gen_table_column_vo_is_verbatim() -> None:
    """28 列，6 个关联表列在**最前面** —— 列序奇怪但照抄."""
    assert SELECT_GEN_TABLE_COLUMN_VO.startswith(
        "select field_map_string, link_table_id, single_selection, multiple_selections, "
        "dialog_search_column_ids, dialog_list_column_ids, column_id, table_id,"
    )
    assert SELECT_GEN_TABLE_COLUMN_VO.endswith("create_by, create_time, update_by, update_time from gen_table_column")
    assert len(_VO_KEYS) == 28


# --------------------------------------------------------------------------- 读

def test_select_db_table_columns_by_name(factory: Any) -> None:
    """三个 ``case when`` 的字面量混用：``is_required`` 假值是 **null**，另两个是 ``'0'``."""
    session = factory(
        _Result(
            rows=[("user_id", None, "1", 1, "用户ID", "1", "bigint(20)")],
            keys=_DB_KEYS,
        )
    )

    columns = GenTableColumnMapper().select_db_table_columns_by_name("sys_user")

    sql = session.statements[0]
    assert "from information_schema.columns where table_schema = (select database())" in sql
    # 括号是 XML 里就有的，照抄
    assert "and table_name = (:table_name)" in sql
    assert "order by ordinal_position" in sql
    assert "then '1' else null end) as is_required" in sql
    assert "then '1' else '0' end) as is_pk" in sql
    assert "(case when extra = 'auto_increment' then '1' else '0' end) as is_increment" in sql
    assert session.params[0] == {"table_name": "sys_user"}
    assert len(columns) == 1
    assert columns[0].column_name == "user_id"
    assert columns[0].is_required is None
    assert columns[0].is_pk == "1"
    assert columns[0].sort == 1


def test_select_gen_table_column_list_by_table_column_ids(factory: Any) -> None:
    session = factory(_Result(rows=[_vo_row(11), _vo_row(12, "user_name", 2)], keys=_VO_KEYS))

    columns = GenTableColumnMapper().select_gen_table_column_list_by_table_column_ids(
        ["11", "12"]
    )

    sql = session.statements[0]
    assert "where column_id in (:id0, :id1) order by sort" in sql
    assert session.params[0] == {"id0": "11", "id1": "12"}
    assert [column.column_id for column in columns] == [11, 12]


def test_select_gen_table_column_list_by_table_column_ids_empty(factory: Any) -> None:
    """空列表拼出 ``in ()``，MySQL 语法错 —— service 层保证不会传空."""
    session = factory(_Result(rows=[], keys=_VO_KEYS))

    GenTableColumnMapper().select_gen_table_column_list_by_table_column_ids([])

    assert "where column_id in () order by sort" in session.statements[0]
    assert session.params[0] == {}


def test_select_gen_table_column_list_without_conditions(factory: Any) -> None:
    session = factory(_Result(rows=[], keys=_VO_KEYS))

    GenTableColumnMapper().select_gen_table_column_list(GenTableColumn())

    sql = session.statements[0]
    assert "where" not in sql.lower()
    assert sql.endswith("ORDER BY sort")
    assert session.params[0] == {}


def test_select_gen_table_column_list_conditions(factory: Any) -> None:
    session = factory(_Result(rows=[], keys=_VO_KEYS))

    GenTableColumnMapper().select_gen_table_column_list(
        GenTableColumn(table_id=7, column_name="user", java_field="userId")
    )

    sql = session.statements[0]
    assert "where table_id = :table_id" in sql
    assert "and `column_name` LIKE CONCAT('%', :column_name, '%%')" in sql
    assert "and java_field LIKE CONCAT('%', :java_field, '%%')" in sql
    assert session.params[0] == {
        "table_id": 7,
        "column_name": "user",
        "java_field": "userId",
    }


def test_select_gen_table_column_list_table_id_zero_is_not_skipped(factory: Any) -> None:
    """``tableId != null and tableId != ''`` —— 对整数来说 ``0`` 会真的去查."""
    session = factory(_Result(rows=[], keys=_VO_KEYS))

    GenTableColumnMapper().select_gen_table_column_list(GenTableColumn(table_id=0))

    assert "where table_id = :table_id" in session.statements[0]
    assert session.params[0] == {"table_id": 0}


def test_select_gen_table_column_list_by_table_id(factory: Any) -> None:
    session = factory(_Result(rows=[_vo_row()], keys=_VO_KEYS))

    columns = GenTableColumnMapper().select_gen_table_column_list_by_table_id(7)

    assert session.statements[0].endswith("where table_id = :table_id order by sort")
    assert session.params[0] == {"table_id": 7}
    assert columns[0].table_id == 7


def test_map_column_ignores_unknown_result_keys(factory: Any) -> None:
    """resultMap 只认自己声明的列 —— 多出来的列名不能塞进实体."""
    keys = list(_VO_KEYS) + ["unexpected_column"]
    row = _vo_row() + ("丢掉",)
    factory(_Result(rows=[row], keys=keys))

    columns = GenTableColumnMapper().select_gen_table_column_list_by_table_id(7)

    assert columns[0].column_id == 11
    assert not hasattr(columns[0], "unexpected_column")


# --------------------------------------------------------------------------- 写

def test_insert_gen_table_column_dynamic_columns(factory: Any) -> None:
    session = factory(_Result(rowcount=1, lastrowid=99))
    column = GenTableColumn(
        table_id=7,
        column_name="user_id",
        column_comment="",
        column_type="bigint(20)",
        java_type="Long",
        java_field="userId",
        is_pk="1",
        sort=None,
        create_by="admin",
    )

    rowcount = GenTableColumnMapper().insert_gen_table_column(column)

    sql = session.statements[0]
    assert sql.startswith("insert into gen_table_column (table_id,column_name,")
    # 空串 / None 的列都被跳过
    assert "column_comment" not in sql
    assert "sort" not in sql
    assert "sysdate()" in sql
    assert session.params[0]["java_field"] == "userId"
    assert "sort" not in session.params[0]
    assert column.column_id == 99
    assert rowcount == 1


def test_insert_gen_table_column_keeps_sort_zero(factory: Any) -> None:
    """``sort != null`` —— ``0`` 是合法值，不能当成"空"丢掉."""
    session = factory(_Result(rowcount=1, lastrowid=1))

    GenTableColumnMapper().insert_gen_table_column(
        GenTableColumn(column_name="c", sort=0)
    )

    assert "sort" in session.statements[0]
    assert session.params[0]["sort"] == 0


def test_insert_gen_table_column_without_lastrowid(factory: Any) -> None:
    factory(_Result(rowcount=0))
    column = GenTableColumn(column_name="c")

    assert GenTableColumnMapper().insert_gen_table_column(column) == 0
    assert column.column_id is None


def test_update_gen_table_column_always_writes_twelve_columns(factory: Any) -> None:
    """12 列无条件写（``= NULL``）；6 个关列表为空时**不写**."""
    session = factory(_Result(rowcount=1))
    column = GenTableColumn(
        column_id=11,
        column_comment=None,
        java_type=None,
        java_field=None,
        is_insert=None,
        is_edit=None,
        is_list=None,
        is_query=None,
        is_required=None,
        query_type=None,
        html_type=None,
        dict_type=None,
        sort=None,
        link_table_id=None,
        single_selection="",
        multiple_selections=None,
        dialog_search_column_ids=None,
        dialog_list_column_ids=None,
        field_map_string=None,
        update_by="admin",
    )

    GenTableColumnMapper().update_gen_table_column(column)

    sql = session.statements[0]
    for name in (
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
    ):
        assert f"{name} = :{name}" in sql, name
        assert session.params[0][name] is None, name
    # 6 个关列表一个都不能出现
    for name in (
        "link_table_id",
        "single_selection",
        "multiple_selections",
        "dialog_search_column_ids",
        "dialog_list_column_ids",
        "field_map_string",
    ):
        assert f"{name} = :{name}" not in sql, name
    assert "update_by = :update_by" in sql
    assert sql.endswith("update_time = sysdate() where column_id = :column_id")
    assert session.params[0]["column_id"] == 11


def test_update_gen_table_column_optional_columns_written(factory: Any) -> None:
    session = factory(_Result(rowcount=1))
    column = GenTableColumn(
        column_id=11,
        link_table_id=8,
        single_selection="1",
        multiple_selections="0",
        dialog_search_column_ids="1,2",
        dialog_list_column_ids="3",
        field_map_string="[]",
    )

    GenTableColumnMapper().update_gen_table_column(column)

    sql = session.statements[0]
    assert "link_table_id = :link_table_id" in sql
    assert "field_map_string = :field_map_string" in sql
    assert session.params[0]["single_selection"] == "1"
    assert session.params[0]["multiple_selections"] == "0"
    assert session.params[0]["dialog_list_column_ids"] == "3"


# --------------------------------------------------------------------------- 删

def test_delete_gen_table_columns_iterates_entities(factory: Any) -> None:
    """``<foreach collection="list" item="item">#{item.columnId}</foreach>`` —— 入参是实体."""
    session = factory(_Result(rowcount=2))

    rowcount = GenTableColumnMapper().delete_gen_table_columns(
        [GenTableColumn(column_id=11), GenTableColumn(column_id=12)]
    )

    assert session.statements[0] == "delete from gen_table_column where column_id in (:p0, :p1)"
    assert session.params[0] == {"p0": 11, "p1": 12}
    assert rowcount == 2


def test_delete_gen_table_column_by_ids_deletes_by_table_id(factory: Any) -> None:
    """方法名叫 ``...ByIds``，但 XML 里是 ``where table_id in (...)``."""
    session = factory(_Result(rowcount=3))

    rowcount = GenTableColumnMapper().delete_gen_table_column_by_ids([7, 8])

    assert session.statements[0] == "delete from gen_table_column where table_id in (:p0, :p1)"
    assert "column_id" not in session.statements[0]
    assert session.params[0] == {"p0": 7, "p1": 8}
    assert rowcount == 3


def test_delete_gen_table_column_by_ids_empty_is_broken_sql(factory: Any) -> None:
    session = factory(_Result(rowcount=0))

    GenTableColumnMapper().delete_gen_table_column_by_ids([])

    assert session.statements[0] == "delete from gen_table_column where table_id in ()"
