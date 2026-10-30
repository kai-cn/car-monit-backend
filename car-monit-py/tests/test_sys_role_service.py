"""``SysRoleService`` —— 业务规则.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysRoleServiceImpl.java

重点不是"有没有调 Mapper"，而是下面几条**改错了不报错**的规则：

* ``selectRoleAll`` 必须转调 ``selectRoleList``（为了让 ``@DataScope`` 生效），
  **不能**直接 ``roleMapper.selectRoleAll()``；
* ``checkRoleNameUnique`` / ``checkRoleKeyUnique`` 用 ``-1`` 表示"新增"，
  命中同一 ``roleId`` 不算重名；
* ``insertRoleMenu`` / ``insertRoleDept`` 的 ``rows`` 初值是 ``1`` ——
  不勾任何菜单/部门时接口仍然"成功"；
* ``menuIds`` / ``deptIds`` 为 ``None`` 时 Java 的 for-each 会 NPE（这里对应
  ``TypeError``），**不要**兜底成空集合；
* ``deleteRoleByIds`` 先逐个校验再动手，超管角色/已分配角色一律整批不删。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.exception.exceptions import CustomException
from app.framework.aspectj.data_scope_aspect import DATA_SCOPE
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.service.sys_role_service import ROLE_NOT_ALLOWED_MESSAGE, SysRoleService

# --------------------------------------------------------------------------- fakes


class _FakeRoleMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_queries: List[SysRole] = []
        self.list_result: List[SysRole] = []
        self.by_id: Dict[int, SysRole] = {}
        self.name_unique_info: Optional[SysRole] = None
        self.key_unique_info: Optional[SysRole] = None
        self.inserted: List[SysRole] = []
        self.updated: List[SysRole] = []
        self.deleted: List[int] = []
        self.deleted_batch: List[Sequence[int]] = []
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        self.delete_batch_result = 1
        #: 模拟 ``useGeneratedKeys``
        self.generated_id: Optional[int] = 77

    def select_role_list(self, role: SysRole) -> List[SysRole]:
        self.calls.append(("select_role_list", role))
        self.list_queries.append(role)
        return list(self.list_result)

    def select_role_all(self) -> List[SysRole]:  # pragma: no cover - 不应被调用
        self.calls.append(("select_role_all",))
        return []

    def select_role_by_id(self, role_id: int) -> Optional[SysRole]:
        self.calls.append(("select_role_by_id", role_id))
        return self.by_id.get(role_id)

    def check_role_name_unique(self, role_name: Optional[str]) -> Optional[SysRole]:
        self.calls.append(("check_role_name_unique", role_name))
        return self.name_unique_info

    def check_role_key_unique(self, role_key: Optional[str]) -> Optional[SysRole]:
        self.calls.append(("check_role_key_unique", role_key))
        return self.key_unique_info

    def insert_role(self, role: SysRole) -> int:
        self.calls.append(("insert_role", role))
        self.inserted.append(role)
        if self.generated_id is not None:
            role.role_id = self.generated_id
        return self.insert_result

    def update_role(self, role: SysRole) -> int:
        self.calls.append(("update_role", role))
        self.updated.append(role)
        return self.update_result

    def delete_role_by_id(self, role_id: int) -> int:
        self.calls.append(("delete_role_by_id", role_id))
        self.deleted.append(role_id)
        return self.delete_result

    def delete_role_by_ids(self, role_ids: Sequence[int]) -> int:
        self.calls.append(("delete_role_by_ids", list(role_ids)))
        self.deleted_batch.append(list(role_ids))
        return self.delete_batch_result

    def select_role_permission_by_user_id(self, user_id: int) -> List[SysRole]:
        self.calls.append(("select_role_permission_by_user_id", user_id))
        return []

    def names(self) -> List[str]:
        return [call[0] for call in self.calls]


class _FakeRoleMenuMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.deleted_by_role: List[int] = []
        self.deleted_batch: List[Sequence[int]] = []
        self.batches: List[List[Any]] = []
        self.batch_result = 2

    def delete_role_menu_by_role_id(self, role_id: int) -> int:
        self.calls.append(("delete_role_menu_by_role_id", role_id))
        self.deleted_by_role.append(role_id)
        return 1

    def delete_role_menu(self, role_ids: Sequence[int]) -> int:
        self.calls.append(("delete_role_menu", list(role_ids)))
        self.deleted_batch.append(list(role_ids))
        return 1

    def batch_role_menu(self, rows: List[Any]) -> int:
        self.calls.append(("batch_role_menu", list(rows)))
        self.batches.append(list(rows))
        return self.batch_result


class _FakeRoleDeptMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.deleted_by_role: List[int] = []
        self.deleted_batch: List[Sequence[int]] = []
        self.batches: List[List[Any]] = []
        self.batch_result = 3
        self.dept_counts: Dict[int, int] = {}

    def delete_role_dept_by_role_id(self, role_id: int) -> int:
        self.calls.append(("delete_role_dept_by_role_id", role_id))
        self.deleted_by_role.append(role_id)
        return 1

    def delete_role_dept(self, role_ids: Sequence[int]) -> int:
        self.calls.append(("delete_role_dept", list(role_ids)))
        self.deleted_batch.append(list(role_ids))
        return 1

    def batch_role_dept(self, rows: List[Any]) -> int:
        self.calls.append(("batch_role_dept", list(rows)))
        self.batches.append(list(rows))
        return self.batch_result

    def select_count_role_dept_by_dept_id(self, dept_id: int) -> int:
        self.calls.append(("select_count_role_dept_by_dept_id", dept_id))
        return self.dept_counts.get(dept_id, 0)


class _FakeUserRoleMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.counts: Dict[int, int] = {}
        self.pair_counts: Dict[tuple, int] = {}

    def count_user_role_by_role_id(self, role_id: int) -> int:
        self.calls.append(("count_user_role_by_role_id", role_id))
        return self.counts.get(role_id, 0)

    def count_user_role_by_role_id_user_id(self, role_id: int, user_id: int) -> int:
        self.calls.append(("count_user_role_by_role_id_user_id", role_id, user_id))
        return self.pair_counts.get((role_id, user_id), 0)


class _Bundle:
    def __init__(self) -> None:
        self.role_mapper = _FakeRoleMapper()
        self.role_menu_mapper = _FakeRoleMenuMapper()
        self.user_role_mapper = _FakeUserRoleMapper()
        self.role_dept_mapper = _FakeRoleDeptMapper()
        self.service = SysRoleService(
            mapper=self.role_mapper,
            role_menu_mapper=self.role_menu_mapper,
            user_role_mapper=self.user_role_mapper,
            role_dept_mapper=self.role_dept_mapper,
        )


@pytest.fixture(autouse=True)
def _isolate() -> Any:
    SecurityContextHolder.clear_context()
    yield
    SecurityContextHolder.clear_context()


@pytest.fixture()
def bundle() -> _Bundle:
    return _Bundle()


def authenticate(user: SysUser) -> LoginUser:
    login_user = LoginUser(user=user, permissions=set())
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return login_user


# --------------------------------------------------------------------------- @DataScope


class TestSelectRoleListDataScope:
    """Java: ``@DataScope(deptAlias = "d")``，而且这份 XML 的 ``${params.dataScope}``
    **不像** ``sys_dept`` 那样被注释掉 —— 片段真的会进 SQL。"""

    def test_the_fragment_is_written_into_the_entity_params(self, bundle: _Bundle) -> None:
        authenticate(SysUser(user_id=2, dept_id=100, roles=[SysRole(role_id=2, data_scope="3")]))
        role = SysRole()

        bundle.service.select_role_list(role)

        assert role.params[DATA_SCOPE] == " AND (d.dept_id = 100 )"
        assert bundle.role_mapper.list_queries == [role]

    def test_an_admin_is_never_filtered(self, bundle: _Bundle) -> None:
        authenticate(SysUser(user_id=1, dept_id=100, roles=[SysRole(role_id=2, data_scope="3")]))
        role = SysRole()

        bundle.service.select_role_list(role)

        assert DATA_SCOPE not in role.params

    def test_no_login_means_no_filter(self, bundle: _Bundle) -> None:
        role = SysRole()

        bundle.service.select_role_list(role)

        assert DATA_SCOPE not in role.params

    def test_select_role_all_goes_through_select_role_list(self, bundle: _Bundle) -> None:
        """Java: ``SpringUtils.getAopProxy(this).selectRoleList(new SysRole())``。

        必须走带 ``@DataScope`` 的那条路，否则返回的角色比 Java 多。
        """
        authenticate(SysUser(user_id=2, dept_id=100, roles=[SysRole(role_id=2, data_scope="3")]))

        bundle.service.select_role_all()

        assert "select_role_all" not in bundle.role_mapper.names()
        assert bundle.role_mapper.names() == ["select_role_list"]
        query = bundle.role_mapper.list_queries[0]
        assert query.params[DATA_SCOPE] == " AND (d.dept_id = 100 )"


# --------------------------------------------------------------------------- 唯一性


class TestUniqueChecks:
    def test_name_free_when_nothing_matches(self, bundle: _Bundle) -> None:
        assert bundle.service.check_role_name_unique(SysRole(role_name="新角色")) == "0"

    def test_name_taken_by_another_role(self, bundle: _Bundle) -> None:
        bundle.role_mapper.name_unique_info = SysRole(role_id=2)
        assert bundle.service.check_role_name_unique(SysRole(role_name="普通角色")) == "1"

    def test_the_same_role_is_not_a_duplicate(self, bundle: _Bundle) -> None:
        bundle.role_mapper.name_unique_info = SysRole(role_id=2)
        assert bundle.service.check_role_name_unique(SysRole(role_id=2, role_name="普通角色")) == "0"

    def test_a_missing_role_id_becomes_minus_one(self, bundle: _Bundle) -> None:
        """Java: ``StringUtils.isNull(role.getRoleId()) ? -1L : role.getRoleId()``。

        因此 ````roleId = -1`` 的真实数据…… 不存在（``role_id`` 是自增主键）。
        """
        bundle.role_mapper.name_unique_info = SysRole(role_id=-1)
        assert bundle.service.check_role_name_unique(SysRole()) == "0"

    def test_key_free_when_nothing_matches(self, bundle: _Bundle) -> None:
        assert bundle.service.check_role_key_unique(SysRole(role_key="new")) == "0"

    def test_key_taken_by_another_role(self, bundle: _Bundle) -> None:
        bundle.role_mapper.key_unique_info = SysRole(role_id=3)
        assert bundle.service.check_role_key_unique(SysRole(role_id=2, role_key="common")) == "1"

    def test_key_of_the_same_role_is_fine(self, bundle: _Bundle) -> None:
        bundle.role_mapper.key_unique_info = SysRole(role_id=2)
        assert bundle.service.check_role_key_unique(SysRole(role_id=2, role_key="common")) == "0"


# --------------------------------------------------------------------------- checkRoleAllowed


class TestCheckRoleAllowed:
    def test_role_one_is_rejected(self, bundle: _Bundle) -> None:
        with pytest.raises(CustomException) as excinfo:
            bundle.service.check_role_allowed(SysRole(role_id=1))
        assert str(excinfo.value) == ROLE_NOT_ALLOWED_MESSAGE == "不允许操作超级管理员角色"

    def test_any_other_role_passes(self, bundle: _Bundle) -> None:
        bundle.service.check_role_allowed(SysRole(role_id=2))

    def test_a_missing_role_id_passes(self, bundle: _Bundle) -> None:
        """``isNotNull(roleId) && role.isAdmin()`` —— 两个条件缺一不可。"""
        bundle.service.check_role_allowed(SysRole())


# --------------------------------------------------------------------------- 新增


class TestInsertRole:
    def test_no_menu_ids_still_reports_success(self, bundle: _Bundle) -> None:
        """``rows`` 初值为 1：不勾菜单时返回 1 -> ``toAjax(1)`` -> 操作成功。"""
        role = SysRole(role_name="新角色", role_key="new", menu_ids=[])

        rows = bundle.service.insert_role(role)

        assert rows == 1
        assert bundle.role_mapper.inserted == [role]
        assert bundle.role_menu_mapper.batches == []

    def test_menu_ids_are_written_with_the_generated_role_id(self, bundle: _Bundle) -> None:
        role = SysRole(role_name="新角色", menu_ids=[100, 101])

        rows = bundle.service.insert_role(role)

        assert rows == bundle.role_menu_mapper.batch_result
        assert role.role_id == 77
        rows_written = bundle.role_menu_mapper.batches[0]
        assert [(row.role_id, row.menu_id) for row in rows_written] == [(77, 100), (77, 101)]

    def test_null_menu_ids_raise_like_java(self, bundle: _Bundle) -> None:
        """Java 的 ``for (Long menuId : role.getMenuIds())`` 遇到 ``null`` 会 NPE。"""
        with pytest.raises(TypeError):
            bundle.service.insert_role(SysRole(role_name="新角色"))

    def test_the_role_is_inserted_before_the_menu_rows(self, bundle: _Bundle) -> None:
        bundle.service.insert_role(SysRole(role_name="新角色", menu_ids=[100]))
        assert bundle.role_mapper.names() == ["insert_role"]


# --------------------------------------------------------------------------- 修改


class TestUpdateRole:
    def test_menu_rows_are_rebuilt_not_merged(self, bundle: _Bundle) -> None:
        role = SysRole(role_id=2, role_name="普通角色", menu_ids=[100])

        rows = bundle.service.update_role(role)

        assert rows == bundle.role_menu_mapper.batch_result
        assert bundle.role_menu_mapper.deleted_by_role == [2]
        assert bundle.role_mapper.updated == [role]

    def test_an_empty_menu_list_clears_the_associations_but_returns_one(
        self, bundle: _Bundle
    ) -> None:
        """先全删，再因为 ``size() == 0`` 不插 —— 结果是"一个菜单都不给"，返回 1。"""
        rows = bundle.service.update_role(SysRole(role_id=2, menu_ids=[]))

        assert rows == 1
        assert bundle.role_menu_mapper.deleted_by_role == [2]
        assert bundle.role_menu_mapper.batches == []

    def test_update_role_status_does_not_touch_the_menu_table(self, bundle: _Bundle) -> None:
        """``changeStatus`` 走的是 ``updateRole``，但**不**重建菜单关联。"""
        rows = bundle.service.update_role_status(SysRole(role_id=2, status="1"))

        assert rows == bundle.role_mapper.update_result
        assert bundle.role_menu_mapper.calls == []


# --------------------------------------------------------------------------- 数据权限


class TestAuthDataScope:
    def test_dept_rows_are_rebuilt(self, bundle: _Bundle) -> None:
        role = SysRole(role_id=2, data_scope="2", dept_ids=[100, 101])

        rows = bundle.service.auth_data_scope(role)

        assert rows == bundle.role_dept_mapper.batch_result
        assert bundle.role_dept_mapper.deleted_by_role == [2]
        assert bundle.role_mapper.updated == [role]
        written = bundle.role_dept_mapper.batches[0]
        assert [(row.role_id, row.dept_id) for row in written] == [(2, 100), (2, 101)]

    def test_the_old_rows_are_deleted_even_when_the_scope_is_not_custom(
        self, bundle: _Bundle
    ) -> None:
        """范围改成 ``1``（全部数据）也会清空 ``sys_role_dept`` —— Java 原样。"""
        rows = bundle.service.auth_data_scope(SysRole(role_id=2, data_scope="1", dept_ids=[]))

        assert rows == 1
        assert bundle.role_dept_mapper.deleted_by_role == [2]

    def test_insert_role_dept_defaults_to_one_row(self, bundle: _Bundle) -> None:
        assert bundle.service.insert_role_dept(SysRole(role_id=2, dept_ids=[])) == 1

    def test_insert_role_dept_without_the_field_raises_like_java(self, bundle: _Bundle) -> None:
        with pytest.raises(TypeError):
            bundle.service.insert_role_dept(SysRole(role_id=2))


# --------------------------------------------------------------------------- 删除


class TestDeleteRoleByIds:
    def test_the_admin_role_is_rejected_before_anything_is_deleted(self, bundle: _Bundle) -> None:
        with pytest.raises(CustomException) as excinfo:
            bundle.service.delete_role_by_ids([1, 2])

        assert str(excinfo.value) == ROLE_NOT_ALLOWED_MESSAGE
        assert bundle.role_mapper.deleted_batch == []
        assert bundle.role_menu_mapper.deleted_batch == []

    def test_an_assigned_role_aborts_the_whole_batch(self, bundle: _Bundle) -> None:
        bundle.role_mapper.by_id[3] = SysRole(role_id=3, role_name="已分配角色")
        bundle.user_role_mapper.counts[3] = 2

        with pytest.raises(CustomException) as excinfo:
            bundle.service.delete_role_by_ids([3])

        assert str(excinfo.value) == "已分配角色已分配,不能删除"
        assert bundle.role_mapper.deleted_batch == []
        assert bundle.role_menu_mapper.deleted_batch == []
        assert bundle.role_dept_mapper.deleted_batch == []

    def test_a_missing_role_raises_a_null_pointer_like_java(self, bundle: _Bundle) -> None:
        """``selectRoleById`` 返回 ``null`` -> ``role.getRoleName()`` NPE。

        只有真的"角色还没被删、但用户关联数 > 0"时才取得到名称；反过来，
        角色不存在而计数为 0 是正常路径（不会进 if）。
        """
        bundle.user_role_mapper.counts[404] = 1
        with pytest.raises(AttributeError):
            bundle.service.delete_role_by_ids([404])

    def test_associations_are_deleted_before_the_role_row(self, bundle: _Bundle) -> None:
        bundle.role_mapper.by_id[2] = SysRole(role_id=2, role_name="普通角色")

        rows = bundle.service.delete_role_by_ids([2])

        assert rows == bundle.role_mapper.delete_batch_result
        assert bundle.role_menu_mapper.deleted_batch == [[2]]
        assert bundle.role_dept_mapper.deleted_batch == [[2]]
        assert bundle.role_mapper.deleted_batch == [[2]]

    def test_every_id_is_checked_before_any_delete(self, bundle: _Bundle) -> None:
        """第二个 id 不合格时，第一个 id 的校验已经跑过了，但一条都没删。"""
        bundle.role_mapper.by_id[2] = SysRole(role_id=2, role_name="普通角色")
        bundle.role_mapper.by_id[3] = SysRole(role_id=3, role_name="已分配角色")
        bundle.user_role_mapper.counts[2] = 0
        bundle.user_role_mapper.counts[3] = 1

        with pytest.raises(CustomException) as excinfo:
            bundle.service.delete_role_by_ids([2, 3])

        assert str(excinfo.value) == "已分配角色已分配,不能删除"
        assert bundle.user_role_mapper.calls == [
            ("count_user_role_by_role_id", 2),
            ("count_user_role_by_role_id", 3),
        ]
        assert bundle.role_mapper.deleted_batch == []

    def test_delete_role_by_id_has_no_guards(self, bundle: _Bundle) -> None:
        """单删版本没有 ``checkRoleAllowed`` / "已分配"校验 —— Java 原样。"""
        rows = bundle.service.delete_role_by_id(1)

        assert rows == bundle.role_mapper.delete_result
        assert bundle.role_mapper.deleted == [1]
        assert bundle.role_menu_mapper.deleted_by_role == [1]
        assert bundle.role_dept_mapper.deleted_by_role == [1]


# --------------------------------------------------------------------------- 计数


class TestCounts:
    def test_count_user_role_by_role_id(self, bundle: _Bundle) -> None:
        bundle.user_role_mapper.counts[2] = 4
        assert bundle.service.count_user_role_by_role_id(2) == 4

    def test_count_user_role_by_role_id_user_id(self, bundle: _Bundle) -> None:
        bundle.user_role_mapper.pair_counts[(2, 1)] = 1
        assert bundle.service.count_user_role_by_role_id_user_id(2, 1) == 1


# --------------------------------------------------------------------------- 权限集合


class TestRolePermissionKeys:
    def test_role_keys_are_split_on_commas(self) -> None:
        """Java: ``perm.getRoleKey().trim().split(",")`` —— ``trim()`` 只作用于整串，
        **不会**逐段去空格。所以 ``" a , b "`` 拆成 ``"a "`` / ``" b"``（带空格）。

        这是 ``@PreAuthorize`` 匹配不到的场景之一，但 Java 原样如此，不要"顺手"改成
        ``[part.strip() for part in ...]``。
        """

        class _Mapper:
            def select_role_permission_by_user_id(self, user_id: int) -> List[SysRole]:
                return [SysRole(role_id=2, role_key=" a , b "), SysRole(role_id=3, role_key="c")]

        service = SysRoleService(mapper=_Mapper())  # type: ignore[arg-type]

        assert service.select_role_permission_by_user_id(1) == {"a ", " b", "c"}

    def test_a_fully_trimmed_key_is_split_cleanly(self) -> None:
        class _Mapper:
            def select_role_permission_by_user_id(self, user_id: int) -> List[SysRole]:
                return [SysRole(role_id=2, role_key="admin,common")]

        service = SysRoleService(mapper=_Mapper())  # type: ignore[arg-type]

        assert service.select_role_permission_by_user_id(1) == {"admin", "common"}
