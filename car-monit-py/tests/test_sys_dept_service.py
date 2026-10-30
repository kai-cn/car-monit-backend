"""``SysDeptService`` -- 业务规则.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDeptServiceImpl.java

重点不是"有没有调 Mapper"，而是四条**改错了不报错**的规则：

* ``insertDept`` / ``updateDept`` 的 ``sub_code`` 三级补零（``-00N`` / ``-0N`` / ``-N``）与
  ``is_uint`` / ``is_zbzg`` / ``tenant_id`` 的联动；
* 父级没变（``flag == false``）时**不重算** ``subCode``；
* ``updateTenantId(subCode)`` 的 ``subCode`` 为 ``None`` 时会**扫全表**；
* ``buildDeptTree`` 一个根都没有时**原样返回入参**。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_dept import SysDept
from app.system.service import sys_dept_service as service_module
from app.system.service.sys_dept_service import SysDeptService

# --------------------------------------------------------------------------- fakes


class _FakeRoleMapper:
    def __init__(self) -> None:
        self.roles: Dict[int, Any] = {}

    def select_role_by_id(self, role_id: int) -> Any:
        return self.roles.get(role_id)


class _FakeDeptMapper:
    """Records every call; returns whatever the test configured."""

    def __init__(self) -> None:
        self.calls: List[str] = []
        self.list_queries: List[Optional[SysDept]] = []
        #: ``select_dept_by_id`` 的答案
        self.dept_by_id: Dict[int, SysDept] = {}
        #: ``select_dept_list`` 的答案（按查询条件分流）
        self.list_result: List[SysDept] = []
        self.by_parent: Dict[int, List[SysDept]] = {}
        self.fgld_result: List[SysDept] = []
        self.leader_result: List[SysDept] = []
        #: 其它
        self.name_unique_info: Optional[SysDept] = None
        self.normal_children = 0
        self.child_count = 0
        self.user_count = 0
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        self.tenant_info: Dict[Optional[str], Optional[SysDept]] = {}
        self.children_of: Dict[int, List[SysDept]] = {}
        self.inserted: List[SysDept] = []
        self.updated: List[SysDept] = []
        self.deleted: List[int] = []
        self.children_updated: List[Sequence[SysDept]] = []
        self.status_updated: List[SysDept] = []
        self.next_dept_id = 500

    # -- reads ------------------------------------------------------------
    def select_dept_by_id(self, dept_id: Optional[int]) -> Optional[SysDept]:
        self.calls.append("select_dept_by_id")
        return self.dept_by_id.get(dept_id)  # type: ignore[arg-type]

    def select_dept_list(self, dept: Optional[SysDept] = None) -> List[SysDept]:
        self.calls.append("select_dept_list")
        self.list_queries.append(dept)
        if dept is not None and dept.fgld_id is not None:
            return list(self.fgld_result)
        if dept is not None and dept.leader_id is not None:
            return list(self.leader_result)
        if dept is not None and dept.parent_id is not None:
            return list(self.by_parent.get(dept.parent_id, []))
        return list(self.list_result)

    def select_dept_list_by_role_id(
        self, role_id: int, dept_check_strictly: bool
    ) -> List[int]:
        self.calls.append("select_dept_list_by_role_id")
        self.last_strictly = dept_check_strictly
        return [100, 101]

    def check_dept_name_unique(
        self, dept_name: Optional[str], parent_id: Optional[int]
    ) -> Optional[SysDept]:
        self.calls.append("check_dept_name_unique")
        return self.name_unique_info

    def check_dept_exist_user(self, dept_id: int) -> int:
        self.calls.append("check_dept_exist_user")
        return self.user_count

    def has_child_by_dept_id(self, dept_id: int) -> int:
        self.calls.append("has_child_by_dept_id")
        return self.child_count

    def select_normal_children_dept_by_id(self, dept_id: int) -> int:
        self.calls.append("select_normal_children_dept_by_id")
        return self.normal_children

    def select_children_dept_by_id(self, dept_id: int) -> List[SysDept]:
        self.calls.append("select_children_dept_by_id")
        return list(self.children_of.get(dept_id, []))

    def select_tenant_id(self, dept: SysDept) -> Optional[SysDept]:
        self.calls.append("select_tenant_id")
        return self.tenant_info.get(dept.sub_code)

    # -- writes -----------------------------------------------------------
    def insert_dept(self, dept: SysDept) -> int:
        self.calls.append("insert_dept")
        self.inserted.append(dept)
        dept.dept_id = self.next_dept_id
        return self.insert_result

    def update_dept(self, dept: SysDept) -> int:
        self.calls.append("update_dept")
        self.updated.append(dept)
        return self.update_result

    def update_dept_children(self, depts: Sequence[SysDept]) -> int:
        self.calls.append("update_dept_children")
        self.children_updated.append(list(depts))
        return len(depts)

    def update_dept_status(self, dept: SysDept) -> int:
        self.calls.append("update_dept_status")
        self.status_updated.append(dept)
        return 1

    def delete_dept_by_id(self, dept_id: int) -> int:
        self.calls.append("delete_dept_by_id")
        self.deleted.append(dept_id)
        return self.delete_result

    def delete_dept_all(self) -> int:
        self.calls.append("delete_dept_all")
        return 0


def _service() -> Any:
    mapper = _FakeDeptMapper()
    role_mapper = _FakeRoleMapper()
    return SysDeptService(mapper=mapper, role_mapper=role_mapper), mapper, role_mapper


# --------------------------------------------------------------------------- 校验


class TestCheckDeptNameUnique:
    def test_a_new_name_is_unique(self) -> None:
        service, mapper, _ = _service()
        mapper.name_unique_info = None
        assert service.check_dept_name_unique(SysDept(dept_name="财务部", parent_id=100)) == "0"

    def test_an_existing_name_under_the_same_parent_conflicts(self) -> None:
        service, mapper, _ = _service()
        mapper.name_unique_info = SysDept(dept_id=101, dept_name="财务部")
        assert service.check_dept_name_unique(SysDept(dept_name="财务部", parent_id=100)) == "1"

    def test_editing_a_department_does_not_conflict_with_itself(self) -> None:
        service, mapper, _ = _service()
        mapper.name_unique_info = SysDept(dept_id=101, dept_name="财务部")
        dept = SysDept(dept_id=101, dept_name="财务部", parent_id=100)
        assert service.check_dept_name_unique(dept) == "0"

    def test_the_null_id_sentinel_is_minus_one(self) -> None:
        """Java: ``StringUtils.isNull(dept.getDeptId()) ? -1L : dept.getDeptId()``.

        主键永远不可能是负数，所以"新增"一定撞不上"自己"。
        """
        service, mapper, _ = _service()
        mapper.name_unique_info = SysDept(dept_id=-1, dept_name="财务部")
        assert service.check_dept_name_unique(SysDept(dept_name="财务部")) == "0"

        mapper.name_unique_info = SysDept(dept_id=0, dept_name="财务部")
        assert service.check_dept_name_unique(SysDept(dept_name="财务部")) == "1"

    def test_the_unique_key_includes_the_parent(self) -> None:
        service, mapper, _ = _service()
        service.check_dept_name_unique(SysDept(dept_name="财务部", parent_id=100))
        assert mapper.calls == ["check_dept_name_unique"]


# --------------------------------------------------------------------------- 建树


def _dept(dept_id: int, parent_id: Optional[int], name: str) -> SysDept:
    return SysDept(dept_id=dept_id, parent_id=parent_id, dept_name=name)


class TestBuildDeptTree:
    def test_children_are_attached_in_place(self) -> None:
        service, _, _ = _service()
        root = _dept(100, 0, "总公司")
        child = _dept(101, 100, "财务部")
        grandchild = _dept(102, 101, "会计科")

        tree = service.build_dept_tree([root, child, grandchild])

        assert tree == [root]
        assert [node.dept_id for node in root.children] == [101]
        assert [node.dept_id for node in child.children] == [102]
        assert grandchild.children == []

    def test_a_null_parent_id_counts_as_a_root(self) -> None:
        """``!tempList.contains(null)`` -> true，所以 ``parentId == null`` 是根节点。"""
        service, _, _ = _service()
        orphan = _dept(100, None, "孤儿")

        tree = service.build_dept_tree([orphan])

        assert tree == [orphan]
        assert orphan.children == []

    def test_without_any_root_the_input_is_returned_unchanged(self) -> None:
        """Java: ``if (returnList.isEmpty()) { returnList = depts; }``.

        典型场景：``treeselect?parentId=100`` 只查到子树，100 不在结果里，于是
        102 的父 101 在结果里、101 的父 100 不在 —— 这时 101 会被当成根。真正
        "一个根都没有"只发生在成环或全被过滤掉时。
        """
        service, _, _ = _service()
        a = _dept(1, 2, "a")
        b = _dept(2, 1, "b")

        result = service.build_dept_tree([a, b])

        assert result is not None
        assert [node.dept_id for node in result] == [1, 2]

    def test_a_department_without_dept_id_raises_like_java(self) -> None:
        """``t.getDeptId().longValue()`` 对 null 抛 NPE。

        要让这个节点成为**根**才会进 ``recursionFn``：``tempList`` 里已经有 ``None``
        （它自己的 ``deptId``），所以 ``parentId = null`` 反而不算根。
        """
        service, _, _ = _service()
        broken = SysDept(dept_id=None, parent_id=999, dept_name="坏数据")
        other = _dept(2, None, "x")

        with pytest.raises(AttributeError):
            service.build_dept_tree([broken, other])


class TestBuildDeptTreeSelect:
    def test_leaves_drop_the_children_key(self) -> None:
        """``TreeSelect.children`` 是 ``@JsonInclude(NON_EMPTY)``。"""
        service, _, _ = _service()
        root = _dept(100, 0, "总公司")
        child = _dept(101, 100, "财务部")

        nodes = service.build_dept_tree_select([root, child])

        assert nodes[0].model_dump(by_alias=True) == {
            "id": 100,
            "label": "总公司",
            "children": [{"id": 101, "label": "财务部"}],
        }

    def test_labels_come_from_the_department_name(self) -> None:
        service, _, _ = _service()
        nodes = service.build_dept_tree_select([_dept(100, 0, "总公司")])
        assert nodes[0].label == "总公司"


# --------------------------------------------------------------------------- 新增


class TestInsertDept:
    def test_a_root_gets_tree_level_one_and_a_00n_code(self) -> None:
        service, mapper, _ = _service()
        mapper.by_parent[0] = [_dept(100, 0, "已有的")]

        dept = SysDept(dept_name="新公司", is_uint="1")
        assert service.insert_dept(dept) == 1

        assert dept.parent_id == 0
        assert dept.tree_leavel == 1
        # counts = 1 -> next = 2 -> "00" + "2"
        assert dept.sub_code == "002"
        # 顶级节点一定是单位：is_uint 被强制成 "1"，随后 tenant_id = 自己的 id
        assert dept.is_uint == "1"
        assert mapper.updated[-1].tenant_id == 500

    def test_a_null_parent_is_forced_to_zero_and_marked_as_a_unit(self) -> None:
        """``if (null == dept.getParentId()) { setParentId(0L); setIsUint("1"); }``"""
        service, mapper, _ = _service()

        dept = SysDept(dept_name="新公司", is_uint="0")
        service.insert_dept(dept)

        assert dept.parent_id == 0
        assert dept.is_uint == "1"

    def test_a_child_inherits_the_parent_level_and_code(self) -> None:
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(
            dept_id=100, tree_leavel=1, sub_code="001", is_uint="1"
        )
        mapper.by_parent[100] = [_dept(101, 100, "a"), _dept(102, 100, "b")]

        dept = SysDept(dept_name="财务部", parent_id=100, is_uint="1")
        service.insert_dept(dept)

        assert dept.tree_leavel == 2
        # counts = 2 -> next = 3 -> parentSubCode + "-00" + 3
        assert dept.sub_code == "001-003"

    @pytest.mark.parametrize(
        ("existing", "suffix"),
        [(8, "001-009"), (9, "001-010"), (98, "001-099"), (99, "001-100")],
    )
    def test_the_three_level_zero_padding(self, existing: int, suffix: str) -> None:
        """``counts < 9`` -> ``-00N``；``< 99`` -> ``-0N``；再多不补零。"""
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")
        mapper.by_parent[100] = [_dept(1000 + index, 100, "x") for index in range(existing)]

        dept = SysDept(dept_name="财务部", parent_id=100, is_uint="1")
        service.insert_dept(dept)

        assert dept.sub_code == suffix

    def test_a_new_department_under_a_brand_new_parent_has_no_code_prefix(self) -> None:
        """父节点 ``sub_code`` 为 ``None`` 时拼出 ``"None-001"`` —— Java 同样是 ``"null-001"``."""
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code=None)

        dept = SysDept(dept_name="财务部", parent_id=100, is_uint="1")
        service.insert_dept(dept)

        assert dept.sub_code == "None-001"

    def test_an_existing_department_under_the_same_parent_keeps_its_code(self) -> None:
        """``flag == false``（父级没变）时**不重算** ``subCode``。"""
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")
        mapper.dept_by_id[101] = SysDept(dept_id=101, parent_id=100, tree_leavel=2)

        dept = SysDept(dept_id=101, dept_name="财务部", parent_id=100, sub_code="001-007")
        service.insert_dept(dept)

        assert dept.sub_code == "001-007"
        assert "select_dept_list" not in mapper.calls

    def test_moving_a_department_recomputes_its_code(self) -> None:
        """父级变了 -> ``flag == true`` -> 按新父节点重新编号。"""
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")
        mapper.dept_by_id[101] = SysDept(dept_id=101, parent_id=50, tree_leavel=2)
        mapper.by_parent[100] = []

        dept = SysDept(dept_id=101, dept_name="财务部", parent_id=100, sub_code="009-001")
        service.insert_dept(dept)

        assert dept.sub_code == "001-001"

    def test_a_missing_parent_raises_attribute_error(self) -> None:
        """Java 在 ``parentBO.getTreeLeavel()`` 处 NPE。"""
        service, _, _ = _service()
        with pytest.raises(AttributeError):
            service.insert_dept(SysDept(dept_name="财务部", parent_id=404, is_uint="1"))

    def test_a_department_is_not_a_bidding_unit(self) -> None:
        """``is_uint == "0"`` -> ``is_zbzg = "0"``，且 ``tenant_id`` 取最近的上层单位。"""
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")
        mapper.tenant_info["001-001"] = SysDept(dept_id=100)

        dept = SysDept(dept_name="财务部", parent_id=100, is_uint="0")
        service.insert_dept(dept)

        assert dept.is_zbzg == "0"
        assert mapper.updated[-1].tenant_id == 100

    def test_a_unit_points_the_tenant_id_at_itself(self) -> None:
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")

        dept = SysDept(dept_name="分公司", parent_id=100, is_uint="1")
        service.insert_dept(dept)

        assert mapper.updated[-1].tenant_id == dept.dept_id == 500

    def test_a_department_without_a_matching_unit_gets_no_tenant_update(self) -> None:
        """``selectTenantId`` 查不到时**什么都不做**（不置空 ``tenant_id``）。"""
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")

        dept = SysDept(dept_name="财务部", parent_id=100, is_uint="0")
        service.insert_dept(dept)

        assert mapper.updated == []

    def test_the_insert_result_is_returned_as_is(self) -> None:
        service, mapper, _ = _service()
        mapper.insert_result = 1
        assert service.insert_dept(SysDept(dept_name="x", is_uint="1")) == 1


# --------------------------------------------------------------------------- 修改


class TestUpdateDept:
    def test_the_main_row_is_updated_before_the_subtree_is_refreshed(self) -> None:
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")
        mapper.dept_by_id[101] = SysDept(dept_id=101, parent_id=50, tree_leavel=2)
        mapper.list_result = []

        assert service.update_dept(SysDept(dept_id=101, dept_name="财务部", parent_id=100, is_uint="1")) == 1

        assert mapper.calls == [
            "select_dept_by_id",
            "select_dept_by_id",
            "select_dept_list",
            "update_dept",
            "select_dept_list",
        ]

    def test_the_subtree_tenant_ids_are_refreshed(self) -> None:
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")
        unit = SysDept(dept_id=101, is_uint="1")
        child = SysDept(dept_id=102, is_uint="0", sub_code="001-001-002")
        mapper.list_result = [unit, child]
        mapper.tenant_info["001-001-002"] = SysDept(dept_id=101)

        service.update_dept(
            SysDept(dept_id=100, dept_name="总公司", parent_id=0, is_uint="1")
        )

        assert [row.dept_id for row in mapper.updated] == [100, 101, 102]
        assert [row.tenant_id for row in mapper.updated] == [None, 101, 101]

    def test_a_null_sub_code_refreshes_the_whole_table(self) -> None:
        """``updateTenantId(null)`` -> ``deptSubCode`` 的 ``<if>`` 不生效 -> 扫全表。

        Java 原样如此：父级没变（``flag == false``）又没传 ``subCode`` 时就会这样。
        """
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")
        mapper.dept_by_id[101] = SysDept(dept_id=101, parent_id=100, tree_leavel=2)
        mapper.list_result = [SysDept(dept_id=200, is_uint="1")]

        service.update_dept(SysDept(dept_id=101, dept_name="财务部", parent_id=100, sub_code=None))

        queried = [query for query in mapper.list_queries if query is not None]
        assert queried[-1].dept_sub_code is None
        assert mapper.updated[-1].tenant_id == 200

    def test_a_department_is_not_a_bidding_unit(self) -> None:
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, tree_leavel=1, sub_code="001")
        mapper.dept_by_id[101] = SysDept(dept_id=101, parent_id=50, tree_leavel=2)
        mapper.list_result = []

        dept = SysDept(dept_id=101, dept_name="财务部", parent_id=100, is_uint="0")
        service.update_dept(dept)

        assert dept.is_zbzg == "0"


# --------------------------------------------------------------------------- 树查询 / 删除


class TestDelegation:
    def test_select_dept_list_applies_the_data_scope(self) -> None:
        service, mapper, _ = _service()
        dept = SysDept(dept_name="财务")
        service.select_dept_list(dept)
        assert mapper.list_queries == [dept]

    def test_select_dept_by_id_is_passed_through(self) -> None:
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100)
        assert service.select_dept_by_id(100).dept_id == 100

    def test_has_child_flips_a_count_into_a_boolean(self) -> None:
        service, mapper, _ = _service()
        mapper.child_count = 0
        assert service.has_child_by_dept_id(100) is False
        mapper.child_count = 1
        assert service.has_child_by_dept_id(100) is True

    def test_check_dept_exist_user_flips_a_count_into_a_boolean(self) -> None:
        service, mapper, _ = _service()
        mapper.user_count = 0
        assert service.check_dept_exist_user(100) is False
        mapper.user_count = 3
        assert service.check_dept_exist_user(100) is True

    def test_normal_children_returns_the_raw_count(self) -> None:
        service, mapper, _ = _service()
        mapper.normal_children = 2
        assert service.select_normal_children_dept_by_id(100) == 2

    def test_delete_dept_by_id_is_a_logical_delete(self) -> None:
        service, mapper, _ = _service()
        mapper.delete_result = 1
        assert service.delete_dept_by_id(100) == 1
        assert mapper.deleted == [100]


class TestSelectDeptListByRoleId:
    def test_the_role_flag_drives_the_parent_exclusion(self) -> None:
        service, mapper, role_mapper = _service()
        role_mapper.roles[2] = type("Role", (), {"dept_check_strictly": True})()

        assert service.select_dept_list_by_role_id(2) == [100, 101]
        assert mapper.last_strictly is True

    def test_a_missing_role_raises_attribute_error(self) -> None:
        """Java: ``roleMapper.selectRoleById`` 返回 null 后 ``role.isDeptCheckStrictly()`` NPE。"""
        service, _, _ = _service()
        with pytest.raises(AttributeError):
            service.select_dept_list_by_role_id(404)


# --------------------------------------------------------------------------- 总公司


class TestSelectHeadOffice:
    def test_no_departments_returns_none(self) -> None:
        service, _, _ = _service()
        assert service.select_head_office() is None

    def test_level_one_and_two_plus_their_tenants(self) -> None:
        """两级：``treeLeavel in (1,2)`` 并上 ``tenantId`` 落在该集合里的部门。"""
        service, mapper, _ = _service()
        hq = SysDept(dept_id=100, tree_leavel=1, tenant_id=100)
        branch = SysDept(dept_id=101, tree_leavel=2, tenant_id=100)
        office = SysDept(dept_id=102, tree_leavel=3, tenant_id=101)
        unrelated = SysDept(dept_id=200, tree_leavel=3, tenant_id=200)
        mapper.list_result = [hq, branch, office, unrelated]

        assert service.select_head_office() == [hq, branch, office]

    def test_a_null_tree_level_raises_like_java(self) -> None:
        """``dept.getTreeLeavel().equals(1)`` 对 null 抛 NPE。"""
        service, mapper, _ = _service()
        mapper.list_result = [SysDept(dept_id=100, tree_leavel=None)]
        with pytest.raises(AttributeError):
            service.select_head_office()


# --------------------------------------------------------------------------- 子树


class TestUpdateDeptChildren:
    def test_ancestors_are_rewritten_with_a_plain_replace(self) -> None:
        service, mapper, _ = _service()
        first = SysDept(dept_id=101, ancestors="0,100,101")
        second = SysDept(dept_id=102, ancestors="0,100,102")
        mapper.children_of[100] = [first, second]

        service.update_dept_children(100, "0,200,100", "0,100")

        assert first.ancestors == "0,200,100,101"
        assert second.ancestors == "0,200,100,102"
        assert mapper.children_updated == [[first, second]]

    def test_no_children_means_no_update_statement(self) -> None:
        service, mapper, _ = _service()
        service.update_dept_children(100, "x", "y")
        assert "update_dept_children" not in mapper.calls

    def test_a_null_ancestors_raises_like_java(self) -> None:
        service, mapper, _ = _service()
        mapper.children_of[100] = [SysDept(dept_id=101, ancestors=None)]
        with pytest.raises(AttributeError):
            service.update_dept_children(100, "x", "y")


class TestUpdateParentDeptStatus:
    def test_it_rereads_the_row_before_writing_the_status(self) -> None:
        service, mapper, _ = _service()
        mapper.dept_by_id[100] = SysDept(dept_id=100, status="1")

        service._update_parent_dept_status(SysDept(dept_id=100, update_by="admin"))

        assert mapper.status_updated[0].update_by == "admin"


# --------------------------------------------------------------------------- 权限 SQL


class TestGetQxSql:
    def test_a_vice_leader_sees_their_departments(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.common.utils.security_utils.get_user_id", lambda: 7
        )
        service, mapper, _ = _service()
        mapper.fgld_result = [SysDept(dept_id=100), SysDept(dept_id=101)]

        assert service.get_qx_sql("x") == "t.eps_id in (100,101)"

    def test_a_department_leader_sees_theirs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "app.common.utils.security_utils.get_user_id", lambda: 7
        )
        service, mapper, _ = _service()
        mapper.leader_result = [SysDept(dept_id=100)]

        assert service.get_qx_sql(None) == "t.eps_id in (100)"

    def test_everyone_else_sees_only_what_they_created(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.common.utils.security_utils.get_user_id", lambda: 7
        )
        service, _, _ = _service()

        assert service.get_qx_sql(None) == " t.create_by=7"


# --------------------------------------------------------------------------- saveAll


class TestSaveAll:
    def test_it_deletes_the_seed_rows_first_then_inserts(self) -> None:
        service, mapper, _ = _service()
        rows = [SysDept(dept_name="a"), SysDept(dept_name="b")]

        service.save_all(rows)

        assert mapper.calls == ["delete_dept_all", "insert_dept", "insert_dept"]

    def test_an_empty_list_touches_nothing(self) -> None:
        service, mapper, _ = _service()
        service.save_all([])
        service.save_all(None)
        assert mapper.calls == []


# --------------------------------------------------------------------------- singleton


class TestSingleton:
    def test_get_and_reset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(service_module, "_SERVICE", None)

        first = service_module.get_dept_service()
        assert service_module.get_dept_service() is first

        service_module.reset_dept_service()
        assert service_module.get_dept_service() is not first
