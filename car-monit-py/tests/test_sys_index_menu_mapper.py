"""``SysIndexMenuMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysIndexMenuMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysIndexMenuMapper.java

这一层为什么值钱
----------------
本模块的 SQL 有几个"改错了不报错、只悄悄换结果集"的地方：

1. ``selectSysIndexMenuList`` **不是单表查询**：``from sys_menu t1, sys_menu t2`` +
   三条硬编码 ``where`` 条件 + 两个 ``not exists`` + 一个 ``exists``。丢掉任何一个
   子查询都会让"可用菜单"变成"全部菜单"。
2. ``<if test="userId != 1 ">`` 是 OGNL 的 ``!=``，**不是** ``!= null`` ——
   ``userId == 1``（超管）要看所有人的菜单，条件必须**跳过**。
3. 这两条 select 都**自带** ``order by``，分页时不会追加客户端排序列。
4. ``insertSysIndexMenu`` / ``updateSysIndexMenu`` 的 ``<trim>`` 里**全部**是
   ``!= null`` —— 传 ``""`` 会**写进库**（与 ``sys_config`` 的 ``!= ''`` 相反）。
5. ``deleteSysIndexMenuById`` / ``ByIds`` 是**软删除**（``update ... set del_flag='1'``），
   只有 ``deleteByMenuUserId`` 是物理 ``delete from``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.system.domain.sys_index_menu import SysIndexMenu
from app.system.mapper.sys_index_menu_mapper import SysIndexMenuMapper

# --------------------------------------------------------------------------- fakes


class _Result:
    """One ``CursorResult``-shaped answer."""

    def __init__(
        self,
        rows: Optional[Sequence[Any]] = None,
        keys: Optional[Sequence[str]] = None,
        scalar_value: Any = None,
        rowcount: int = 0,
    ) -> None:
        self._rows = list(rows or [])
        self._keys = list(keys or [])
        self._scalar = scalar_value
        self.rowcount = rowcount

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


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_index_menu_mapper

    monkeypatch.setattr(sys_index_menu_mapper, "session_scope", factory)


@pytest.fixture(autouse=True)
def _clear_page_state() -> Any:
    clear_page()
    yield
    clear_page()


#: ``selectSysIndexMenuList`` 的投影列（``t2.menu_name as menuName2`` / ``t1.menu_id`` /
#: ``t1.menu_name``）。
_LIST_KEYS: Sequence[str] = ("menuName2", "menu_id", "menu_name")

#: ``selectSysIndexMenuVo`` 的 11 列，顺序与 XML 一致。
_VO_KEYS: Sequence[str] = (
    "ID",
    "USER_ID",
    "MENU_ID",
    "SORT",
    "EPS_ID",
    "DEL_FLAG",
    "CREATE_BY",
    "CREATE_TIME",
    "UPDATE_BY",
    "UPDATE_TIME",
    "TENANT_ID",
)

#: ``getList`` 的 3 列。
_MY_LIST_KEYS: Sequence[str] = ("id", "menu_name", "menuUrl")


# --------------------------------------------------------------------------- selectSysIndexMenuList


class TestSelectSysIndexMenuList:
    def _list(self, monkeypatch: pytest.MonkeyPatch, entity: SysIndexMenu) -> _SessionFactory:
        factory = _SessionFactory(_Result(rows=[], keys=_LIST_KEYS))
        _patch(monkeypatch, factory)
        SysIndexMenuMapper().select_sys_index_menu_list(entity)
        return factory

    def test_the_three_hardcoded_conditions_are_always_there(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._list(monkeypatch, SysIndexMenu(user_id=2)).statements[0]

        assert "select t2.menu_name as menuname2,t1.menu_id,t1.menu_name" in statement.lower()
        assert "from sys_menu t1, sys_menu t2" in statement.lower()
        assert "t1.menu_type='c'" in statement.lower()
        assert "t1.visible = '0'" in statement
        assert "t2.menu_id = t1.parent_id" in statement

    def test_the_two_not_exists_are_always_there(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._list(monkeypatch, SysIndexMenu(user_id=2)).statements[0]

        assert "not exists (select 1 from sys_index_menu tim where tim.del_flag = '0'" in statement
        assert "not exists (select 1 from sys_menu t3 where t3.menu_type = 'c'" in statement.lower()

    def test_a_normal_user_gets_the_role_exists_filter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        statement = self._list(monkeypatch, SysIndexMenu(user_id=2)).statements[0]

        assert "exists (select 1 from sys_role_menu rm,sys_user_role ur" in statement
        assert "and ur.user_id = :user_id" in statement

    def test_a_super_user_does_not_get_the_role_filter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``userId == 1`` -> ``<if>`` 不成立（OGNL ``!=``），超管看所有人的菜单。"""
        factory = self._list(monkeypatch, SysIndexMenu(user_id=1))

        statement = factory.statements[0]
        assert "sys_role_menu" not in statement
        # 但另外两个 not exists 仍在，且 userId 仍要绑定（not exists 里也用了它）
        assert factory.params[0]["user_id"] == 1

    def test_a_null_user_still_gets_the_role_filter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OGNL 里 ``null != 1`` 为真 —— 少了 userId 反而**更**严格。"""
        statement = self._list(monkeypatch, SysIndexMenu()).statements[0]

        assert "sys_role_menu" in statement

    def test_the_two_filters_are_like_and_skipped_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = self._list(
            monkeypatch, SysIndexMenu(user_id=2, menu_name="费用", menu_name2="")
        )

        statement = factory.statements[0]
        assert "and t1.menu_name like concat('%',:menu_name,'%')" in statement
        assert "menu_name2" not in statement
        assert factory.params[0] == {"user_id": 2, "menu_name": "费用"}

    def test_the_statement_carries_its_own_order_by(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """自带 ``order by`` -> PageHelper 不再追加客户端排序列。"""
        statement = self._list(monkeypatch, SysIndexMenu(user_id=2)).statements[0]

        assert statement.endswith(
            "order by t2.parent_id,t2.order_num,t1.order_num,t1.menu_id"
        )

    def test_when_paged_the_count_wraps_the_whole_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(
            _Result(scalar_value=1),
            _Result(rows=[["费用管理", 100, "车辆查询"]], keys=_LIST_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()

        rows = SysIndexMenuMapper().select_sys_index_menu_list(SysIndexMenu(user_id=2))

        assert isinstance(rows, PageList)
        assert rows.total == 1
        count_statement, data_statement = factory.statements
        assert count_statement.startswith("select count(0) from (")
        assert count_statement.endswith(") table_count")
        assert data_statement.endswith("LIMIT 0, 10")

    def test_the_projected_columns_land_on_the_right_attributes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(
            _Result(rows=[["费用管理", 100, "车辆查询"]], keys=_LIST_KEYS)
        )
        _patch(monkeypatch, factory)

        rows = SysIndexMenuMapper().select_sys_index_menu_list(SysIndexMenu(user_id=2))

        assert (rows[0].menu_name2, rows[0].menu_id, rows[0].menu_name) == (
            "费用管理",
            100,
            "车辆查询",
        )
        # 其它属性保持 None（resultMap 只声明了这几列）
        assert rows[0].id is None
        assert rows[0].menu_url is None


# --------------------------------------------------------------------------- getList


class TestGetList:
    def test_the_fixed_shape_of_the_nine_grid_query(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_MY_LIST_KEYS))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().get_list(SysIndexMenu(user_id=7))

        statement = factory.statements[0]
        assert "from SYS_INDEX_MENU t" in statement
        assert "left join sys_menu t1 on t.MENU_ID = t1.menu_id" in statement
        assert "left join sys_menu t2 on t1.parent_id = t2.menu_id" in statement
        assert "concat(t2.path,'/',t1.path) as menuurl" in statement.lower()
        assert "t.del_flag='0'" in statement
        assert "t.USER_ID = :user_id" in statement
        assert statement.endswith("order by t.CREATE_TIME desc limit 9")

    def test_it_never_runs_a_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``limit 9`` 是语句自带的；控制器也不 ``startPage()``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_MY_LIST_KEYS))
        _patch(monkeypatch, factory)
        start_page()

        SysIndexMenuMapper().get_list(SysIndexMenu(user_id=7))

        assert len(factory.statements) == 1
        assert "count(0)" not in factory.statements[0]

    def test_the_user_id_is_bound_verbatim(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_MY_LIST_KEYS))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().get_list(SysIndexMenu(user_id=7))

        assert factory.params == [{"user_id": 7}]

    def test_the_three_columns_are_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(
            _Result(rows=[["u-1", "车辆查询", "/car/query"]], keys=_MY_LIST_KEYS)
        )
        _patch(monkeypatch, factory)

        rows = SysIndexMenuMapper().get_list(SysIndexMenu(user_id=7))

        assert (rows[0].id, rows[0].menu_name, rows[0].menu_url) == (
            "u-1",
            "车辆查询",
            "/car/query",
        )


# --------------------------------------------------------------------------- selectSysIndexMenuById


class TestSelectSysIndexMenuById:
    def test_the_vo_selects_the_eleven_columns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().select_sys_index_menu_by_id("abc")

        statement = factory.statements[0]
        assert "select t.ID, t.USER_ID, t.MENU_ID, t.SORT, t.EPS_ID, t.DEL_FLAG" in statement
        assert "t.CREATE_BY, t.CREATE_TIME, t.UPDATE_BY, t.UPDATE_TIME, t.TENANT_ID" in statement
        assert "from sys_index_menu t where t.ID = :id" in statement
        assert factory.params == [{"id": "abc"}]

    def test_a_miss_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        assert SysIndexMenuMapper().select_sys_index_menu_by_id("abc") is None

    def test_the_snake_case_columns_are_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(
            _Result(rows=[["u-1", 7, 100, 1, 3, "0", 7, None, 7, None, 100]], keys=_VO_KEYS)
        )
        _patch(monkeypatch, factory)

        entity = SysIndexMenuMapper().select_sys_index_menu_by_id("u-1")

        assert entity is not None
        assert (entity.id, entity.user_id, entity.menu_id, entity.sort) == ("u-1", 7, 100, 1)
        assert (entity.eps_id, entity.del_flag, entity.create_by, entity.tenant_id) == (3, "0", 7, 100)


# --------------------------------------------------------------------------- insert / update


class TestInsertAndUpdate:
    def test_the_insert_lists_the_columns_in_xml_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        entity = SysIndexMenu(
            id="u-1",
            user_id=7,
            menu_id=100,
            del_flag="0",
            create_by=7,
            tenant_id=100,
        )
        SysIndexMenuMapper().insert_sys_index_menu(entity)

        statement = factory.statements[0]
        assert (
            statement
            == "insert into sys_index_menu (ID,USER_ID,MENU_ID,DEL_FLAG,CREATE_BY,TENANT_ID) "
            "values (:id,:user_id,:menu_id,:del_flag,:create_by,:tenant_id)"
        )

    def test_a_blank_string_is_written_not_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<trim>`` 里全是 ``!= null`` —— ``""`` 会真的进 SQL（与 ``sys_config`` 相反）。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().insert_sys_index_menu(SysIndexMenu(id="u-1", del_flag=""))

        statement = factory.statements[0]
        assert "DEL_FLAG" in statement
        assert factory.params[0]["del_flag"] == ""

    def test_all_none_produces_an_empty_column_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java 同样会拼出 ``insert into sys_index_menu () values ()`` —— 保留该行为。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().insert_sys_index_menu(SysIndexMenu())

        assert factory.statements[0] == "insert into sys_index_menu () values ()"

    def test_the_id_is_not_backfilled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """没有 ``useGeneratedKeys`` —— ``id`` 是 service 侧先算好的。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        entity = SysIndexMenu(user_id=7, menu_id=100)
        SysIndexMenuMapper().insert_sys_index_menu(entity)

        assert entity.id is None

    def test_the_update_sets_the_ten_columns_and_filters_on_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().update_sys_index_menu(
            SysIndexMenu(id="u-1", user_id=7, del_flag="1")
        )

        statement = factory.statements[0]
        assert statement == (
            "update sys_index_menu set USER_ID = :user_id,DEL_FLAG = :del_flag where ID = :id"
        )
        assert factory.params[0] == {"user_id": 7, "del_flag": "1", "id": "u-1"}

    def test_the_update_never_sets_the_id_column(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``id`` 只出现在 ``where`` 里，不参与 ``set``。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().update_sys_index_menu(SysIndexMenu(id="u-1", user_id=7))

        statement = factory.statements[0]
        assert "set USER_ID" in statement
        assert "set " not in statement.replace("set USER_ID", "")


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_by_id_is_a_soft_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().delete_sys_index_menu_by_id("u-1")

        assert factory.statements[0] == (
            "update sys_index_menu set del_flag = '1' where ID = :id"
        )
        assert factory.params == [{"id": "u-1"}]

    def test_delete_by_ids_is_a_soft_delete_with_an_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().delete_sys_index_menu_by_ids(["u-1", "u-2"])

        assert factory.statements[0] == (
            "update sys_index_menu set del_flag = '1' where ID in (:p0, :p1)"
        )
        assert factory.params == [{"p0": "u-1", "p1": "u-2"}]

    def test_an_empty_id_list_produces_in_parentheses(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<foreach>`` 空数组 -> ``in ()``（Java 同样是语法错）。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().delete_sys_index_menu_by_ids([])

        assert factory.statements[0].endswith("where ID in ()")

    def test_delete_by_menu_user_id_is_physical(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """唯一一条真 ``delete from`` —— 供"先删后插"用，**不带** ``del_flag`` 过滤。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysIndexMenuMapper().delete_by_menu_user_id(SysIndexMenu(user_id=7, menu_id=100))

        assert factory.statements[0] == (
            "delete from sys_index_menu where menu_id = :menu_id and user_id = :user_id"
        )
        assert factory.params == [{"menu_id": 100, "user_id": 7}]