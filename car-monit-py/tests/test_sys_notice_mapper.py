"""``SysNoticeMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysNoticeMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysNoticeMapper.java

为什么要对**拼出来的 SQL** 断言
------------------------------
公告的 CRUD 一旦接上假 Mapper，SQL 就全被遮住了，而这里有五处改错了**不会报错**、
只会悄悄换结果集：

* ``<where>`` 的 8 个 ``<if>`` 分**三类判据**：大多数是 ``!= null and != ''``，
  但 ``createBy`` 与 ``tenantId`` 只有 ``!= null`` —— 传空串照样过滤；
* ``tenantId`` 那一条还带写死的兜底 ``or t.TENANT_ID = 100``；
* ``insertNotice`` 的 ``<if>`` 判据与 ``updateNotice`` 的 ``<set>`` 判据**不一致**：
  ``buss_id`` 在 insert 里只判 ``!= null``，在 update 里判 ``!= null and != ''``；
* ``insertNotice`` **没有** ``notice_id`` 的 ``<if>`` —— 入参 id 会被丢弃；
* ``notice_content`` 在投影里是 ``cast(... as char)``，在条件里是等值 ``=``（不是 like）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.system.domain.sys_notice import SysNotice
from app.system.mapper.sys_notice_mapper import SELECT_NOTICE_VO, SysNoticeMapper

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


#: ``SysNoticeResult`` 的 13 列，顺序与 ``selectNoticeVo`` 一致。
_NOTICE_KEYS: Sequence[str] = (
    "notice_id",
    "notice_title",
    "notice_type",
    "notice_content",
    "status",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "remark",
    "buss_id",
    "buss_name",
    "tenant_id",
)


def _row(notice_id: int = 1) -> tuple:
    return (
        notice_id,
        "系统升级公告",
        "1",
        "<p>内容</p>",
        "0",
        "1",
        None,
        "1",
        None,
        None,
        "100",
        "张三",
        100,
    )


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_notice_mapper

    monkeypatch.setattr(sys_notice_mapper, "session_scope", factory)


# --------------------------------------------------------------------------- selectNoticeList


class TestSelectNoticeList:
    def test_without_filters_there_is_no_where_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """8 个 ``<if>`` 都不命中时 ``<where>`` 不产出内容，但 ``order by`` 仍在。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        rows = SysNoticeMapper().select_notice_list(SysNotice())

        assert [row.notice_id for row in rows] == [1]
        statement = factory.statements[0]
        assert " from sys_notice t" in statement
        assert "where" not in statement.lower()
        assert statement.endswith("order by t.create_time desc")

    def test_the_projection_casts_notice_content(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``cast(t.notice_content as char) as notice_content`` —— 照抄，别"简化"。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        SysNoticeMapper().select_notice_list(SysNotice())

        assert "cast(t.notice_content as char) as notice_content" in factory.statements[0]

    def test_the_eight_filters_keep_the_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``title`` -> ``type`` -> ``createBy`` -> ``status`` -> ``buss*`` -> ``tenant`` -> ``content``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        SysNoticeMapper().select_notice_list(
            SysNotice(
                notice_title="升级",
                notice_type="1",
                create_by="1",
                status="0",
                buss_id="100",
                buss_name="张三",
                tenant_id=100,
                notice_content="<p>内容</p>",
            )
        )

        statement = factory.statements[0]
        expected = [
            "t.notice_title like concat('%', :notice_title, '%')",
            "t.notice_type = :notice_type",
            "t.create_by = :create_by",
            "t.status = :status",
            "t.buss_id = :buss_id",
            "t.buss_name like concat('%', :buss_name, '%')",
            "(t.TENANT_ID = :tenant_id or t.TENANT_ID = 100)",
            "(t.notice_content = :notice_content)",
        ]
        positions = [statement.lower().index(fragment.lower()) for fragment in expected]
        assert positions == sorted(positions)
        assert factory.params[0] == {
            "notice_title": "升级",
            "notice_type": "1",
            "create_by": "1",
            "status": "0",
            "buss_id": "100",
            "buss_name": "张三",
            "tenant_id": 100,
            "notice_content": "<p>内容</p>",
        }

    def test_the_where_clause_does_not_start_with_and(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<where>`` 会吃掉首个 ``AND``；拼出 ``where AND a`` 就是 SQL 语法错。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        SysNoticeMapper().select_notice_list(
            SysNotice(notice_title="升级", notice_type="1")
        )

        statement = factory.statements[0]
        assert "where and" not in statement.lower()
        assert "where t.notice_title like" in statement
        assert " and t.notice_type = :notice_type" in statement

    def test_notice_content_filter_is_equality_not_like(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``noticeContent`` 是整段富文本，用**等值**匹配；``like`` 会变成全表扫。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        SysNoticeMapper().select_notice_list(SysNotice(notice_content="abc"))

        statement = factory.statements[0]
        assert "(t.notice_content = :notice_content)" in statement
        assert "notice_content like" not in statement

    def test_text_only_filters_skip_the_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``noticeTitle`` 等判据是 ``!= null and != ''``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        SysNoticeMapper().select_notice_list(
            SysNotice(notice_title="", notice_type="", status="", buss_id="", buss_name="")
        )

        statement = factory.statements[0]
        assert "where" not in statement.lower()

    def test_create_by_and_tenant_id_still_filter_on_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """这两条的判据**只有** ``!= null`` —— 空串也算"有值"，条件照样生效。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        SysNoticeMapper().select_notice_list(SysNotice(create_by="", tenant_id=0))

        statement = factory.statements[0]
        assert "t.create_by = :create_by" in statement
        assert "(t.TENANT_ID = :tenant_id or t.TENANT_ID = 100)" in statement
        assert factory.params[0] == {"create_by": "", "tenant_id": 0}

    def test_a_single_space_still_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """判据是 ``!= ''`` 而不是 ``isBlank``，所以 ``" "`` 会真的去 like。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        SysNoticeMapper().select_notice_list(SysNotice(notice_title=" "))

        assert "t.notice_title like concat('%', :notice_title, '%')" in factory.statements[0]

    def test_the_tenant_fallback_is_hard_coded_to_100(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``or t.TENANT_ID = 100`` 是写死的"公共租户"，不是参数。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        SysNoticeMapper().select_notice_list(SysNotice(tenant_id=7))

        statement = factory.statements[0]
        assert "or t.TENANT_ID = 100" in statement
        assert factory.params[0] == {"tenant_id": 7}

    def test_after_start_page_the_count_wraps_the_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PageHelper: ``count = select count(0) from (<原语句>) table_count``，再 ``LIMIT``。"""
        factory = _SessionFactory(
            _Result(scalar_value=7),
            _Result(rows=[_row()], keys=_NOTICE_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()

        rows = SysNoticeMapper().select_notice_list(SysNotice(status="0"))

        assert isinstance(rows, PageList)
        assert rows.total == 7
        count_statement, data_statement = factory.statements
        assert count_statement.startswith("select count(0) from (")
        assert count_statement.endswith(") table_count")
        # LIMIT 追加在语句自带的 order by 之后
        assert data_statement.endswith("order by t.create_time desc LIMIT 0, 10")

    def test_the_page_is_consumed_by_the_first_select(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``take_page`` 取一次就清空，与 PageHelper 一致。"""
        factory = _SessionFactory(
            _Result(scalar_value=1),
            _Result(rows=[_row()], keys=_NOTICE_KEYS),
            _Result(rows=[_row()], keys=_NOTICE_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()
        mapper = SysNoticeMapper()

        mapper.select_notice_list(SysNotice())
        mapper.select_notice_list(SysNotice())

        assert "LIMIT" in factory.statements[1]
        assert "LIMIT" not in factory.statements[2]

    def test_without_start_page_nothing_is_paginated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``addDeliveryTimeAbnormal`` 走的正是这条路径：没有 ``startPage()``。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        rows = SysNoticeMapper().select_notice_list(SysNotice(buss_id="9"))

        assert isinstance(rows, PageList)
        assert rows.total == 1
        assert "LIMIT" not in factory.statements[0]
        assert factory.statements[0].endswith("order by t.create_time desc")


# --------------------------------------------------------------------------- 单行查询


class TestSelectNoticeById:
    def test_all_thirteen_columns_are_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row(3)], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        notice = SysNoticeMapper().select_notice_by_id(3)

        assert notice is not None
        assert notice.notice_id == 3
        assert notice.notice_title == "系统升级公告"
        assert notice.notice_content == "<p>内容</p>"
        assert notice.tenant_id == 100
        assert factory.statements[0].endswith("where t.notice_id = :notice_id")
        assert factory.params[0] == {"notice_id": 3}

    def test_a_missing_row_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Java ``selectOne`` 无行时返回 ``null``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_NOTICE_KEYS))
        _patch(monkeypatch, factory)

        assert SysNoticeMapper().select_notice_by_id(404) is None


# --------------------------------------------------------------------------- insertNotice


class TestInsertNotice:
    def test_create_time_is_always_written(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)

        SysNoticeMapper().insert_notice(SysNotice(notice_title="标题", notice_type="1"))

        statement = factory.statements[0]
        assert statement.startswith("insert into sys_notice (notice_title,notice_type,create_time)")
        assert statement.endswith("values (:notice_title,:notice_type,sysdate())")

    def test_the_generated_key_is_written_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``useGeneratedKeys="true" keyProperty="noticeId"``。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=11))
        _patch(monkeypatch, factory)
        notice = SysNotice(notice_title="标题")

        SysNoticeMapper().insert_notice(notice)

        assert notice.notice_id == 11

    def test_the_incoming_id_is_dropped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """与 ``sys_post`` 不同：**没有** ``notice_id`` 的 ``<if>``，入参 id 会被丢弃。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=5))
        _patch(monkeypatch, factory)
        notice = SysNotice(notice_id=99, notice_title="标题")

        SysNoticeMapper().insert_notice(notice)

        assert "notice_id" not in factory.statements[0]
        assert notice.notice_id == 5

    def test_buss_and_tenant_columns_keep_the_empty_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``bussId`` / ``bussName`` / ``tenantId`` 的判据只有 ``!= null``。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=1))
        _patch(monkeypatch, factory)

        SysNoticeMapper().insert_notice(SysNotice(buss_id="", buss_name="", tenant_id=0))

        statement = factory.statements[0]
        assert "buss_id" in statement
        assert "buss_name" in statement
        assert "tenant_id" in statement
        assert factory.params[0] == {"buss_id": "", "buss_name": "", "tenant_id": 0}

    def test_text_columns_drop_the_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``notice_title`` / ``notice_type`` / ``status`` / ``remark`` 判 ``!= null and != ''``。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=1))
        _patch(monkeypatch, factory)

        SysNoticeMapper().insert_notice(
            SysNotice(notice_title="", notice_type="", status="", remark="")
        )

        statement = factory.statements[0]
        assert "notice_title" not in statement
        assert "notice_type" not in statement
        assert "status" not in statement
        assert "remark" not in statement
        assert statement == "insert into sys_notice (create_time) values (sysdate())"

    def test_notice_content_follows_the_text_rule_in_insert(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``noticeContent`` 在 insert 里判 ``!= null and != ''``（与 update 相反）。"""
        factory = _SessionFactory(
            _Result(rowcount=1, lastrowid=1),
            _Result(rowcount=1, lastrowid=2),
        )
        _patch(monkeypatch, factory)
        mapper = SysNoticeMapper()

        mapper.insert_notice(SysNotice(notice_content=""))
        mapper.insert_notice(SysNotice(notice_content="<p>x</p>"))

        assert "notice_content" not in factory.statements[0]
        assert "notice_content" in factory.statements[1]
        assert factory.params[1] == {"notice_content": "<p>x</p>"}


# --------------------------------------------------------------------------- updateNotice


class TestUpdateNotice:
    def test_update_time_is_always_touched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysNoticeMapper().update_notice(SysNotice(notice_id=1))

        assert factory.statements[0] == (
            "update sys_notice set update_time = sysdate() where notice_id = :notice_id"
        )

    def test_the_set_order_matches_the_xml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysNoticeMapper().update_notice(
            SysNotice(
                notice_id=1,
                notice_title="标题",
                notice_type="1",
                notice_content="<p>x</p>",
                status="0",
                update_by="1",
                buss_id="100",
                buss_name="张三",
            )
        )

        statement = factory.statements[0]
        expected_order = [
            "notice_title",
            "notice_type",
            "notice_content",
            "status",
            "update_by",
            "buss_id",
            "buss_name",
            "update_time",
        ]
        positions = [statement.index(f"{column} =") for column in expected_order]
        assert positions == sorted(positions)
        assert statement.endswith("where notice_id = :notice_id")

    def test_tenant_id_is_not_updatable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<set>`` 里**没有** ``tenant_id`` —— 改公告不会改租户。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysNoticeMapper().update_notice(SysNotice(notice_id=1, tenant_id=777))

        statement = factory.statements[0]
        assert "tenant_id" not in statement
        assert "tenant_id" not in factory.params[0]

    def test_notice_content_survives_an_empty_string_but_titles_do_not(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``notice_content`` 只判 ``!= null``，其余文本列判 ``!= null and != ''``。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysNoticeMapper().update_notice(
            SysNotice(notice_id=1, notice_title="", notice_type="", status="", notice_content="")
        )

        statement = factory.statements[0]
        assert "notice_title" not in statement
        assert "notice_type" not in statement
        assert "status" not in statement
        assert "notice_content = :notice_content" in statement
        assert factory.params[0]["notice_content"] == ""

    def test_buss_columns_drop_the_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """与 insert 相反的**不对称**：update 里 ``buss_id`` 会跳过空串。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysNoticeMapper().update_notice(SysNotice(notice_id=1, buss_id="", buss_name=""))

        assert "buss_id" not in factory.statements[0]
        assert "buss_name" not in factory.statements[0]


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_notice_by_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        assert SysNoticeMapper().delete_notice_by_id(4) == 1
        assert factory.statements[0] == "delete from sys_notice where notice_id = :notice_id"
        assert factory.params[0] == {"notice_id": 4}

    def test_delete_notice_by_ids_builds_an_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=3))
        _patch(monkeypatch, factory)

        assert SysNoticeMapper().delete_notice_by_ids([1, 2, 3]) == 3
        assert factory.statements[0] == "delete from sys_notice where notice_id in (:p0, :p1, :p2)"
        assert factory.params[0] == {"p0": 1, "p1": 2, "p2": 3}


# --------------------------------------------------------------------------- 常量


def test_the_vo_projection_has_exactly_thirteen_columns() -> None:
    """``selectNoticeVo`` 是两条查询的共同前提，别随手加列。"""
    columns = " ".join(SELECT_NOTICE_VO.split()).split("from sys_notice")[0]
    for expected in _NOTICE_KEYS:
        assert expected in columns
    # ``params`` / ``searchValue`` 不参与投影，只由请求参数填
    assert "params" not in columns
    assert "search_value" not in columns
