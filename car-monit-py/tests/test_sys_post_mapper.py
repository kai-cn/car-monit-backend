"""``SysPostMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysPostMapper.java

为什么要对**拼出来的 SQL** 断言
------------------------------
岗位 CRUD 的假 Mapper 会把 SQL 全遮住，而这里有四个地方改错了不会报错、只会换结果集：

* ``<where>`` 的三个 ``<if>`` 用的是 ``!= null and != ''``（**不是** ``isBlank``），
  顺序是 ``post_code`` -> ``status`` -> ``post_name``；
* ``insertPost`` 的 ``create_time`` 是**无条件**列（``sysdate()``），其余列各有条件，
  ``post_id`` 的判据还多一个 ``!= 0``；
* ``updatePost`` 的 ``update_time = sysdate()`` 无条件，但 ``remark`` 只有 ``!= null``
  —— 所以空串 ``""`` **会**被写进去，和 ``post_code`` 之类的处理不同；
* ``checkPostNameUnique`` / ``checkPostCodeUnique`` 带 ``limit 1``，而 ``selectPostVo``
  不 select ``update_by`` / ``update_time``（这两列永远映射成 ``None``）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.system.domain.sys_post import SysPost
from app.system.mapper.sys_post_mapper import SysPostMapper, SELECT_POST_VO

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


#: ``selectPostVo`` 的列标签，顺序与 XML 一致。
_POST_KEYS: Sequence[str] = (
    "post_id",
    "post_code",
    "post_name",
    "post_sort",
    "status",
    "create_by",
    "create_time",
    "remark",
)

#: ``selectPostsByUserName`` 只 select 三列。
_POST_KEYS_BY_USER_NAME: Sequence[str] = ("post_id", "post_name", "post_code")


def _row(post_id: int = 1, post_code: str = "ceo", post_name: str = "董事长") -> tuple:
    return (post_id, post_code, post_name, "1", "0", "admin", None, None)


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_post_mapper

    monkeypatch.setattr(sys_post_mapper, "session_scope", factory)


# --------------------------------------------------------------------------- selectPostList


class TestSelectPostList:
    def test_without_filters_there_is_no_where_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """三个 ``<if>`` 都不命中时，``<where>`` 标签不产出任何内容。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        rows = SysPostMapper().select_post_list(SysPost())

        assert [row.post_id for row in rows] == [1]
        statement = factory.statements[0]
        assert statement.startswith("select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark")
        assert " from sys_post" in statement
        assert "where" not in statement.lower()

    def test_the_three_filters_keep_the_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``post_code`` -> ``status`` -> ``post_name``，用 ``and`` 连接。"""
        factory = _SessionFactory(_Result(rows=[], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        SysPostMapper().select_post_list(SysPost(post_code="ce", status="0", post_name="董事"))

        statement = factory.statements[0]
        assert (
            "where post_code like concat('%', :post_code, '%') "
            "and status = :status "
            "and post_name like concat('%', :post_name, '%')"
        ) in statement
        # 顺序不能变：换顺序不会报错，只是索引选择不同、结果集一样
        where_part = statement[statement.index("where ") :]
        assert (
            where_part.index("post_code like")
            < where_part.index("status = :status")
            < where_part.index("post_name like")
        )
        assert factory.params[0] == {"post_code": "ce", "status": "0", "post_name": "董事"}

    def test_empty_string_is_not_a_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Java: ``postCode != null and postCode != ''`` —— 空串不算条件。"""
        factory = _SessionFactory(_Result(rows=[], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        SysPostMapper().select_post_list(SysPost(post_code="", post_name=""))

        statement = factory.statements[0]
        assert "where" not in statement.lower()
        assert ":post_code" not in statement

    def test_a_single_space_still_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """判据是 ``!= ''`` 而不是 ``isBlank``，所以 ``" "`` 会真的去 like。"""
        factory = _SessionFactory(_Result(rows=[], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        SysPostMapper().select_post_list(SysPost(post_code=" "))

        assert "post_code like concat('%', :post_code, '%')" in factory.statements[0]
        assert factory.params[0] == {"post_code": " "}

    def test_after_start_page_the_count_wraps_the_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PageHelper: ``count = select count(0) from (<原语句>) table_count``，再 ``LIMIT``。"""
        factory = _SessionFactory(
            _Result(scalar_value=7),
            _Result(rows=[_row()], keys=_POST_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()

        rows = SysPostMapper().select_post_list(SysPost(status="0"))

        assert isinstance(rows, PageList)
        assert rows.total == 7
        count_statement, data_statement = factory.statements
        # SELECT_POST_VO 逐字照抄 XML，开头带一个换行，所以包进子查询后是 ``from ( <换行> select ...``。
        assert count_statement.startswith("select count(0) from (")
        assert "select post_id" in count_statement
        assert count_statement.endswith(") table_count")
        assert data_statement.endswith("LIMIT 0, 10")

    def test_the_page_is_consumed_by_the_first_select(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``take_page`` 取一次就清空，与 PageHelper 一致。"""
        factory = _SessionFactory(
            _Result(scalar_value=1),
            _Result(rows=[_row()], keys=_POST_KEYS),
            _Result(rows=[_row()], keys=_POST_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()
        mapper = SysPostMapper()

        mapper.select_post_list(SysPost())
        mapper.select_post_list(SysPost())

        assert "LIMIT" in factory.statements[1]
        assert "LIMIT" not in factory.statements[2]


# --------------------------------------------------------------------------- 单行查询


class TestSingleRowQueries:
    def test_select_post_by_id_maps_all_eight_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[_row(3)], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        post = SysPostMapper().select_post_by_id(3)

        assert post is not None
        assert (post.post_id, post.post_code, post.post_name) == (3, "ceo", "董事长")
        assert factory.statements[0].endswith("where post_id = :post_id")
        assert factory.params[0] == {"post_id": 3}

    def test_select_post_by_id_returns_none_for_a_missing_row(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java ``selectOne`` 无行时返回 ``null``，不是抛 ``TooManyResultsException``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        assert SysPostMapper().select_post_by_id(404) is None

    def test_update_by_and_update_time_are_never_selected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``selectPostVo`` 不 select 这两列 -> 永远 ``None``。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        post = SysPostMapper().select_post_by_id(1)

        assert post is not None
        assert post.update_by is None
        assert post.update_time is None

    def test_check_post_name_unique_uses_limit_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row(9)], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        post = SysPostMapper().check_post_name_unique("董事长")

        assert post is not None and post.post_id == 9
        assert factory.statements[0].endswith("where post_name=:post_name limit 1")
        assert factory.params[0] == {"post_name": "董事长"}

    def test_check_post_code_unique_uses_limit_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_POST_KEYS))
        _patch(monkeypatch, factory)

        assert SysPostMapper().check_post_code_unique("ceo") is None
        assert factory.statements[0].endswith("where post_code=:post_code limit 1")

    def test_select_posts_by_user_name_only_maps_three_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``resultMap`` + 三列投影 -> 其余字段全 ``None``。"""
        factory = _SessionFactory(
            _Result(rows=[(1, "董事长", "ceo")], keys=_POST_KEYS_BY_USER_NAME)
        )
        _patch(monkeypatch, factory)

        posts = SysPostMapper().select_posts_by_user_name("ry")

        assert len(posts) == 1
        assert posts[0].post_id == 1
        assert posts[0].post_name == "董事长"
        assert posts[0].status is None
        assert posts[0].create_by is None


# --------------------------------------------------------------------------- insertPost


class TestInsertPost:
    def test_create_time_is_always_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)

        SysPostMapper().insert_post(SysPost(post_code="ceo", post_name="董事长", post_sort="1"))

        statement = factory.statements[0]
        assert statement.startswith("insert into sys_post(post_code,post_name,post_sort,create_time)values")
        assert statement.endswith("(:post_code,:post_name,:post_sort,sysdate())")

    def test_the_generated_key_is_written_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``useGeneratedKeys="true" keyProperty="postId"``。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)
        post = SysPost(post_code="ceo", post_name="董事长", post_sort="1")

        SysPostMapper().insert_post(post)

        assert post.post_id == 11

    def test_empty_text_columns_are_dropped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``remark != null and remark != ''`` —— 空串不进屋。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)

        SysPostMapper().insert_post(
            SysPost(post_code="ceo", post_name="董事长", post_sort="1", status="", remark="")
        )

        statement = factory.statements[0]
        assert "status" not in statement
        assert "remark" not in statement

    def test_post_id_is_only_inserted_when_non_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Java: ``postId != null and postId != 0``。"""
        factory = _SessionFactory(
            _Result(rowcount=1, lastrowid=None),
            _Result(rowcount=1, lastrowid=None),
        )
        _patch(monkeypatch, factory)
        mapper = SysPostMapper()

        mapper.insert_post(SysPost(post_id=0, post_code="a", post_name="b", post_sort="1"))
        mapper.insert_post(SysPost(post_id=5, post_code="a", post_name="b", post_sort="1"))

        assert "post_id" not in factory.statements[0]
        assert factory.statements[1].startswith("insert into sys_post(post_id,post_code,post_name,post_sort,create_time)values")
        assert factory.params[1]["post_id"] == 5

    def test_create_by_is_written_when_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=1))
        _patch(monkeypatch, factory)

        SysPostMapper().insert_post(
            SysPost(post_code="a", post_name="b", post_sort="1", create_by="ry")
        )

        assert "create_by" in factory.statements[0]
        assert factory.params[0]["create_by"] == "ry"


# --------------------------------------------------------------------------- updatePost


class TestUpdatePost:
    def test_update_time_is_always_touched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysPostMapper().update_post(SysPost(post_id=1))

        assert factory.statements[0] == (
            "update sys_post set update_time = sysdate() where post_id = :post_id"
        )

    def test_the_set_order_matches_the_xml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysPostMapper().update_post(
            SysPost(
                post_id=1,
                post_code="ceo",
                post_name="董事长",
                post_sort="1",
                status="0",
                remark="r",
                update_by="ry",
            )
        )

        statement = factory.statements[0]
        expected_order = ["post_code", "post_name", "post_sort", "status", "remark", "update_by", "update_time"]
        positions = [statement.index(f"{column} =") for column in expected_order]
        assert positions == sorted(positions)
        assert statement.endswith("where post_id = :post_id")

    def test_empty_text_is_skipped_but_empty_remark_is_kept(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``remark`` 的条件只有 ``!= null``：空串照样写进去。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysPostMapper().update_post(
            SysPost(post_id=1, post_code="", post_name="", post_sort="", status="", remark="")
        )

        statement = factory.statements[0]
        assert "post_code" not in statement
        assert "post_name" not in statement
        assert "post_sort" not in statement
        assert "status" not in statement
        assert "remark = :remark" in statement
        assert factory.params[0]["remark"] == ""


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_post_by_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        assert SysPostMapper().delete_post_by_id(4) == 1
        assert factory.statements[0] == "delete from sys_post where post_id = :post_id"
        assert factory.params[0] == {"post_id": 4}

    def test_delete_post_by_ids_builds_an_in_clause(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=3))
        _patch(monkeypatch, factory)

        assert SysPostMapper().delete_post_by_ids([1, 2, 3]) == 3
        assert factory.statements[0] == "delete from sys_post where post_id in (:p0, :p1, :p2)"
        assert factory.params[0] == {"p0": 1, "p1": 2, "p2": 3}


# --------------------------------------------------------------------------- 常量


def test_the_vo_projection_has_exactly_eight_columns() -> None:
    """``selectPostVo`` 的列清单是五条 select 的共同前提，别随手加列。"""
    columns = " ".join(SELECT_POST_VO.split()).split("from sys_post")[0]
    for expected in ("post_id", "post_code", "post_name", "post_sort", "status", "create_by", "create_time", "remark"):
        assert expected in columns
    assert "update_by" not in columns
    assert "update_time" not in columns
