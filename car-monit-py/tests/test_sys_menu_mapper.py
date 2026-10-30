"""``SysMenuMapper`` —— SQL 拼接与结果映射.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml

为什么对**拼出来的 SQL** 断言
------------------------------
菜单 CRUD 的假 Mapper 会把 SQL 全遮住，而下面几处改错了不会报错、只会换结果集：

* ``selectMenuList`` / ``selectMenuListByUserId`` 的三个 ``<if>`` 判据是
  ``x != null and x != ''``（**不 trim**），用 ``is_not_empty`` 会漏掉"只填一个空格"；
* ``selectMenuListByUserId`` 的 ``userId`` 走 ``#{params.userId}``，不是实体字段；
* ``selectMenuListByRoleId`` 的 ``<if test="menuCheckStrictly">`` 是 **primitive
  boolean**，真分支会多一段 ``not in`` 子查询；
* ``insertMenu`` **没有** ``useGeneratedKeys`` —— 新增后拿不到 ``menuId``；
* ``updateMenu`` 里 ``component`` / ``visible`` / ``status`` / ``perms`` 只判 ``null``，
  传空串会**清列**，其余列会被整列跳过；
* ``deleteMenuById`` 是**物理删除**（``sys_menu`` 没有 ``del_flag``）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_menu import SysMenu
from app.system.mapper.sys_menu_mapper import SysMenuMapper

# --------------------------------------------------------------------------- fakes


class _Result:
    """One ``CursorResult``-shaped answer, with ``mappings()`` support."""

    def __init__(
        self,
        rows: Optional[Sequence[Mapping[str, Any]]] = None,
        scalar_value: Any = None,
        rowcount: int = 0,
        lastrowid: Optional[int] = None,
    ) -> None:
        self._rows = [dict(row) if isinstance(row, Mapping) else row for row in rows or []]
        self._scalar = scalar_value
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def mappings(self) -> "_Result":
        return self

    def all(self) -> List[Mapping[str, Any]]:
        return list(self._rows)

    def first(self) -> Optional[Mapping[str, Any]]:
        return self._rows[0] if self._rows else None

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


#: ``selectMenuVo`` / ``_TREE_COLUMNS`` 共用的 14 个列标签。
_MENU_KEYS: Sequence[str] = (
    "menu_id",
    "menu_name",
    "parent_id",
    "order_num",
    "path",
    "component",
    "is_frame",
    "is_cache",
    "menu_type",
    "visible",
    "status",
    "perms",
    "icon",
    "create_time",
)


def _row(**overrides: Any) -> Dict[str, Any]:
    """一行 ``selectMenuVo`` 结果，按 :data:`_MENU_KEYS` 排。"""
    values: Dict[str, Any] = {
        "menu_id": 100,
        "menu_name": "用户管理",
        "parent_id": 1,
        "order_num": "1",
        "path": "user",
        "component": "system/user/index",
        "is_frame": "1",
        "is_cache": "0",
        "menu_type": "C",
        "visible": "0",
        "status": "0",
        "perms": "system:user:list",
        "icon": "user",
        "create_time": None,
    }
    values.update(overrides)
    return {key: values[key] for key in _MENU_KEYS}


def _patch(monkeypatch: pytest.MonkeyPatch, factory: _SessionFactory) -> None:
    from app.system.mapper import sys_menu_mapper

    monkeypatch.setattr(sys_menu_mapper, "session_scope", factory)


# --------------------------------------------------------------------------- selectMenuList


class TestSelectMenuList:
    def test_no_filters_emits_no_where(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``<where>`` 在无条件时什么都不输出 —— 与手写 ``where 1=1`` 不同。"""
        factory = _SessionFactory(_Result(rows=[_row()]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_list(SysMenu())

        assert " where " not in factory.statement
        assert factory.statement.startswith("select menu_id, menu_name, parent_id")
        assert factory.statement.endswith("from sys_menu order by parent_id, order_num")

    def test_three_filters_in_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_list(
            SysMenu(menu_name="用户", visible="0", status="0")
        )

        where = factory.statement.split("from sys_menu")[1]
        assert where.index("menu_name like") < where.index("visible =")
        assert where.index("visible =") < where.index("status =")
        assert factory.first_params == {
            "menu_name": "用户",
            "visible": "0",
            "status": "0",
        }

    def test_menu_name_is_a_like_but_not_the_others(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_list(SysMenu(menu_name="用户", status="0"))

        assert "menu_name like concat('%', :menu_name, '%')" in factory.statement
        assert "status = :status" in factory.statement

    def test_a_single_space_still_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``x != ''`` 对单个空格为真。用 ``is_not_empty``（先 trim）会漏掉这条。"""
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_list(SysMenu(menu_name=" "))

        assert "menu_name like" in factory.statement
        assert factory.first_params == {"menu_name": " "}

    def test_empty_string_is_treated_as_null(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_list(SysMenu(menu_name="", visible="", status=""))

        assert " where " not in factory.statement

    def test_rows_are_mapped_including_ifnull_perms(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[_row(perms="")]))
        _patch(monkeypatch, factory)

        menu = SysMenuMapper().select_menu_list(SysMenu())[0]

        assert menu.menu_id == 100
        assert menu.menu_name == "用户管理"
        assert menu.parent_id == 1
        assert menu.order_num == "1"
        assert menu.component == "system/user/index"
        assert menu.menu_type == "C"
        # resultMap 里没有 parent_name / remark / create_by -> 恒为 None
        assert menu.parent_name is None
        assert menu.remark is None
        assert menu.create_by is None
        assert menu.children == []


# --------------------------------------------------------------------------- selectMenuListByUserId


class TestSelectMenuListByUserId:
    def test_joins_three_tables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_list_by_user_id(SysMenu())

        for join in (
            "left join sys_role_menu rm on m.menu_id = rm.menu_id",
            "left join sys_user_role ur on rm.role_id = ur.role_id",
            "left join sys_role ro on ur.role_id = ro.role_id",
        ):
            assert join in factory.statement

    def test_user_id_comes_from_params_not_from_a_field(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java: ``menu.getParams().put("userId", userId)`` + ``#{params.userId}``."""
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        menu = SysMenu()
        menu.params["userId"] = 7
        SysMenuMapper().select_menu_list_by_user_id(menu)

        assert "where ur.user_id = :user_id" in factory.statement
        assert factory.first_params["user_id"] == 7

    def test_no_menu_type_or_status_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """管理页要看得见停用菜单 —— 与 ``selectMenuTreeByUserId`` 的关键差异。"""
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        menu = SysMenu()
        menu.params["userId"] = 7
        SysMenuMapper().select_menu_list_by_user_id(menu)

        assert "menu_type in" not in factory.statement
        assert "m.status = 0" not in factory.statement
        assert "ro.status = 0" not in factory.statement

    def test_filters_are_aliased_and_ordered(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        menu = SysMenu(menu_name="用户", visible="0", status="0")
        menu.params["userId"] = 7
        SysMenuMapper().select_menu_list_by_user_id(menu)

        where = factory.statement.split("where ur.user_id = :user_id")[1]
        assert "where m.menu_name like concat('%', :menu_name, '%')" in where
        assert "AND m.visible = :visible" in where
        assert "AND m.status = :status" in where
        assert where.index("m.menu_name") < where.index("m.visible") < where.index("m.status")
        assert factory.statement.endswith("order by m.parent_id, m.order_num")


# --------------------------------------------------------------------------- selectMenuListByRoleId


class TestSelectMenuListByRoleId:
    def test_non_strict_has_no_not_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[(100,), (101,)]))
        _patch(monkeypatch, factory)

        result = SysMenuMapper().select_menu_list_by_role_id(2, False)

        assert result == [100, 101]
        assert "not in" not in factory.statement
        assert factory.statement.endswith("order by m.parent_id, m.order_num")
        assert factory.first_params == {"role_id": 2}

    def test_strict_adds_the_not_in_subquery(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``menuCheckStrictly`` 为真 => 剔除“父节点已勾选”的子节点。"""
        factory = _SessionFactory(_Result(rows=[(100,)]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_list_by_role_id(2, True)

        assert "and m.menu_id not in (select m.parent_id from sys_menu m inner join sys_role_menu rm" in factory.statement
        # 子查询与主查询各用一次 :role_id —— 同一个命名参数，绑定一次
        assert factory.statement.count(":role_id") == 2
        assert factory.first_params == {"role_id": 2}

    def test_only_the_menu_id_column_is_selected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_list_by_role_id(2, False)

        assert factory.statement.startswith("select m.menu_id from sys_menu m")


# --------------------------------------------------------------------------- 其余查询


class TestSelectMenuPerms:
    def test_has_no_where_at_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """XML 里这条没有 ``where`` —— 死代码，但仍要能跑（迁移原则第 4 条）。"""
        factory = _SessionFactory(_Result(rows=[("system:user:list",)]))
        _patch(monkeypatch, factory)

        assert SysMenuMapper().select_menu_perms() == ["system:user:list"]
        assert " where " not in factory.statement


class TestSelectMenuById:
    def test_where_is_only_the_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``sys_menu`` 没有 ``del_flag``，所以不存在软删过滤。"""
        factory = _SessionFactory(_Result(rows=[_row()]))
        _patch(monkeypatch, factory)

        SysMenuMapper().select_menu_by_id(100)

        assert factory.statement.endswith("from sys_menu where menu_id = :menu_id")
        assert "del_flag" not in factory.statement
        assert factory.first_params == {"menu_id": 100}

    def test_missing_row_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        assert SysMenuMapper().select_menu_by_id(404) is None


class TestHasChildByMenuId:
    def test_counts_by_parent_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(scalar_value=3))
        _patch(monkeypatch, factory)

        assert SysMenuMapper().has_child_by_menu_id(100) == 3
        assert factory.statement == "select count(1) from sys_menu where parent_id = :menu_id"

    def test_null_scalar_becomes_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(scalar_value=None))
        _patch(monkeypatch, factory)

        assert SysMenuMapper().has_child_by_menu_id(100) == 0


class TestCheckMenuNameUnique:
    def test_limit_one_belongs_to_the_sql(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[_row()]))
        _patch(monkeypatch, factory)

        SysMenuMapper().check_menu_name_unique("用户管理", 1)

        assert factory.statement.endswith(
            "where menu_name = :menu_name and parent_id = :parent_id limit 1"
        )
        assert "del_flag" not in factory.statement
        assert factory.first_params == {"menu_name": "用户管理", "parent_id": 1}

    def test_no_row_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rows=[]))
        _patch(monkeypatch, factory)

        assert SysMenuMapper().check_menu_name_unique("x", 1) is None


# --------------------------------------------------------------------------- insertMenu


class TestInsertMenu:
    def test_minimal_menu_writes_only_create_time(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().insert_menu(SysMenu())

        assert factory.statement == (
            "insert into sys_menu(create_time)values(sysdate())"
        )
        assert factory.first_params == {}

    def test_all_columns_in_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().insert_menu(
            SysMenu(
                menu_id=0,
                parent_id=1,
                menu_name="用户管理",
                order_num="1",
                path="user",
                component="system/user/index",
                is_frame="1",
                is_cache="0",
                menu_type="C",
                visible="0",
                status="0",
                perms="system:user:list",
                icon="user",
                remark="备注",
                create_by="admin",
            )
        )

        assert factory.statement == (
            "insert into sys_menu("
            "parent_id,menu_name,order_num,path,component,is_frame,is_cache,menu_type,"
            "visible,status,perms,icon,remark,create_by,create_time"
            ")values("
            ":parent_id,:menu_name,:order_num,:path,:component,:is_frame,:is_cache,"
            ":menu_type,:visible,:status,:perms,:icon,:remark,:create_by,sysdate()"
            ")"
        )
        # menu_id == 0 -> 整列不出现（自增）
        assert "menu_id" not in factory.statement.split("values")[0]

    def test_parent_id_zero_is_dropped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``parentId != null and parentId != 0`` —— 根节点的 0 不写库。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().insert_menu(SysMenu(parent_id=0, menu_name="根目录"))

        assert "parent_id" not in factory.statement
        assert factory.first_params == {"menu_name": "根目录"}

    def test_menu_id_is_written_when_non_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().insert_menu(SysMenu(menu_id=2000, menu_name="固定 id"))

        assert factory.statement.startswith(
            "insert into sys_menu(menu_id,menu_name,create_time)"
        )
        assert factory.first_params == {"menu_id": 2000, "menu_name": "固定 id"}

    def test_empty_strings_are_dropped_except_the_null_only_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``visible`` / ``status`` 只判 ``null``，空串**照写**；其余空串整列跳过。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().insert_menu(
            SysMenu(menu_name="", component="", visible="", status="")
        )

        assert factory.statement == (
            "insert into sys_menu(visible,status,create_time)values(:visible,:status,sysdate())"
        )
        assert factory.first_params == {"visible": "", "status": ""}

    def test_no_generated_key_is_written_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``insertMenu`` **没有** ``useGeneratedKeys`` —— 与其它模块相反。"""
        factory = _SessionFactory(_Result(rowcount=1, lastrowid=999))
        _patch(monkeypatch, factory)

        menu = SysMenu(menu_name="新菜单")
        assert SysMenuMapper().insert_menu(menu) == 1
        assert menu.menu_id is None


# --------------------------------------------------------------------------- updateMenu


class TestUpdateMenu:
    def test_update_time_is_always_last(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().update_menu(SysMenu(menu_id=100, menu_name="改名"))

        assert factory.statement == (
            "update sys_menu set menu_name = :menu_name, update_time = sysdate() "
            "where menu_id = :menu_id"
        )
        assert factory.first_params == {"menu_name": "改名", "menu_id": 100}

    def test_only_menu_id_still_emits_a_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``update_time = sysdate()`` 是无条件的，所以 ``<set>`` 永远非空。"""
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        SysMenuMapper().update_menu(SysMenu(menu_id=100))

        assert factory.statement == (
            "update sys_menu set update_time = sysdate() where menu_id = :menu_id"
        )

    def test_all_columns_in_xml_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().update_menu(
            SysMenu(
                menu_id=100,
                menu_name="用户管理",
                parent_id=1,
                order_num="1",
                path="user",
                component="system/user/index",
                is_frame="1",
                is_cache="0",
                menu_type="C",
                visible="0",
                status="0",
                perms="system:user:list",
                icon="user",
                remark="备注",
                update_by="admin",
            )
        )

        assert factory.statement == (
            "update sys_menu set "
            "menu_name = :menu_name, parent_id = :parent_id, order_num = :order_num, "
            "path = :path, component = :component, is_frame = :is_frame, "
            "is_cache = :is_cache, menu_type = :menu_type, visible = :visible, "
            "status = :status, perms = :perms, icon = :icon, remark = :remark, "
            "update_by = :update_by, update_time = sysdate() "
            "where menu_id = :menu_id"
        )

    def test_empty_string_clears_the_null_only_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``component`` / ``visible`` / ``status`` / ``perms`` 只判 ``null`` -> 空串清列。"""
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().update_menu(
            SysMenu(menu_id=100, component="", visible="", status="", perms="")
        )

        assert factory.statement == (
            "update sys_menu set component = :component, visible = :visible, "
            "status = :status, perms = :perms, update_time = sysdate() "
            "where menu_id = :menu_id"
        )
        assert factory.first_params == {
            "component": "",
            "visible": "",
            "status": "",
            "perms": "",
            "menu_id": 100,
        }

    def test_empty_string_skips_the_other_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        SysMenuMapper().update_menu(
            SysMenu(menu_id=100, menu_name="", path="", icon="", update_by="", remark="")
        )

        assert factory.statement == (
            "update sys_menu set update_time = sysdate() where menu_id = :menu_id"
        )


# --------------------------------------------------------------------------- deleteMenuById


class TestDeleteMenuById:
    def test_it_is_a_hard_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=1))
        _patch(monkeypatch, factory)

        assert SysMenuMapper().delete_menu_by_id(100) == 1
        assert factory.statement == "delete from sys_menu where menu_id = :menu_id"
        assert factory.first_params == {"menu_id": 100}

    def test_missing_row_returns_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        factory = _SessionFactory(_Result(rowcount=0))
        _patch(monkeypatch, factory)

        assert SysMenuMapper().delete_menu_by_id(404) == 0
