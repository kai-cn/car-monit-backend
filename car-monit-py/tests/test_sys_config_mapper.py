"""``SysConfigMapper`` -- SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysConfigMapper.xml
#   ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysConfigMapper.java

这一层为什么值钱
----------------
参数配置的 CRUD 一旦接上假 Mapper，SQL 就全被遮住了。这里有五处改错了**不会报错**、
只会悄悄换结果集或改掉数据：

1. ``selectConfig`` 与 ``selectConfigList`` 是**两条不同的语句**：前者只有 2 个条件
   （``configId`` / ``configKey``），后者有 5 个（``configName`` / ``configType`` /
   ``configKey`` / ``beginTime`` / ``endTime``）。把两条合成一条就会多出/少掉条件。
2. 两条语句都**没有** ``order by`` —— 不许"顺手"补，补了会让 PageHelper 不再追加
   客户端的排序列。
3. ``insertConfig`` **没有** ``useGeneratedKeys``，插入后 ``configId`` 仍是 ``null``。
4. ``updateConfig`` 的 ``<set>`` 里只有 ``remark`` 判 ``!= null``（空串会**清列**），
   其余 5 列判 ``!= null and != ''``。
5. ``checkConfigKeyUnique`` 的入参是**键名**，且 SQL 自带 ``limit 1``。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.page.page_helper import PageList, clear_page, start_page
from app.system.domain.sys_config import SysConfig
from app.system.mapper.sys_config_mapper import SELECT_CONFIG_VO, SysConfigMapper

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


#: ``selectConfigVo`` 的 10 列，顺序与 XML 一致。
_CONFIG_KEYS: Sequence[str] = (
    "config_id",
    "config_name",
    "config_key",
    "config_value",
    "config_type",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "remark",
)


def _row(config_id: int = 1) -> tuple:
    return (
        config_id,
        "主框架页-默认皮肤样式名称",
        "sys.index.skinName",
        "skin-blue",
        "Y",
        "admin",
        None,
        None,
        None,
        "备注",
    )


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_config_mapper

    monkeypatch.setattr(sys_config_mapper, "session_scope", factory)


# --------------------------------------------------------------------------- selectConfig


class TestSelectConfig:
    def test_without_conditions_there_is_no_where_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<sql id="sqlwhereSearch">`` 的 ``<where>`` 为空时不产出内容。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        config = SysConfigMapper().select_config(SysConfig())

        assert config is not None
        assert config.config_key == "sys.index.skinName"
        statement = factory.statements[0]
        assert " from sys_config" in statement
        assert "where" not in statement.lower()
        assert "order by" not in statement.lower()

    def test_config_id_is_bound_on_its_own(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``selectConfigById`` 只传 id —— 只有一个条件。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config(SysConfig(config_id=7))

        assert "where config_id = :config_id" in factory.statements[0]
        assert factory.params[0] == {"config_id": 7}

    def test_config_id_zero_is_still_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """判据是 ``!= null``：``0`` 会真的去 ``where config_id = 0``（查不到）。"""
        factory = _SessionFactory(_Result(rows=[], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        assert SysConfigMapper().select_config(SysConfig(config_id=0)) is None
        assert factory.params[0] == {"config_id": 0}

    def test_config_key_is_bound_when_not_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``selectConfigByKey`` 的回源查询。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config(SysConfig(config_key="sys.user.initPassword"))

        assert "where config_key = :config_key" in factory.statements[0]
        assert factory.params[0] == {"config_key": "sys.user.initPassword"}

    def test_an_empty_config_key_is_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``configKey`` 是 ``!= null and != ''`` —— 空串不产生条件。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config(SysConfig(config_key=""))

        assert "where" not in factory.statements[0].lower()

    def test_both_conditions_are_joined_with_and(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config(SysConfig(config_id=1, config_key="k"))

        statement = factory.statements[0]
        assert "where config_id = :config_id and config_key = :config_key" in statement
        assert "where and" not in statement.lower()

    def test_remark_comes_from_the_auto_mapping(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``SysConfigResult`` **没有**声明 ``remark``，靠自动映射补上。"""
        factory = _SessionFactory(_Result(rows=[_row()], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        config = SysConfigMapper().select_config(SysConfig(config_id=1))

        assert config is not None
        assert config.remark == "备注"
        assert config.create_by == "admin"


# --------------------------------------------------------------------------- selectConfigList


class TestSelectConfigList:
    def test_without_filters_there_is_no_where_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        rows = SysConfigMapper().select_config_list(SysConfig())

        assert [row.config_id for row in rows] == [1]
        statement = factory.statements[0]
        assert "where" not in statement.lower()
        # 本语句**没有** order by（与 dict/notice 不同）
        assert "order by" not in statement.lower()

    def test_the_five_filters_keep_the_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``configName`` -> ``configType`` -> ``configKey`` -> ``beginTime`` -> ``endTime``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config_list(
            SysConfig(
                config_name="皮肤",
                config_type="Y",
                config_key="sys.index",
                params={"beginTime": "2024-01-01", "endTime": "2024-12-31"},
            )
        )

        statement = factory.statements[0]
        expected = [
            "config_name like concat('%', :config_name, '%')",
            "config_type = :config_type",
            "config_key like concat('%', :config_key, '%')",
            "date_format(create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')",
            "date_format(create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')",
        ]
        positions = [statement.index(fragment) for fragment in expected]
        assert positions == sorted(positions)
        assert factory.params[0]["begin_time"] == "2024-01-01"
        assert factory.params[0]["end_time"] == "2024-12-31"

    def test_the_where_clause_does_not_start_with_and(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``<where>`` 会吃掉首个 ``AND``；拼出 ``where AND a`` 就是 SQL 语法错。"""
        factory = _SessionFactory(_Result(rows=[], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config_list(SysConfig(config_type="Y"))

        statement = factory.statements[0]
        assert "where and" not in statement.lower()
        assert "where config_type = :config_type" in statement

    def test_a_single_space_still_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """OGNL 的 ``!= null and != ''`` **不是** ``isBlank``：``" "`` 照样 ``like '% %'``。"""
        factory = _SessionFactory(_Result(rows=[], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config_list(SysConfig(config_name=" "))

        assert "config_name like" in factory.statements[0]
        assert factory.params[0] == {"config_name": " "}

    def test_an_empty_param_is_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config_list(
            SysConfig(params={"beginTime": "", "endTime": None})
        )

        assert "where" not in factory.statements[0].lower()

    def test_after_start_page_the_count_wraps_the_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(
            _Result(scalar_value=1),
            _Result(rows=[_row()], keys=_CONFIG_KEYS),
        )
        _patch(monkeypatch, factory)
        start_page()

        rows = SysConfigMapper().select_config_list(SysConfig(config_type="Y"))

        assert isinstance(rows, PageList)
        assert rows.total == 1
        count_statement, data_statement = factory.statements
        assert count_statement.startswith("select count(0) from (")
        assert count_statement.endswith(") table_count")
        assert data_statement.endswith("LIMIT 0, 10")

    def test_without_start_page_nothing_is_paginated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        SysConfigMapper().select_config_list(SysConfig())

        assert len(factory.statements) == 1
        assert "limit" not in factory.statements[0].lower()


# --------------------------------------------------------------------------- checkConfigKeyUnique


class TestCheckConfigKeyUnique:
    def test_the_statement_carries_limit_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row()], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        info = SysConfigMapper().check_config_key_unique("sys.index.skinName")

        assert info is not None and info.config_id == 1
        assert factory.statements[0].endswith("where config_key = :config_key limit 1")

    def test_a_miss_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[], keys=_CONFIG_KEYS))
        _patch(monkeypatch, factory)

        assert SysConfigMapper().check_config_key_unique("nope") is None


# --------------------------------------------------------------------------- insertConfig


class TestInsertConfig:
    def test_empty_strings_are_dropped_from_the_column_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """六列全是 ``!= null and != ''`` —— 空串既不进列名也不进值。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysConfigMapper().insert_config(
            SysConfig(config_name="皮肤", config_key="k", config_value="", config_type="")
        )

        statement = factory.statements[0]
        assert statement.startswith("insert into sys_config (config_name,config_key,create_time)")
        assert statement.endswith("values (:config_name,:config_key,sysdate())")
        assert factory.params[0] == {"config_name": "皮肤", "config_key": "k"}

    def test_the_generated_key_is_not_written_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """XML **没有** ``useGeneratedKeys``，所以 ``config_id`` 保持 ``None``。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=42))
        _patch(monkeypatch, factory)
        config = SysConfig(config_name="皮肤", config_key="k", config_value="v")

        SysConfigMapper().insert_config(config)

        assert config.config_id is None

    def test_remark_and_create_by_are_optional(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysConfigMapper().insert_config(
            SysConfig(config_name="n", config_key="k", config_value="v", create_by="admin", remark="r")
        )

        statement = factory.statements[0]
        assert "create_by" in statement
        assert "remark" in statement
        assert factory.params[0]["create_by"] == "admin"


# --------------------------------------------------------------------------- updateConfig


class TestUpdateConfig:
    def test_remark_keeps_an_empty_string_while_others_drop_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``remark`` 只判 ``!= null`` —— 传 ``""`` 会**清列**；其余列会跳过。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysConfigMapper().update_config(
            SysConfig(
                config_id=1,
                config_name="",
                config_key="",
                config_value="",
                config_type="",
                update_by="",
                remark="",
            )
        )

        statement = factory.statements[0]
        assert "set remark = :remark, update_time = sysdate()" in statement
        assert factory.params[0] == {"remark": "", "config_id": 1}

    def test_update_time_is_unconditional(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysConfigMapper().update_config(SysConfig(config_id=3))

        assert factory.statements[0] == (
            "update sys_config set update_time = sysdate() where config_id = :config_id"
        )

    def test_the_set_clause_keeps_the_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysConfigMapper().update_config(
            SysConfig(
                config_id=1,
                config_name="n",
                config_key="k",
                config_value="v",
                config_type="N",
                update_by="admin",
                remark="r",
            )
        )

        statement = factory.statements[0]
        expected = [
            "config_name = :config_name",
            "config_key = :config_key",
            "config_value = :config_value",
            "config_type = :config_type",
            "update_by = :update_by",
            "remark = :remark",
        ]
        positions = [statement.index(fragment) for fragment in expected]
        assert positions == sorted(positions)
        assert statement.endswith("where config_id = :config_id")


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_by_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Java 侧没有调用方，按迁移原则第 4 条照留。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        assert SysConfigMapper().delete_config_by_id(5) == 1
        assert factory.statements[0] == "delete from sys_config where config_id = :config_id"

    def test_delete_by_ids_builds_an_in_clause(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, factory)

        assert SysConfigMapper().delete_config_by_ids([1, 2]) == 2
        assert "in (:p0, :p1)" in factory.statements[0]
        assert factory.params[0] == {"p0": 1, "p1": 2}

    def test_an_empty_array_yields_an_empty_in_clause(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java 也一样拼出 ``in ()``（MySQL 语法错，不是 0 行）。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysConfigMapper().delete_config_by_ids([])

        assert factory.statements[0].endswith("where config_id in ()")


def test_the_vo_is_exported_verbatim() -> None:
    """``SELECT_CONFIG_VO`` 必须与 XML 逐字一致（含那行 Tab 缩进的 ``from``）。"""
    assert "config_id, config_name, config_key, config_value, config_type" in SELECT_CONFIG_VO
    assert "\n\t\tfrom sys_config" in SELECT_CONFIG_VO
