"""``SysUpgradeInfoMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysUpgradeInfoMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUpgradeInfoMapper.java

本模块"改错了不报错、只悄悄换结果集"的五处
-------------------------------------------
1. ``selectSysUpgradeInfoList`` 的 ``where t.del_flag = '0'`` 是**硬编码**的
   （XML 里没有 ``<where>`` 标签），所以条件片段**不带**前导 ``AND``。
2. 7 个 ``<if>`` 分两类判据：``id`` / ``ver`` / ``info`` / ``backCol1`` 是
   ``!= null and != ''``；``epsId`` / ``tenantId`` / ``createBy`` 只判
   ``!= null`` —— 后者传 ``""`` 会真的变成 ``t.eps_id = ''``。
3. ``selectSysUpgradeInfoById`` **没有** ``del_flag`` 过滤，软删除的行照样查得到。
4. ``selectSysUpgradeInfoNewest`` **完全无视入参**（语句里没有一个 ``#{...}``），
   并且写死 ``back_col1 = 1`` + ``ORDER BY t.UPDATE_TIME desc LIMIT 1``。
5. 两条 ``delete`` 都是软删除（``set del_flag = '1'``），没有物理删除。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.system.domain.sys_upgrade_info import SysUpgradeInfo
from app.system.mapper.sys_upgrade_info_mapper import SysUpgradeInfoMapper

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
        self.params: List[Optional[Dict[str, Any]]] = []

    def execute(self, statement: Any, params: Optional[Dict[str, Any]] = None) -> _Result:
        self.statements.append(" ".join(str(statement).split()))
        self.params.append(None if params is None else dict(params))
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
    def params(self) -> List[Optional[Dict[str, Any]]]:
        return [params for session in self.sessions for params in session.params]


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_upgrade_info_mapper

    monkeypatch.setattr(sys_upgrade_info_mapper, "session_scope", factory)


@pytest.fixture(autouse=True)
def _clear_page_state() -> Any:
    clear_page()
    yield
    clear_page()


#: ``selectSysUpgradeInfoVo`` 的 11 列，顺序与 XML 一致。
_VO_KEYS: Sequence[str] = (
    "id",
    "ver",
    "info",
    "back_col1",
    "eps_id",
    "del_flag",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "tenant_id",
)

#: 一行的标准值，顺序与 ``_VO_KEYS`` 对齐。
_VO_ROW: Sequence[Any] = (
    "u-1",
    "1.2.3",
    "修复若干问题",
    "1",
    103,
    "0",
    2,
    None,
    2,
    None,
    100,
)


def _list(monkeypatch: pytest.MonkeyPatch, entity: SysUpgradeInfo) -> _SessionFactory:
    factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
    _patch(monkeypatch, factory)
    SysUpgradeInfoMapper().select_sys_upgrade_info_list(entity)
    return factory


# --------------------------------------------------------------------------- selectById


class TestSelectById:
    def test_the_vo_selects_the_eleven_columns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().select_sys_upgrade_info_by_id("u-1")

        assert factory.statements[0] == (
            "select t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag, t.create_by, "
            "t.create_time, t.update_by, t.update_time, t.tenant_id "
            "from sys_upgrade_info t where t.id = :id"
        )
        assert factory.params == [{"id": "u-1"}]

    def test_there_is_no_del_flag_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """与 list 不对称：软删除的行**仍然**能按 id 查到。"""
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().select_sys_upgrade_info_by_id("u-1")

        assert "del_flag" in factory.statements[0]  # 只是被 select 出来，不参与过滤
        assert "del_flag =" not in factory.statements[0]
        assert "del_flag='" not in factory.statements[0]

    def test_a_miss_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        assert SysUpgradeInfoMapper().select_sys_upgrade_info_by_id("u-1") is None

    def test_the_eleven_columns_are_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_VO_ROW], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        entity = SysUpgradeInfoMapper().select_sys_upgrade_info_by_id("u-1")

        assert entity is not None
        assert (entity.id, entity.ver, entity.info, entity.back_col1) == (
            "u-1",
            "1.2.3",
            "修复若干问题",
            "1",
        )
        assert (entity.eps_id, entity.del_flag, entity.create_by, entity.tenant_id) == (
            103,
            "0",
            2,
            100,
        )

    def test_database_upper_case_labels_still_map(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``_map_upgrade_info`` 把列名 ``lower()`` 后再查表，``ID`` 也能落位。"""
        factory = _SessionFactory(_Result(rows=[_VO_ROW], keys=[key.upper() for key in _VO_KEYS]))
        _patch(monkeypatch, factory)

        entity = SysUpgradeInfoMapper().select_sys_upgrade_info_by_id("u-1")

        assert entity is not None
        assert entity.back_col1 == "1"
        assert entity.tenant_id == 100


# --------------------------------------------------------------------------- selectList


class TestSelectList:
    def test_the_hardcoded_condition_is_the_only_one_for_an_empty_query(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _list(monkeypatch, SysUpgradeInfo())

        assert factory.statements[0] == (
            "select t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag, t.create_by, "
            "t.create_time, t.update_by, t.update_time, t.tenant_id "
            "from sys_upgrade_info t where t.del_flag = '0' "
            "order by t.create_time desc,t.id"
        )
        assert factory.params == [{}]

    def test_the_conditions_join_with_and_and_never_emit_where_and(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """XML 没有 ``<where>`` 标签 —— 硬编码的 ``where`` 后面只能接 ``and``。"""
        statement = _list(monkeypatch, SysUpgradeInfo(ver="1.2.3")).statements[0]

        assert "where t.del_flag = '0' and t.ver = :ver" in statement
        assert "where and" not in statement

    def test_the_seven_conditions_follow_the_xml_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _list(
            monkeypatch,
            SysUpgradeInfo(
                id="u-1",
                ver="1.2.3",
                info="修复",
                back_col1="1",
                eps_id=103,
                tenant_id=100,
                create_by=2,
            ),
        )

        statement = factory.statements[0]
        positions = [
            statement.index("t.id = :id"),
            statement.index("t.ver = :ver"),
            statement.index("t.info = :info"),
            statement.index("t.back_col1 = :back_col1"),
            statement.index("t.eps_id = :eps_id"),
            statement.index("t.tenant_id = :tenant_id"),
            statement.index("t.create_by = :create_by"),
        ]
        assert positions == sorted(positions)

    def test_the_four_equality_conditions_skip_blank_strings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``!= null and != ''`` —— ``""`` 被跳过（与下面那三个条件相反）。"""
        factory = _list(
            monkeypatch,
            SysUpgradeInfo(id="", ver="", info="", back_col1=""),
        )

        statement = factory.statements[0]
        for column in ("t.id", "t.ver", "t.info", "t.back_col1"):
            assert f"{column} = " not in statement
        assert factory.params == [{}]

    def test_a_whitespace_string_is_not_blank(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``OGNL`` 的 ``!= ''`` 不 trim —— ``"   "`` 会进 SQL。"""
        factory = _list(monkeypatch, SysUpgradeInfo(ver="   "))

        assert "t.ver = :ver" in factory.statements[0]
        assert factory.params[0]["ver"] == "   "

    def test_the_three_null_only_conditions_have_no_empty_string_check(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``epsId`` / ``tenantId`` / ``createBy`` 的判据只有 ``!= null``。

        这三个字段是 ``Long`` / ``int``，正常构造传 ``""`` 会先被 pydantic 拒掉
        （Spring 侧同样把空串转成 ``null``），所以用 ``model_construct`` 绕过校验，
        只为钉住"判据里**没有** ``!= ''``"这件事。
        """
        factory = _list(
            monkeypatch,
            SysUpgradeInfo.model_construct(eps_id="", tenant_id="", create_by=""),
        )

        statement = factory.statements[0]
        assert "t.eps_id = :eps_id" in statement
        assert "t.tenant_id = :tenant_id" in statement
        assert "t.create_by = :create_by" in statement
        assert factory.params[0] == {"eps_id": "", "tenant_id": "", "create_by": ""}

    def test_the_zero_valued_foreign_keys_are_kept(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``0`` 不是 ``null`` —— ``tenantId = 0`` 会真的进 SQL。"""
        factory = _list(monkeypatch, SysUpgradeInfo(eps_id=0, tenant_id=0, create_by=0))

        assert factory.params[0] == {"eps_id": 0, "tenant_id": 0, "create_by": 0}

    def test_the_statement_carries_its_own_order_by(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """自带 ``order by`` -> 前端点表头排序不生效。"""
        statement = _list(monkeypatch, SysUpgradeInfo()).statements[0]

        assert statement.endswith("order by t.create_time desc,t.id")

    def test_when_paged_the_count_wraps_the_whole_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(
            _Result(scalar_value=1),
            _Result(rows=[_VO_ROW], keys=_VO_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()

        rows = SysUpgradeInfoMapper().select_sys_upgrade_info_list(SysUpgradeInfo(tenant_id=100))

        assert isinstance(rows, PageList)
        assert rows.total == 1
        count_statement, data_statement = factory.statements
        assert count_statement.startswith("select count(0) from (")
        assert count_statement.endswith(") table_count")
        assert data_statement.endswith("LIMIT 0, 10")

    def test_when_paged_the_client_order_by_is_ignored(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """语句自带 ``order by`` -> ``select_page`` 不追加请求排序。"""
        # count 必须 > 0：PageHelper 在 count 为 0 时连 data 语句都不执行。
        factory = _SessionFactory(
            _Result(scalar_value=1),
            _Result(rows=[], keys=_VO_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()

        SysUpgradeInfoMapper().select_sys_upgrade_info_list(SysUpgradeInfo())

        data_statement = factory.statements[1]
        assert data_statement.count("order by") == 1
        assert data_statement.endswith("LIMIT 0, 10")

    def test_the_rows_are_mapped_positionally(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``resultMap`` 只声明了这 11 列，其它属性保持 ``None``。"""
        factory = _SessionFactory(_Result(rows=[_VO_ROW], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        rows = SysUpgradeInfoMapper().select_sys_upgrade_info_list(SysUpgradeInfo())

        assert (rows[0].id, rows[0].ver, rows[0].back_col1) == ("u-1", "1.2.3", "1")
        assert rows[0].dept_sub_code is None
        assert rows[0].sort is None
        assert rows[0].remark is None


# --------------------------------------------------------------------------- selectNewest


class TestSelectNewest:
    def test_the_sql_ignores_the_parameter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Java 声明了入参但语句里没有 ``#{...}`` —— 传什么都不影响结果。"""
        factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().select_sys_upgrade_info_newest(
            SysUpgradeInfo(id="u-1", ver="9.9.9", tenant_id=999)
        )

        assert factory.statements[0] == (
            "select t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag, t.create_by, "
            "t.create_time, t.update_by, t.update_time, t.tenant_id "
            "from sys_upgrade_info t where t.del_flag = '0' and t.back_col1 = 1 "
            "ORDER BY t.UPDATE_TIME desc LIMIT 1"
        )
        assert factory.params == [None]

    def test_only_the_live_flagged_row_can_win(self, monkeypatch: pytest.MonkeyPatch) -> None:
        statement = (
            _newest_factory(monkeypatch).statements[0]
        )

        assert "t.del_flag = '0'" in statement
        assert "t.back_col1 = 1" in statement

    def test_a_miss_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch(monkeypatch, _SessionFactory(_Result(rows=[], keys=_VO_KEYS)))

        assert SysUpgradeInfoMapper().select_sys_upgrade_info_newest(SysUpgradeInfo()) is None

    def test_a_hit_returns_the_mapped_entity(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch(monkeypatch, _SessionFactory(_Result(rows=[_VO_ROW], keys=_VO_KEYS)))

        entity = SysUpgradeInfoMapper().select_sys_upgrade_info_newest(SysUpgradeInfo())

        assert entity is not None
        assert (entity.ver, entity.info) == ("1.2.3", "修复若干问题")

    def test_it_does_not_run_a_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``limit 1`` 是语句自带的；控制器也没 ``startPage()``。"""
        factory = _newest_factory(monkeypatch)

        assert len(factory.statements) == 1
        assert "count(0)" not in factory.statements[0]


def _newest_factory(monkeypatch: pytest.MonkeyPatch) -> _SessionFactory:
    factory = _SessionFactory(_Result(rows=[], keys=_VO_KEYS))
    _patch(monkeypatch, factory)
    SysUpgradeInfoMapper().select_sys_upgrade_info_newest(SysUpgradeInfo())
    return factory


# --------------------------------------------------------------------------- insert / update


class TestInsert:
    def test_the_columns_follow_the_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().insert_sys_upgrade_info(
            SysUpgradeInfo(id="u-1", ver="1.2.3", del_flag="0", create_by=2, tenant_id=100)
        )

        assert factory.statements[0] == (
            "insert into sys_upgrade_info (id,ver,del_flag,create_by,tenant_id) "
            "values (:id,:ver,:del_flag,:create_by,:tenant_id)"
        )
        assert factory.params[0] == {
            "id": "u-1",
            "ver": "1.2.3",
            "del_flag": "0",
            "create_by": 2,
            "tenant_id": 100,
        }

    def test_all_eleven_columns_in_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().insert_sys_upgrade_info(
            SysUpgradeInfo(
                id="u-1",
                ver="1.2.3",
                info="修复",
                back_col1="1",
                eps_id=103,
                del_flag="0",
                create_by=2,
                create_time=_stamp(),
                update_by=2,
                update_time=_stamp(),
                tenant_id=100,
            )
        )

        statement = factory.statements[0]
        assert statement.startswith(
            "insert into sys_upgrade_info "
            "(id,ver,info,back_col1,eps_id,del_flag,create_by,create_time,update_by,update_time,tenant_id) "
            "values ("
        )

    def test_a_blank_string_is_written_not_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<trim>`` 里全是 ``!= null`` —— ``""`` 会真的进 SQL。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().insert_sys_upgrade_info(SysUpgradeInfo(id="u-1", ver=""))

        assert "ver" in factory.statements[0]
        assert factory.params[0]["ver"] == ""

    def test_all_none_produces_an_empty_column_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java 同样会拼出 ``insert into sys_upgrade_info () values ()`` —— 保留该行为。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().insert_sys_upgrade_info(SysUpgradeInfo())

        assert factory.statements[0] == "insert into sys_upgrade_info () values ()"

    def test_the_id_is_not_backfilled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """没有 ``useGeneratedKeys`` —— ``id`` 是 service 侧先算好的。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        entity = SysUpgradeInfo(ver="1.2.3")
        SysUpgradeInfoMapper().insert_sys_upgrade_info(entity)

        assert entity.id is None

    def test_the_row_count_is_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        assert SysUpgradeInfoMapper().insert_sys_upgrade_info(SysUpgradeInfo(id="u-1")) == 1


class TestUpdate:
    def test_the_ten_columns_and_the_id_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().update_sys_upgrade_info(
            SysUpgradeInfo(id="u-1", ver="1.2.4", del_flag="0")
        )

        assert factory.statements[0] == (
            "update sys_upgrade_info set ver = :ver,del_flag = :del_flag where id = :id"
        )
        assert factory.params[0] == {"ver": "1.2.4", "del_flag": "0", "id": "u-1"}

    def test_the_id_never_appears_in_the_set_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().update_sys_upgrade_info(SysUpgradeInfo(id="u-1", ver="1.2.4"))

        statement = factory.statements[0]
        assert "id = :id" in statement
        assert statement.count("id = :id") == 1
        assert "set id" not in statement

    def test_a_blank_string_clears_the_column(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<set>`` 只有 ``!= null`` —— ``""`` 会把列清空（与 list 的等值条件不同）。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().update_sys_upgrade_info(SysUpgradeInfo(id="u-1", info=""))

        assert "info = :info" in factory.statements[0]
        assert factory.params[0]["info"] == ""

    def test_all_none_still_emits_a_syntactically_broken_update(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java 同样会拼出 ``update ... set  where id = ?`` —— 照抄。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().update_sys_upgrade_info(SysUpgradeInfo(id="u-1"))

        # ``_RecordingSession`` 会把连续空白压成一个空格，所以这里看到的是单空格。
        assert factory.statements[0] == "update sys_upgrade_info set where id = :id"


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_by_id_is_a_soft_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().delete_sys_upgrade_info_by_id("u-1")

        assert factory.statements[0] == (
            "update sys_upgrade_info set del_flag = '1' where id = :id"
        )
        assert factory.params == [{"id": "u-1"}]

    def test_delete_by_ids_is_a_soft_delete_with_an_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().delete_sys_upgrade_info_by_ids(["u-1", "u-2"])

        assert factory.statements[0] == (
            "update sys_upgrade_info set del_flag = '1' where id in (:p0, :p1)"
        )
        assert factory.params == [{"p0": "u-1", "p1": "u-2"}]

    def test_an_empty_id_list_produces_in_parentheses(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<foreach>`` 空数组 -> ``in ()``（Java 同样是语法错）。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().delete_sys_upgrade_info_by_ids([])

        assert factory.statements[0].endswith("where id in ()")

    def test_there_is_no_physical_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """整个 XML 里没有 ``delete from``。"""
        factory = _SessionFactory(_Result(rowcount=1), _Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysUpgradeInfoMapper().delete_sys_upgrade_info_by_id("u-1")
        SysUpgradeInfoMapper().delete_sys_upgrade_info_by_ids(["u-1"])

        assert all(statement.startswith("update ") for statement in factory.statements)

    def test_the_row_count_is_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        assert SysUpgradeInfoMapper().delete_sys_upgrade_info_by_ids(["u-1"]) == 0


def _stamp() -> Any:
    from app.common.utils.date_utils import get_timestamp

    return get_timestamp()
