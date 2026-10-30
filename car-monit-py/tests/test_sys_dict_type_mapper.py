"""``SysDictTypeMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysDictTypeMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDictTypeMapper.java

这一层为什么值钱
----------------
字典类型的 CRUD 一旦接上假 Mapper，SQL 就全被遮住了。这里有四处改错了**不会报错**、
只会悄悄换结果集或改掉数据：

1. ``selectDictTypeList`` 的 5 个 ``<if>`` 判据是 OGNL 的 ``!= null and != ''``，
   **不是** ``isBlank`` —— 传 ``" "``（单个空格）时 Java 照样 ``like '% %'``。
   用 RuoYi 那个会 ``trim`` 的 ``StringUtils.isEmpty`` 去判就会漏条件。
2. ``insertDictType`` **没有** ``useGeneratedKeys``，插入后 ``dictId`` 仍是 ``null``。
   顺手回写 ``lastrowid`` 会让"新增后再查重"的边界行为变掉。
3. ``status`` 在 insert / update 里都只判 ``!= null``，空串会照写；而 ``remark``
   在 insert 里判 ``!= null and != ''``、在 update 里却只判 ``!= null``。
4. ``selectDictTypeVo`` 只投影 7 列，**没有** ``update_by`` / ``update_time``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_dict_type import SysDictType
from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.system.mapper.sys_dict_type_mapper import SELECT_DICT_TYPE_VO, SysDictTypeMapper

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
        self.statements.append(" ".join(str(statement).split()))
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


@pytest.fixture(autouse=True)
def _clear_page_state() -> Any:
    clear_page()
    yield
    clear_page()


#: ``selectDictTypeVo`` 的 7 列，顺序与 XML 一致。
_TYPE_KEYS: Sequence[str] = (
    "dict_id",
    "dict_name",
    "dict_type",
    "status",
    "create_by",
    "create_time",
    "remark",
)


def _row(dict_id: int = 1) -> tuple:
    return (dict_id, "用户性别", "sys_user_sex", "0", "admin", None, "备注")


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_dict_type_mapper

    monkeypatch.setattr(sys_dict_type_mapper, "session_scope", factory)


# --------------------------------------------------------------------------- selectDictTypeList


class TestSelectDictTypeList:
    def test_without_filters_there_is_no_where_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """5 个 ``<if>`` 都不命中时 ``<where>`` 不产出内容，但 ``order by`` 仍在。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        rows = SysDictTypeMapper().select_dict_type_list(SysDictType())

        assert [row.dict_id for row in rows] == [1]
        statement = factory.statements[0]
        assert " from sys_dict_type" in statement
        assert "where" not in statement.lower()
        assert statement.endswith("order by create_time desc")

    def test_the_five_filters_keep_the_xml_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``dictName`` -> ``status`` -> ``dictType`` -> ``beginTime`` -> ``endTime``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().select_dict_type_list(
            SysDictType(
                dict_name="性别",
                dict_type="sys_user",
                status="0",
                params={"beginTime": "2024-01-01", "endTime": "2024-12-31"},
            )
        )

        statement = factory.statements[0]
        expected = [
            "dict_name like concat('%', :dict_name, '%')",
            "status = :status",
            "dict_type like concat('%', :dict_type, '%')",
            "date_format(create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')",
            "date_format(create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')",
        ]
        positions = [statement.lower().index(fragment.lower()) for fragment in expected]
        assert positions == sorted(positions)
        assert factory.params[0] == {
            "dict_name": "性别",
            "status": "0",
            "dict_type": "sys_user",
            "begin_time": "2024-01-01",
            "end_time": "2024-12-31",
        }

    def test_dict_type_is_a_like_while_status_is_equality(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """字典类型下拉框要能模糊搜（``sys_`` -> 一批），状态是精确值。"""
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().select_dict_type_list(
            SysDictType(dict_type="sys_", status="0")
        )

        statement = factory.statements[0]
        assert "dict_type like concat('%', :dict_type, '%')" in statement
        assert "status = :status" in statement
        assert "status like" not in statement

    def test_empty_strings_drop_the_condition(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().select_dict_type_list(
            SysDictType(dict_name="", dict_type="", status="")
        )

        assert "where" not in factory.statements[0].lower()

    def test_a_single_space_still_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """判据是 ``!= ''`` 而不是 ``isBlank``；``" "`` 不是空串。"""
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().select_dict_type_list(SysDictType(dict_name=" "))

        assert "dict_name like concat('%', :dict_name, '%')" in factory.statements[0]
        assert factory.params[0] == {"dict_name": " "}

    def test_an_empty_params_dictionary_skips_the_dates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``params`` 为空 dict / 缺键时两条时间条件都不出现。"""
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().select_dict_type_list(SysDictType(params={}))

        assert "date_format" not in factory.statements[0]

    def test_the_where_clause_does_not_start_with_and(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<where>`` 会吃掉首个 ``AND``；拼出 ``where AND a`` 就是 SQL 语法错。"""
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().select_dict_type_list(
            SysDictType(dict_name="性别", status="0")
        )

        statement = factory.statements[0]
        assert "where and" not in statement.lower()
        assert "where dict_name like" in statement
        assert " and status = :status" in statement

    def test_after_start_page_the_count_wraps_the_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(
            _Result(scalar_value=7),
            _Result(rows=[_row()], keys=_TYPE_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()

        rows = SysDictTypeMapper().select_dict_type_list(SysDictType(status="0"))

        assert isinstance(rows, PageList)
        assert rows.total == 7
        count_statement, data_statement = factory.statements
        assert count_statement.startswith("select count(0) from (")
        assert count_statement.endswith(") table_count")
        assert data_statement.endswith("order by create_time desc LIMIT 0, 10")

    def test_without_start_page_nothing_is_paginated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        rows = SysDictTypeMapper().select_dict_type_list(SysDictType())

        assert isinstance(rows, PageList)
        assert rows.total == 1
        assert "LIMIT" not in factory.statements[0]

    def test_the_client_order_by_is_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """语句自带 ``order by`` 时不再追加 ``orderByColumn``（``COMPATIBILITY`` §25.6）。"""
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        query = SysDictType(params={"orderByColumn": "dict_name", "isAsc": "ascending"})
        SysDictTypeMapper().select_dict_type_list(query)

        statement = factory.statements[0]
        assert "order by create_time desc" in statement
        assert "dict_name asc" not in statement


# --------------------------------------------------------------------------- selectDictTypeAll


class TestSelectDictTypeAll:
    def test_it_is_unpaged_and_ordered_by_create_time_desc(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``/optionselect`` 与启动预热共用；**不**走 ``take_page``。"""
        factory = _SessionFactory(_Result(rows=[_row(2)], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)
        start_page()

        rows = SysDictTypeMapper().select_dict_type_all()

        assert [row.dict_id for row in rows] == [2]
        assert factory.statements[0].endswith("order by create_time desc")
        assert "LIMIT" not in factory.statements[0]

    def test_it_keeps_the_page_for_the_next_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """上面那条没有 ``take_page``，所以分页参数还挂着给下一条 select。"""
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)
        start_page()

        SysDictTypeMapper().select_dict_type_all()

        from app.common.core.page.page_helper import take_page

        assert take_page() is not None


# --------------------------------------------------------------------------- 单行查询


class TestSingleRowSelects:
    def test_the_seven_columns_are_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row(3)], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        entity = SysDictTypeMapper().select_dict_type_by_id(3)

        assert entity is not None
        assert entity.dict_id == 3
        assert entity.dict_name == "用户性别"
        assert entity.dict_type == "sys_user_sex"
        assert entity.status == "0"
        assert entity.remark == "备注"
        assert factory.statements[0].endswith("where dict_id = :dict_id")
        assert factory.params[0] == {"dict_id": 3}

    def test_update_by_is_always_null(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``selectDictTypeVo`` 不投影 ``update_by`` / ``update_time``。"""
        factory = _SessionFactory(_Result(rows=[_row(3)], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        entity = SysDictTypeMapper().select_dict_type_by_id(3)

        assert entity is not None
        assert entity.update_by is None
        assert entity.update_time is None

    def test_a_missing_row_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        assert SysDictTypeMapper().select_dict_type_by_id(404) is None

    def test_select_by_type_uses_the_type_column(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        entity = SysDictTypeMapper().select_dict_type_by_type("sys_user_sex")

        assert entity is not None
        assert factory.statements[0].endswith("where dict_type = :dict_type")
        assert factory.params[0] == {"dict_type": "sys_user_sex"}

    def test_check_unique_has_a_limit_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``limit 1`` 是 XML 里写死的，别丢 —— 撞上重复数据时也只取一条。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        entity = SysDictTypeMapper().check_dict_type_unique("sys_user_sex")

        assert entity is not None
        assert factory.statements[0].endswith("where dict_type = :dict_type limit 1")

    def test_check_unique_returns_none_when_free(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_TYPE_KEYS))
        _patch(monkeypatch, factory)

        assert SysDictTypeMapper().check_dict_type_unique("brand_new") is None


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_by_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        assert SysDictTypeMapper().delete_dict_type_by_id(4) == 1
        assert factory.statements[0] == "delete from sys_dict_type where dict_id = :dict_id"
        assert factory.params[0] == {"dict_id": 4}

    def test_delete_by_ids_builds_an_in_clause(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=3))
        _patch(monkeypatch, factory)

        assert SysDictTypeMapper().delete_dict_type_by_ids([1, 2, 3]) == 3
        assert factory.statements[0] == (
            "delete from sys_dict_type where dict_id in (:p0, :p1, :p2)"
        )
        assert factory.params[0] == {"p0": 1, "p1": 2, "p2": 3}

    def test_an_empty_id_array_produces_an_invalid_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<foreach>`` 空集合 -> ``in ()`` -> MySQL 语法错（Java 一样）。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().delete_dict_type_by_ids([])

        assert factory.statements[0].endswith("where dict_id in ()")


# --------------------------------------------------------------------------- insert


class TestInsertDictType:
    def test_create_time_is_always_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().insert_dict_type(SysDictType(dict_name="用户性别"))

        statement = factory.statements[0]
        assert statement.startswith("insert into sys_dict_type(dict_name,create_time)")
        assert statement.endswith("values(:dict_name,sysdate())")

    def test_the_generated_key_is_not_written_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """XML 里**没有** ``useGeneratedKeys`` —— ``dictId`` 插入后仍是 ``None``。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)
        entity = SysDictType(dict_name="用户性别")

        SysDictTypeMapper().insert_dict_type(entity)

        assert entity.dict_id is None

    def test_the_incoming_id_is_dropped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``insertDictType`` 没有 ``dict_id`` 的 ``<if>``。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().insert_dict_type(SysDictType(dict_id=99, dict_name="用户性别"))

        assert "dict_id" not in factory.statements[0]

    def test_text_columns_drop_the_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``dict_name`` / ``dict_type`` / ``remark`` / ``create_by`` 判 ``!= null and != ''``。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().insert_dict_type(
            SysDictType(dict_name="", dict_type="", remark="", create_by="")
        )

        assert factory.statements[0] == "insert into sys_dict_type(create_time)values(sysdate())"

    def test_status_keeps_the_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``status`` 只判 ``!= null`` —— 空串会照写（数据库里是空状态，不是默认值）。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().insert_dict_type(SysDictType(status=""))

        assert "status" in factory.statements[0]
        assert factory.params[0] == {"status": ""}

    def test_a_zero_status_is_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().insert_dict_type(SysDictType(status="1"))

        assert factory.params[0] == {"status": "1"}


# --------------------------------------------------------------------------- update


class TestUpdateDictType:
    def test_update_time_is_always_touched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().update_dict_type(SysDictType(dict_id=1))

        assert factory.statements[0] == (
            "update sys_dict_type set update_time = sysdate() where dict_id = :dict_id"
        )
        assert factory.params[0] == {"dict_id": 1}

    def test_the_set_order_matches_the_xml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().update_dict_type(
            SysDictType(
                dict_id=1,
                dict_name="用户性别",
                dict_type="sys_user_sex",
                status="0",
                remark="备注",
                update_by="admin",
            )
        )

        statement = factory.statements[0]
        expected_order = ["dict_name", "dict_type", "status", "remark", "update_by", "update_time"]
        positions = [statement.index(f"{column} =") for column in expected_order]
        assert positions == sorted(positions)
        assert statement.endswith("where dict_id = :dict_id")

    def test_create_by_is_not_updatable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<set>`` 里没有 ``create_by`` / ``create_time``。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().update_dict_type(
            SysDictType(dict_id=1, create_by="someone", create_time=None)
        )

        statement = factory.statements[0]
        assert "create_by" not in statement
        assert "create_time" not in statement

    def test_the_text_columns_drop_empty_but_status_and_remark_keep_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<set>`` 的判据与 insert **不一致**：``remark`` 只判 ``!= null``。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictTypeMapper().update_dict_type(
            SysDictType(dict_id=1, dict_name="", dict_type="", update_by="", status="", remark="")
        )

        statement = factory.statements[0]
        assert "dict_name = :dict_name" not in statement
        assert "dict_type = :dict_type" not in statement
        assert "update_by = :update_by" not in statement
        assert "status = :status" in statement
        assert "remark = :remark" in statement
        assert factory.params[0] == {"status": "", "remark": "", "dict_id": 1}


# --------------------------------------------------------------------------- 常量


def test_the_vo_projection_has_exactly_seven_columns() -> None:
    """``selectDictTypeVo`` 是四条查询的共同前提，别随手加列。"""
    columns = " ".join(SELECT_DICT_TYPE_VO.split()).split("from sys_dict_type")[0]
    for expected in _TYPE_KEYS:
        assert expected in columns
    assert "update_by" not in columns
    assert "update_time" not in columns
