"""``SysRoleMapper`` 及其三张关联表 mapper —— SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml
#   ruoyi-system/src/main/resources/mapper/system/SysRoleMenuMapper.xml
#   ruoyi-system/src/main/resources/mapper/system/SysRoleDeptMapper.xml
#   ruoyi-system/src/main/resources/mapper/system/SysUserRoleMapper.xml

为什么对**拼出来的 SQL** 断言
------------------------------
角色 CRUD 的假 Mapper 会把 SQL 全遮住，而下面几处改错了不会报错、只会换结果集：

* ``selectRoleList`` 里 ``${params.dataScope}`` 是**生效**的（与 ``sys_dept`` 相反），
  且 ``selectRoleVo`` 自带 ``distinct``；
* ``insertRole`` / ``updateRole`` 的 ``menuCheckStrictly != null`` 判据恒真 ——
  两个 primitive ``boolean`` 列**必定**参与写库；
* ``updateRole`` 的 ``remark`` 只判 ``null``（空串会真的覆盖），其余字段判
  ``null and != ''``；
* ``checkRoleNameUnique`` / ``checkRoleKeyUnique`` 带 ``limit 1`` 且**不过滤**
  ``del_flag``；
* ``deleteRoleById`` / ``deleteRoleByIds`` 名叫 delete，实为 ``del_flag = '2'`` 软删。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_role import SysRole
from app.system.domain.sys_role_dept import SysRoleDept
from app.system.domain.sys_role_menu import SysRoleMenu
from app.system.mapper.sys_role_dept_mapper import SysRoleDeptMapper
from app.system.mapper.sys_role_mapper import SysRoleMapper
from app.system.mapper.sys_role_menu_mapper import SysRoleMenuMapper
from app.system.mapper.sys_user_role_mapper import SysUserRoleMapper

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
        self.params: List[Any] = []

    def execute(self, statement: Any, params: Any = None) -> _Result:
        self.statements.append(" ".join(str(statement).split()))
        self.params.append(dict(params) if isinstance(params, dict) else params)
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
    def params(self) -> List[Any]:
        return [params for session in self.sessions for params in session.params]

    @property
    def statement(self) -> str:
        return self.statements[0]

    @property
    def first_params(self) -> Dict[str, Any]:
        return self.params[0]


#: ``selectRoleVo`` 的列标签，顺序与 XML 一致（11 列）。
_ROLE_KEYS: Sequence[str] = (
    "role_id",
    "role_name",
    "role_key",
    "role_sort",
    "data_scope",
    "menu_check_strictly",
    "dept_check_strictly",
    "status",
    "del_flag",
    "create_time",
    "remark",
)


def _row(**overrides: Any) -> tuple:
    """一行 ``selectRoleVo`` 结果，按 :data:`_ROLE_KEYS` 顺序排。"""
    values: Dict[str, Any] = {
        "role_id": 2,
        "role_name": "普通角色",
        "role_key": "common",
        "role_sort": "2",
        "data_scope": "2",
        "menu_check_strictly": 0,
        "dept_check_strictly": 0,
        "status": "0",
        "del_flag": "0",
        "create_time": None,
        "remark": None,
    }
    values.update(overrides)
    return tuple(values[key] for key in _ROLE_KEYS)


def _where_part(statement: str) -> str:
    """取出 ``selectRoleVo`` 之后的 WHERE 片段（列清单里也有 ``del_flag``）。"""
    return statement.split("left join sys_dept d on u.dept_id = d.dept_id")[1]


def _patch(monkeypatch: pytest.MonkeyPatch, module: Any, factory: _SessionFactory) -> None:
    monkeypatch.setattr(module, "session_scope", factory)


# --------------------------------------------------------------------------- selectRoleById / 唯一性


class TestSelectRoleById:
    def test_no_del_flag_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``selectRoleById`` 能查到已删除的角色 —— 删除校验要靠它取 ``roleName``。"""
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[_row()], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_role_by_id(2)

        where_clause = factory.statement.split("left join sys_dept d on u.dept_id = d.dept_id")[1]
        assert "del_flag" not in where_clause
        assert where_clause.strip() == "where r.role_id = :role_id"

    def test_missing_row_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)
        assert SysRoleMapper().select_role_by_id(404) is None

    def test_all_columns_are_mapped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(
            _Result(rows=[_row(remark="备注", create_time="2024-01-01")], keys=_ROLE_KEYS)
        )
        _patch(monkeypatch, sys_role_mapper, factory)

        role = SysRoleMapper().select_role_by_id(2)

        assert role is not None
        assert (role.role_id, role.role_name, role.role_key, role.role_sort) == (2, "普通角色", "common", "2")
        assert (role.data_scope, role.status, role.del_flag) == ("2", "0", "0")
        assert (role.menu_check_strictly, role.dept_check_strictly) == (False, False)
        assert role.remark == "备注"
        # resultMap 里没有 update_by / update_time -> 恒为 None
        assert role.update_by is None
        assert role.update_time is None

    def test_tinyint_ones_become_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(
            _Result(rows=[_row(menu_check_strictly=1, dept_check_strictly=1)], keys=_ROLE_KEYS)
        )
        _patch(monkeypatch, sys_role_mapper, factory)

        role = SysRoleMapper().select_role_by_id(2)

        assert role is not None
        assert role.menu_check_strictly is True
        assert role.dept_check_strictly is True


class TestUniqueChecks:
    def test_name_check_uses_limit_one_and_no_del_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[_row()], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        found = SysRoleMapper().check_role_name_unique("普通角色")

        assert found is not None and found.role_id == 2
        assert "where r.role_name=:role_name limit 1" in factory.statement
        # 列清单里本来就有 r.del_flag，“不过滤 del_flag” 要看 WHERE 之后
        assert "del_flag" not in _where_part(factory.statement)
        assert factory.first_params == {"role_name": "普通角色"}

    def test_key_check_uses_limit_one_and_no_del_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[_row()], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        found = SysRoleMapper().check_role_key_unique("common")

        assert found is not None
        assert "where r.role_key=:role_key limit 1" in factory.statement
        assert "del_flag" not in _where_part(factory.statement)

    def test_no_match_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)
        assert SysRoleMapper().check_role_name_unique("不存在") is None


# --------------------------------------------------------------------------- selectRoleList


class TestSelectRoleList:
    def test_without_filters_only_the_soft_delete_guard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_role_list(SysRole())

        assert "where r.del_flag = '0'" in factory.statement
        assert factory.statement.endswith("order by r.role_sort")
        assert factory.first_params == {}

    def test_the_vo_is_distinct_and_joins_three_tables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """片段 join 了 ``sys_user_role`` / ``sys_user`` / ``sys_dept``，没有 ``distinct``
        的话"一个角色被两个用户拥有"会出现两次。"""
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_role_list(SysRole())

        statement = factory.statement
        assert statement.startswith("select distinct r.role_id")
        assert "from sys_role r" in statement
        assert "left join sys_user_role ur on ur.role_id = r.role_id" in statement
        assert "left join sys_user u on u.user_id = ur.user_id" in statement
        assert "left join sys_dept d on u.dept_id = d.dept_id" in statement

    def test_all_five_filters_in_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        role = SysRole(role_name="管理", status="0", role_key="admin", params={})
        role.params = {"beginTime": "2024-01-01", "endTime": "2024-12-31"}
        SysRoleMapper().select_role_list(role)

        statement = factory.statement
        positions = [
            statement.index("AND r.role_name like concat('%', :role_name, '%')"),
            statement.index("AND r.status = :status"),
            # XML 里是 ``AND r.role_key =  #{roleKey}``（两个空格），断言前已被折叠
            statement.index("AND r.role_key = :role_key"),
            statement.index("date_format(r.create_time,'%y%m%d') >= date_format(:begin_time,'%y%m%d')"),
            statement.index("date_format(r.create_time,'%y%m%d') <= date_format(:end_time,'%y%m%d')"),
        ]
        assert positions == sorted(positions)
        assert factory.first_params == {
            "role_name": "管理",
            "status": "0",
            "role_key": "admin",
            "begin_time": "2024-01-01",
            "end_time": "2024-12-31",
        }

    def test_empty_string_is_not_a_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<if test="roleName != null and roleName != ''">`` —— 空串跳过。"""
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_role_list(SysRole(role_name="", role_key="", status=""))

        assert "role_name like" not in factory.statement
        assert "r.role_key =" not in factory.statement
        assert "r.status =" not in factory.statement

    def test_a_single_space_is_still_a_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<if>`` 不 trim，``" "`` 会真的参与过滤（见 ``MAPPING_SYS_DEPT.md`` 同一结论）。"""
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_role_list(SysRole(role_name=" "))

        assert "AND r.role_name like concat('%', :role_name, '%')" in factory.statement
        assert factory.first_params["role_name"] == " "

    def test_data_scope_fragment_is_spliced_verbatim(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``${params.dataScope}`` 是**唯一**生效的 ``${}`` 拼接点（与 ``sys_dept`` 相反）。

        它排在各 ``<if>`` 之后、``order by`` 之前。
        """
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        role = SysRole()
        role.params = {"dataScope": " AND (d.dept_id = 100)"}
        SysRoleMapper().select_role_list(role)

        statement = factory.statement
        assert statement.endswith("where r.del_flag = '0' AND (d.dept_id = 100) order by r.role_sort")
        assert "AND (" in statement

    def test_no_data_scope_leaves_the_clause_inert(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_role_list(SysRole())

        assert "AND (" not in factory.statement

    def test_after_start_page_the_count_wraps_the_statement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``SysRoleController#list`` 调了 ``startPage()`` —— 这条 select 必须被分页。

        曾经漏了 ``take_page()``：接口会返回**全表**、``total`` 退化成行数。
        """
        from app.common.core.page.page_helper import PageList, clear_page, start_page
        from app.system.mapper import sys_role_mapper

        clear_page()
        factory = _SessionFactory(
            _Result(scalar_value=23),
            _Result(rows=[_row()], keys=_ROLE_KEYS),
        )
        _patch(monkeypatch, sys_role_mapper, factory)
        start_page()

        rows = SysRoleMapper().select_role_list(SysRole())

        assert isinstance(rows, PageList)
        assert rows.total == 23
        assert rows[0].role_id == 2
        count_statement, data_statement = factory.statements
        assert count_statement.startswith("select count(0) from (")
        assert count_statement.endswith(") table_count")
        assert "order by r.role_sort" in data_statement
        assert data_statement.endswith("LIMIT 0, 10")
        clear_page()

    def test_the_paging_applies_even_though_the_statement_has_its_own_order_by(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """语句自带 ``order by`` -> 客户端的 ``orderByColumn`` 被忽略（``COMPATIBILITY`` §25.6）。"""
        from app.common.core.page.page_helper import clear_page, start_page
        from app.system.mapper import sys_role_mapper

        clear_page()
        factory = _SessionFactory(
            _Result(scalar_value=1),
            _Result(rows=[_row()], keys=_ROLE_KEYS),
        )
        _patch(monkeypatch, sys_role_mapper, factory)
        start_page()

        SysRoleMapper().select_role_list(SysRole())

        data_statement = factory.statements[1]
        assert data_statement.count("order by") == 1
        assert "role_sort" in data_statement
        clear_page()


# --------------------------------------------------------------------------- insertRole


class TestInsertRole:
    def test_minimal_role_still_writes_the_two_boolean_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``menuCheckStrictly != null`` 对 primitive ``boolean`` 恒为真。

        所以哪怕只传 ``roleName``，``menu_check_strictly`` / ``dept_check_strictly``
        也一定出现在列清单里 —— 这是 XML 的真实行为，别按"包装类型"去理解。
        """
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1, lastrowid=9))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().insert_role(SysRole(role_name="测试"))

        statement = factory.statement
        assert statement == (
            "insert into sys_role(role_name, menu_check_strictly, dept_check_strictly, create_time) "
            "values(:role_name, :menu_check_strictly, :dept_check_strictly, sysdate())"
        )
        assert factory.first_params == {
            "role_name": "测试",
            "menu_check_strictly": 0,
            "dept_check_strictly": 0,
        }

    def test_all_columns_in_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1, lastrowid=9))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().insert_role(
            SysRole(
                role_id=5,
                role_name="角色",
                role_key="key",
                role_sort="3",
                data_scope="1",
                menu_check_strictly=True,
                dept_check_strictly=True,
                status="0",
                remark="备注",
                create_by="admin",
            )
        )

        assert factory.statement.startswith(
            "insert into sys_role(role_id, role_name, role_key, role_sort, data_scope, "
            "menu_check_strictly, dept_check_strictly, status, remark, create_by, create_time)"
        )
        assert factory.first_params["menu_check_strictly"] == 1
        assert factory.first_params["dept_check_strictly"] == 1
        assert factory.first_params["create_by"] == "admin"

    def test_role_id_zero_is_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<if test="roleId != null and roleId != 0">`` —— 0 与 null 等价。"""
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1, lastrowid=9))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().insert_role(SysRole(role_id=0, role_name="角色"))

        assert "role_id," not in factory.statement
        assert "role_id" not in factory.first_params

    def test_empty_strings_are_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1, lastrowid=9))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().insert_role(SysRole(role_name="角色", status="", remark="", create_by=""))

        for column in ("status", "remark", "create_by"):
            assert f"{column}," not in factory.statement

    def test_generated_key_is_written_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``useGeneratedKeys="true" keyProperty="roleId"`` —— 主键直接 set 回实体，
        Service 的 ``insertRoleMenu`` 依赖它。"""
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1, lastrowid=42))
        _patch(monkeypatch, sys_role_mapper, factory)

        role = SysRole(role_name="角色")
        rows = SysRoleMapper().insert_role(role)

        assert rows == 1
        assert role.role_id == 42


# --------------------------------------------------------------------------- updateRole


class TestUpdateRole:
    def test_the_two_boolean_columns_are_always_updated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().update_role(SysRole(role_id=2))

        assert factory.statement == (
            "update sys_role set menu_check_strictly = :menu_check_strictly, "
            "dept_check_strictly = :dept_check_strictly, update_time = sysdate() "
            "where role_id = :role_id"
        )
        assert factory.first_params["role_id"] == 2

    def test_empty_remark_overwrites_but_empty_name_does_not(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``remark`` 只判 ``!= null``，``role_name`` 判 ``!= null and != ''``。

        这条差异在"编辑角色时清空备注"场景下是**可见**的：备注真的被清掉。
        """
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().update_role(SysRole(role_id=2, role_name="", remark=""))

        assert "role_name = :role_name" not in factory.statement
        assert "remark = :remark" in factory.statement
        assert factory.first_params["remark"] == ""

    def test_null_remark_is_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().update_role(SysRole(role_id=2, remark=None))

        assert "remark" not in factory.statement

    def test_all_sets_in_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().update_role(
            SysRole(
                role_id=3,
                role_name="新名",
                role_key="new",
                role_sort="1",
                data_scope="1",
                menu_check_strictly=True,
                dept_check_strictly=False,
                status="1",
                remark="注",
                update_by="admin",
            )
        )

        statement = factory.statement
        order = [
            statement.index("role_name = :role_name"),
            statement.index("role_key = :role_key"),
            statement.index("role_sort = :role_sort"),
            statement.index("data_scope = :data_scope"),
            statement.index("menu_check_strictly = :menu_check_strictly"),
            statement.index("dept_check_strictly = :dept_check_strictly"),
            statement.index("status = :status"),
            statement.index("remark = :remark"),
            statement.index("update_by = :update_by"),
            statement.index("update_time = sysdate()"),
        ]
        assert order == sorted(order)
        assert factory.first_params["menu_check_strictly"] == 1
        assert factory.first_params["dept_check_strictly"] == 0


# --------------------------------------------------------------------------- 删除


class TestDeleteRole:
    def test_single_delete_is_soft(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().delete_role_by_id(2)

        assert factory.statement == "update sys_role set del_flag = '2' where role_id = :role_id"
        assert factory.first_params == {"role_id": 2}

    def test_batch_delete_expands_the_foreach(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, sys_role_mapper, factory)

        rows = SysRoleMapper().delete_role_by_ids([2, 3])

        assert rows == 2
        assert factory.statement == "update sys_role set del_flag = '2' where role_id in (:p0, :p1)"
        assert factory.first_params == {"p0": 2, "p1": 3}


# --------------------------------------------------------------------------- 其他 select


class TestOtherSelects:
    def test_select_role_all_has_no_soft_delete_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``selectRoleAll`` 的 SQL **没有** ``where``，连 ``del_flag`` 都不过滤。

        Java 里它没有任何调用者（Service 的 ``selectRoleAll`` 走的是
        ``selectRoleList``），这里照原样保留，**不要**"顺手补上 del_flag"。
        """
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_role_all()

        assert "where" not in factory.statement
        assert "del_flag = '0'" not in factory.statement

    def test_permission_by_user_id_filters_owner_and_del_flag(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_role_permission_by_user_id(1)

        assert "WHERE r.del_flag = '0' and ur.user_id = :user_id" in factory.statement
        assert factory.first_params == {"user_id": 1}

    def test_role_ids_by_user_id_returns_ids(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``resultType="Integer"`` —— 返回的是**角色 id**，不是行。"""
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[(2,), (3,)]))
        _patch(monkeypatch, sys_role_mapper, factory)

        assert SysRoleMapper().select_role_list_by_user_id(1) == [2, 3]

    def test_roles_by_user_name_filters_del_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_mapper

        factory = _SessionFactory(_Result(rows=[], keys=_ROLE_KEYS))
        _patch(monkeypatch, sys_role_mapper, factory)

        SysRoleMapper().select_roles_by_user_name("admin")

        assert "WHERE r.del_flag = '0' and u.user_name = :user_name" in factory.statement


# --------------------------------------------------------------------------- SysRoleMenuMapper


class TestRoleMenuMapper:
    def test_delete_by_role_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_menu_mapper

        factory = _SessionFactory(_Result(rowcount=3))
        _patch(monkeypatch, sys_role_menu_mapper, factory)

        assert SysRoleMenuMapper().delete_role_menu_by_role_id(2) == 3
        assert factory.statement == "delete from sys_role_menu where role_id=:role_id"
        assert factory.first_params == {"role_id": 2}

    def test_batch_delete_expands_the_foreach(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_menu_mapper

        factory = _SessionFactory(_Result(rowcount=4))
        _patch(monkeypatch, sys_role_menu_mapper, factory)

        SysRoleMenuMapper().delete_role_menu([2, 3])

        assert factory.statement == "delete from sys_role_menu where role_id in (:p0, :p1)"

    def test_batch_insert_is_row_per_menu(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_menu_mapper

        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, sys_role_menu_mapper, factory)

        rows = SysRoleMenuMapper().batch_role_menu(
            [SysRoleMenu(role_id=2, menu_id=100), SysRoleMenu(role_id=2, menu_id=101)]
        )

        assert rows == 2
        assert factory.statements == [
            "insert into sys_role_menu(role_id, menu_id) values (:role_id, :menu_id)"
        ]
        assert factory.params[0] == [
            {"role_id": 2, "menu_id": 100},
            {"role_id": 2, "menu_id": 101},
        ]

    def test_empty_batch_insert_sends_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_menu_mapper

        factory = _SessionFactory()
        _patch(monkeypatch, sys_role_menu_mapper, factory)

        assert SysRoleMenuMapper().batch_role_menu([]) == 0
        assert factory.statements == []

    def test_check_menu_exist_role(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_menu_mapper

        factory = _SessionFactory(_Result(scalar_value=2))
        _patch(monkeypatch, sys_role_menu_mapper, factory)

        assert SysRoleMenuMapper().check_menu_exist_role(100) == 2
        assert factory.statement == "select count(1) from sys_role_menu where menu_id = :menu_id"
        assert factory.first_params == {"menu_id": 100}


# --------------------------------------------------------------------------- SysRoleDeptMapper


class TestRoleDeptMapper:
    def test_delete_by_role_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_dept_mapper

        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, sys_role_dept_mapper, factory)

        assert SysRoleDeptMapper().delete_role_dept_by_role_id(2) == 1
        assert factory.statement == "delete from sys_role_dept where role_id=:role_id"

    def test_batch_delete_expands_the_foreach(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_dept_mapper

        factory = _SessionFactory(_Result(rowcount=2))
        _patch(monkeypatch, sys_role_dept_mapper, factory)

        SysRoleDeptMapper().delete_role_dept([2, 3])

        assert factory.statement == "delete from sys_role_dept where role_id in (:p0, :p1)"

    def test_batch_insert_is_row_per_dept(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_dept_mapper

        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, sys_role_dept_mapper, factory)

        SysRoleDeptMapper().batch_role_dept([SysRoleDept(role_id=2, dept_id=100)])

        assert factory.params[0] == [{"role_id": 2, "dept_id": 100}]

    def test_empty_batch_insert_sends_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_dept_mapper

        factory = _SessionFactory()
        _patch(monkeypatch, sys_role_dept_mapper, factory)

        assert SysRoleDeptMapper().batch_role_dept([]) == 0
        assert factory.statements == []

    def test_count_by_dept_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_role_dept_mapper

        factory = _SessionFactory(_Result(scalar_value=1))
        _patch(monkeypatch, sys_role_dept_mapper, factory)

        assert SysRoleDeptMapper().select_count_role_dept_by_dept_id(100) == 1
        assert factory.statement == "select count(1) from sys_role_dept where dept_id=:dept_id"
        assert factory.first_params == {"dept_id": 100}


# --------------------------------------------------------------------------- SysUserRoleMapper


class TestUserRoleMapper:
    def test_count_by_role_id_and_user_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_user_role_mapper

        factory = _SessionFactory(_Result(scalar_value=1))
        _patch(monkeypatch, sys_user_role_mapper, factory)

        rows = SysUserRoleMapper().count_user_role_by_role_id_user_id(2, 1)

        assert rows == 1
        assert factory.statement == (
            "select count(1) from sys_user_role where role_id=:role_id and user_id = :user_id"
        )
        assert factory.first_params == {"role_id": 2, "user_id": 1}

    def test_count_by_role_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.system.mapper import sys_user_role_mapper

        factory = _SessionFactory(_Result(scalar_value=3))
        _patch(monkeypatch, sys_user_role_mapper, factory)

        assert SysUserRoleMapper().count_user_role_by_role_id(2) == 3
