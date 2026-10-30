"""``SysDictDataMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/SysDictDataMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDictDataMapper.java

这一层为什么值钱
----------------
字典数据是所有下拉框的数据源，SQL 一旦被假 Mapper 遮住，下面这些地方改错了**不会
报错**：

1. ``selectDictDataByType`` 里 ``status = '0'`` 是**写死**的 —— 停用项不进缓存。
   ``selectDictDataList`` 则完全不过滤状态（管理页面要看到停用项）。
2. ``selectDictDataByTypeMore`` 的集合表达式是 OGNL 的 ``dictTypes.split(',')``，
   Java 的 ``split`` **丢弃尾部空串**：``"a,b,"`` -> ``["a","b"]``。用 Python 的
   ``str.split`` 会多一个 ``""``，于是 ``in ('a','b','')``。
3. ``selectDictLabel`` **没有** ``limit 1``，撞上重复数据时 MyBatis 的 ``selectOne``
   抛 ``TooManyResultsException``（500）。Python 侧显式抛同样的异常，别"取第一行"。
4. ``insertDictData`` 同样**没有** ``useGeneratedKeys``，插入后 ``dictCode`` 仍是
   ``null``。
5. ``insertDictData`` 的 ``<if>`` 判据与 ``updateDictData`` 的 ``<set>`` 判据**不一致**：
   ``css_class`` / ``list_class`` / ``remark`` 在 insert 里判 ``!= null and != ''``，
   在 update 里只判 ``!= null``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.system.mapper.sys_dict_data_mapper import SELECT_DICT_DATA_VO, SysDictDataMapper

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


#: ``selectDictDataVo`` 的 12 列，顺序与 XML 一致。
_DATA_KEYS: Sequence[str] = (
    "dict_code",
    "dict_sort",
    "dict_label",
    "dict_value",
    "dict_type",
    "css_class",
    "list_class",
    "is_default",
    "status",
    "create_by",
    "create_time",
    "remark",
)


def _row(dict_code: int = 1) -> tuple:
    return (
        dict_code,
        1,
        "男",
        "0",
        "sys_user_sex",
        None,
        "default",
        "Y",
        "0",
        "admin",
        None,
        "备注",
    )


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_dict_data_mapper

    monkeypatch.setattr(sys_dict_data_mapper, "session_scope", factory)


# --------------------------------------------------------------------------- selectDictDataList


class TestSelectDictDataList:
    def test_without_filters_there_is_no_where_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        rows = SysDictDataMapper().select_dict_data_list(SysDictData())

        assert [row.dict_code for row in rows] == [1]
        statement = factory.statements[0]
        assert " from sys_dict_data" in statement
        assert "where" not in statement.lower()
        assert statement.endswith("order by dict_sort asc")

    def test_the_three_filters_keep_the_xml_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``dictType``（等值）-> ``dictLabel``（like）-> ``status``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_list(
            SysDictData(dict_type="sys_user_sex", dict_label="男", status="0")
        )

        statement = factory.statements[0]
        expected = [
            "dict_type = :dict_type",
            "dict_label like concat('%', :dict_label, '%')",
            "status = :status",
        ]
        positions = [statement.index(fragment) for fragment in expected]
        assert positions == sorted(positions)
        assert factory.params[0] == {
            "dict_type": "sys_user_sex",
            "dict_label": "男",
            "status": "0",
        }

    def test_the_list_does_not_filter_the_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """管理页面要看到停用项 —— 只有传了 ``status`` 才过滤。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_list(SysDictData(dict_type="sys_user_sex"))

        assert "status = :status" not in factory.statements[0]

    def test_a_single_space_still_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_list(SysDictData(dict_label=" "))

        assert "dict_label like concat('%', :dict_label, '%')" in factory.statements[0]

    def test_the_where_clause_does_not_start_with_and(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<where>`` 会吃掉首个 ``AND``；拼出 ``where AND a`` 就是 SQL 语法错。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_list(
            SysDictData(dict_type="sys_user_sex", dict_label="男")
        )

        statement = factory.statements[0]
        assert "where and" not in statement.lower()
        assert "where dict_type = :dict_type" in statement
        assert " and dict_label like" in statement

    def test_after_start_page_the_count_wraps_the_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(
            _Result(scalar_value=12),
            _Result(rows=[_row()], keys=_DATA_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()

        rows = SysDictDataMapper().select_dict_data_list(SysDictData(dict_type="sys_user_sex"))

        assert isinstance(rows, PageList)
        assert rows.total == 12
        count_statement, data_statement = factory.statements
        assert count_statement.startswith("select count(0) from (")
        assert data_statement.endswith("order by dict_sort asc LIMIT 0, 10")

    def test_without_start_page_nothing_is_paginated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``selectDictDataMap`` / ``selectDictDataLaleMap`` 走的正是这条路径。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        rows = SysDictDataMapper().select_dict_data_list(SysDictData(dict_type="sys_user_sex"))

        assert isinstance(rows, PageList)
        assert "LIMIT" not in factory.statements[0]


# --------------------------------------------------------------------------- selectDictDataByType


class TestSelectDictDataByType:
    def test_only_enabled_rows_are_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``status = '0'`` 是写死的：停用项不会进缓存，也就不会出现在下拉框。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_by_type("sys_user_sex")

        statement = factory.statements[0]
        assert "where status = '0' and dict_type = :dict_type" in statement
        assert statement.endswith("order by dict_sort asc")
        assert factory.params[0] == {"dict_type": "sys_user_sex"}

    def test_the_result_is_ordered_by_dict_sort(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_by_type("sys_user_sex")

        assert factory.statements[0].endswith("order by dict_sort asc")

    def test_it_is_never_paginated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """缓存回源不分页 —— 即便前台留着 ``startPage()`` 也不该吃掉它。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)
        start_page()

        SysDictDataMapper().select_dict_data_by_type("sys_user_sex")

        assert "LIMIT" not in factory.statements[0]

    def test_all_twelve_columns_are_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row(7)], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        items = SysDictDataMapper().select_dict_data_by_type("sys_user_sex")

        item = items[0]
        assert item.dict_code == 7
        assert item.dict_sort == 1
        assert item.dict_label == "男"
        assert item.dict_value == "0"
        assert item.dict_type == "sys_user_sex"
        assert item.list_class == "default"
        assert item.is_default == "Y"
        assert item.status == "0"
        assert item.remark == "备注"

    def test_an_empty_result_is_an_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MyBatis 的 ``selectList`` 永远返回 List（不返回 null）。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().select_dict_data_by_type("unknown") == []


# --------------------------------------------------------------------------- selectDictDataByTypeMore


class TestSelectDictDataByTypeMore:
    def test_the_types_are_split_into_an_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_by_type_more("car_type,plate_color")

        statement = factory.statements[0]
        assert "where status = '0' and dict_type in (:t0, :t1)" in statement
        assert statement.endswith("order by dict_type,dict_sort asc")
        assert factory.params[0] == {"t0": "car_type", "t1": "plate_color"}

    def test_a_trailing_comma_is_dropped_like_java_split(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java ``"a,b,".split(",")`` -> ``["a","b"]``；多了个 ``""`` 就查不到东西。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_by_type_more("car_type,plate_color,")

        assert factory.params[0] == {"t0": "car_type", "t1": "plate_color"}

    def test_a_single_type_still_uses_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_by_type_more("car_type")

        assert "dict_type in (:t0)" in factory.statements[0]

    def test_a_lone_comma_produces_an_invalid_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``",".split(",")`` 在 Java 里是长度 0 的数组 -> ``in ()`` -> MySQL 语法错。"""
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_data_by_type_more(",")

        assert "dict_type in ()" in factory.statements[0]
        assert factory.params[0] == {}

    def test_none_raises_like_the_ognl_npe(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``dictTypes.split(',')`` 对 null 调方法 -> NullPointerException -> 500。"""
        factory = _SessionFactory()
        _patch(monkeypatch, factory)

        with pytest.raises(AttributeError) as error:
            SysDictDataMapper().select_dict_data_by_type_more(None)

        assert "NullPointerException" in str(error.value)
        assert factory.statements == []


# --------------------------------------------------------------------------- selectDictLabel


class TestSelectDictLabel:
    def test_a_hit_returns_the_label(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[("男",)]))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().select_dict_label("sys_user_sex", "0") == "男"
        assert factory.params[0] == {"dict_type": "sys_user_sex", "dict_value": "0"}

    def test_there_is_no_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """XML 里没有 ``limit 1``，这正是 ``TooManyResultsException`` 的来源。"""
        factory = _SessionFactory(_Result(rows=[("男",)]))
        _patch(monkeypatch, factory)

        SysDictDataMapper().select_dict_label("sys_user_sex", "0")

        assert "limit" not in factory.statements[0].lower()

    def test_a_miss_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().select_dict_label("sys_user_sex", "9") is None

    def test_two_rows_raise_too_many_results(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """同一 ``(type, value)`` 两条数据时 Java 抛异常 -> HTTP 500，这里同样抛。"""
        factory = _SessionFactory(_Result(rows=[("男",), ("男性",)]))
        _patch(monkeypatch, factory)

        with pytest.raises(AttributeError) as error:
            SysDictDataMapper().select_dict_label("sys_user_sex", "0")

        assert "TooManyResultsException" in str(error.value)
        assert "found: 2" in str(error.value)


# --------------------------------------------------------------------------- 其它单行查询


class TestOtherSelects:
    def test_select_by_id_maps_the_row(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row(5)], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        item = SysDictDataMapper().select_dict_data_by_id(5)

        assert item is not None
        assert item.dict_code == 5
        assert factory.statements[0].endswith("where dict_code = :dict_code")
        assert factory.params[0] == {"dict_code": 5}

    def test_select_by_id_returns_none_when_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_DATA_KEYS))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().select_dict_data_by_id(404) is None

    def test_count_by_type_ignores_the_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """删字典类型前的"是否已分配"判定 —— 停用项也算已分配。"""
        factory = _SessionFactory(_Result(scalar_value=3))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().count_dict_data_by_type("sys_user_sex") == 3
        statement = factory.statements[0]
        assert statement == "select count(1) from sys_dict_data where dict_type=:dict_type"
        assert "status" not in statement

    def test_count_with_a_null_scalar_is_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(scalar_value=None))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().count_dict_data_by_type("x") == 0


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_by_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().delete_dict_data_by_id(4) == 1
        assert factory.statements[0] == "delete from sys_dict_data where dict_code = :dict_code"

    def test_delete_by_ids_builds_an_in_clause(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().delete_dict_data_by_ids([8, 9]) == 2
        assert factory.statements[0] == (
            "delete from sys_dict_data where dict_code in (:p0, :p1)"
        )
        assert factory.params[0] == {"p0": 8, "p1": 9}

    def test_an_empty_id_array_produces_an_invalid_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysDictDataMapper().delete_dict_data_by_ids([])

        assert factory.statements[0].endswith("where dict_code in ()")


# --------------------------------------------------------------------------- insert


class TestInsertDictData:
    def test_create_time_is_always_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)

        SysDictDataMapper().insert_dict_data(SysDictData(dict_label="男"))

        statement = factory.statements[0]
        assert statement.startswith("insert into sys_dict_data(dict_label,create_time)")
        assert statement.endswith("values(:dict_label,sysdate())")

    def test_the_generated_key_is_not_written_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """XML 里**没有** ``useGeneratedKeys`` —— ``dictCode`` 插入后仍是 ``None``。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)
        item = SysDictData(dict_label="男")

        SysDictDataMapper().insert_dict_data(item)

        assert item.dict_code is None

    def test_the_incoming_code_is_dropped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().insert_dict_data(SysDictData(dict_code=99, dict_label="男"))

        assert "dict_code" not in factory.statements[0]

    def test_text_columns_drop_the_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().insert_dict_data(
            SysDictData(
                dict_label="",
                dict_value="",
                dict_type="",
                css_class="",
                list_class="",
                is_default="",
                remark="",
                create_by="",
            )
        )

        assert factory.statements[0] == "insert into sys_dict_data(create_time)values(sysdate())"

    def test_sort_and_status_keep_their_zero_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``dict_sort`` / ``status`` 只判 ``!= null``；``0`` 不是空串。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().insert_dict_data(SysDictData(dict_sort=0, status="0"))

        statement = factory.statements[0]
        assert "dict_sort" in statement
        assert "status" in statement
        assert factory.params[0] == {"dict_sort": 0, "status": "0"}

    def test_an_empty_status_is_still_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().insert_dict_data(SysDictData(status=""))

        assert "status" in factory.statements[0]
        assert factory.params[0] == {"status": ""}

    def test_the_column_order_matches_the_xml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().insert_dict_data(
            SysDictData(
                dict_sort=2,
                dict_label="女",
                dict_value="1",
                dict_type="sys_user_sex",
                css_class="c",
                list_class="l",
                is_default="N",
                status="0",
                remark="r",
                create_by="admin",
            )
        )

        statement = factory.statements[0]
        expected = [
            "dict_sort",
            "dict_label",
            "dict_value",
            "dict_type",
            "css_class",
            "list_class",
            "is_default",
            "status",
            "remark",
            "create_by",
            "create_time",
        ]
        positions = [statement.index(column) for column in expected]
        assert positions == sorted(positions)


# --------------------------------------------------------------------------- update


class TestUpdateDictData:
    def test_update_time_is_always_touched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().update_dict_data(SysDictData(dict_code=1))

        assert factory.statements[0] == (
            "update sys_dict_data set update_time = sysdate() where dict_code = :dict_code"
        )
        assert factory.params[0] == {"dict_code": 1}

    def test_the_set_order_matches_the_xml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().update_dict_data(
            SysDictData(
                dict_code=1,
                dict_sort=2,
                dict_label="女",
                dict_value="1",
                dict_type="sys_user_sex",
                css_class="c",
                list_class="l",
                is_default="N",
                status="0",
                remark="r",
                update_by="admin",
            )
        )

        statement = factory.statements[0]
        expected_order = [
            "dict_sort",
            "dict_label",
            "dict_value",
            "dict_type",
            "css_class",
            "list_class",
            "is_default",
            "status",
            "remark",
            "update_by",
            "update_time",
        ]
        positions = [statement.index(f"{column} =") for column in expected_order]
        assert positions == sorted(positions)
        assert statement.endswith("where dict_code = :dict_code")

    def test_create_by_is_not_updatable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().update_dict_data(SysDictData(dict_code=1, create_by="someone"))

        assert "create_by" not in factory.statements[0]

    def test_the_set_keeps_empty_lists_and_classes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``css_class`` / ``list_class`` / ``status`` / ``remark`` 在 update 里只判 ``!= null``。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().update_dict_data(
            SysDictData(
                dict_code=1,
                css_class="",
                list_class="",
                status="",
                remark="",
            )
        )

        statement = factory.statements[0]
        assert "css_class = :css_class" in statement
        assert "list_class = :list_class" in statement
        assert "status = :status" in statement
        assert "remark = :remark" in statement
        assert factory.params[0] == {
            "css_class": "",
            "list_class": "",
            "status": "",
            "remark": "",
            "dict_code": 1,
        }

    def test_the_set_drops_empty_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``dict_label`` / ``dict_value`` / ``dict_type`` / ``is_default`` / ``update_by``。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysDictDataMapper().update_dict_data(
            SysDictData(dict_code=1, dict_label="", dict_value="", dict_type="", update_by="")
        )

        statement = factory.statements[0]
        assert "dict_label = :dict_label" not in statement
        assert "dict_value = :dict_value" not in statement
        assert "dict_type = :dict_type" not in statement
        assert "update_by = :update_by" not in statement

    def test_update_dict_data_type_renames_every_child(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """改类型名时同步子表 —— ``updateDictType`` 的一致性来源。"""
        factory = _SessionFactory(_Result(rowcount=5))
        _patch(monkeypatch, factory)

        assert SysDictDataMapper().update_dict_data_type("old_type", "new_type") == 5
        assert factory.statements[0] == (
            "update sys_dict_data set dict_type = :new_dict_type where dict_type = :old_dict_type"
        )
        assert factory.params[0] == {"old_dict_type": "old_type", "new_dict_type": "new_type"}


# --------------------------------------------------------------------------- 常量


def test_the_vo_projection_has_exactly_twelve_columns() -> None:
    """``selectDictDataVo`` 是四条查询的共同前提，别随手加列。"""
    columns = " ".join(SELECT_DICT_DATA_VO.split()).split("from sys_dict_data")[0]
    for expected in _DATA_KEYS:
        assert expected in columns
    assert "update_by" not in columns
    assert "update_time" not in columns
