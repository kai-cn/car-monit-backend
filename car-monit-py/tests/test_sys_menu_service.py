"""``SysMenuService`` —— 列表分支、树构建、路由零件、CRUD 委派.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysMenuServiceImpl.java

本文件盖住四类"改错了不报错、只换结果"的逻辑：

1. ``selectMenuList`` 的两分支（超管全表 / 非超管按角色）以及
   ``menu.params`` 被**写回**的副作用；
2. ``buildMenuTree`` 的"一个根都没有时返回入参本身"；
3. ``buildMenus`` 的三个分支（目录带子节点 / 顶部菜单项 / 其它）；
4. ``checkMenuNameUnique`` 的 ``-1`` 哨兵。
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

import pytest

from app.common.constant import user_constants as UserConstants
from app.common.core.domain.entity.sys_menu import SysMenu
from app.common.core.domain.tree_select import TreeSelect
from app.system.domain.vo.router_vo import RouterVo
from app.system.service.sys_menu_service import SysMenuService

# --------------------------------------------------------------------------- fakes


class _Menu:
    """Stand-in for ``SysRole`` (only ``selectRoleById`` is needed here)."""

    def __init__(self, menu_check_strictly: Optional[bool] = True) -> None:
        self.menu_check_strictly = menu_check_strictly


class _FakeMenuMapper:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, Any]] = []
        self.all: List[SysMenu] = []
        self.by_user: List[SysMenu] = []
        self.role_menu_ids: List[int] = [100, 101]
        self.perms: List[Optional[str]] = []
        self.by_id: Optional[SysMenu] = None
        self.child_count = 0
        self.unique_row: Optional[SysMenu] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1

    def select_menu_list(self, menu: SysMenu) -> List[SysMenu]:
        self.calls.append(("select_menu_list", menu))
        return self.all

    def select_menu_list_by_user_id(self, menu: SysMenu) -> List[SysMenu]:
        self.calls.append(("select_menu_list_by_user_id", menu))
        return self.by_user

    def select_menu_list_by_role_id(
        self, role_id: int, menu_check_strictly: bool
    ) -> List[int]:
        self.calls.append(("select_menu_list_by_role_id", (role_id, menu_check_strictly)))
        return self.role_menu_ids

    def select_menu_perms_by_user_id(self, user_id: int) -> List[Optional[str]]:
        self.calls.append(("select_menu_perms_by_user_id", user_id))
        return self.perms

    def select_menu_by_id(self, menu_id: int) -> Optional[SysMenu]:
        self.calls.append(("select_menu_by_id", menu_id))
        return self.by_id

    def has_child_by_menu_id(self, menu_id: int) -> int:
        self.calls.append(("has_child_by_menu_id", menu_id))
        return self.child_count

    def check_menu_name_unique(
        self, menu_name: Optional[str], parent_id: Optional[int]
    ) -> Optional[SysMenu]:
        self.calls.append(("check_menu_name_unique", (menu_name, parent_id)))
        return self.unique_row

    def insert_menu(self, menu: SysMenu) -> int:
        self.calls.append(("insert_menu", menu))
        return self.insert_result

    def update_menu(self, menu: SysMenu) -> int:
        self.calls.append(("update_menu", menu))
        return self.update_result

    def delete_menu_by_id(self, menu_id: int) -> int:
        self.calls.append(("delete_menu_by_id", menu_id))
        return self.delete_result

    def of(self, name: str) -> Any:
        return next(value for key, value in self.calls if key == name)


class _FakeRoleMapper:
    def __init__(self, role: Optional[_Menu] = None) -> None:
        self.calls: List[Tuple[str, Any]] = []
        self.role = role if role is not None else _Menu()

    def select_role_by_id(self, role_id: int) -> Optional[_Menu]:
        self.calls.append(("select_role_by_id", role_id))
        return self.role


class _FakeRoleMenuMapper:
    def __init__(self, count: int = 0) -> None:
        self.calls: List[Tuple[str, Any]] = []
        self.count = count

    def check_menu_exist_role(self, menu_id: int) -> int:
        self.calls.append(("check_menu_exist_role", menu_id))
        return self.count


def _service(
    menu_mapper: Optional[_FakeMenuMapper] = None,
    role_mapper: Optional[_FakeRoleMapper] = None,
    role_menu_mapper: Optional[_FakeRoleMenuMapper] = None,
) -> SysMenuService:
    return SysMenuService(
        menu_mapper or _FakeMenuMapper(),
        role_mapper or _FakeRoleMapper(),
        role_menu_mapper or _FakeRoleMenuMapper(),
    )


def _menu(
    menu_id: int,
    parent_id: int = 0,
    *,
    name: Optional[str] = None,
    menu_type: str = "C",
    path: Optional[str] = None,
    component: Optional[str] = None,
    is_frame: str = "1",
    visible: str = "0",
) -> SysMenu:
    """一行 ``selectMenuVo``，只填关心的字段。"""
    return SysMenu(
        menu_id=menu_id,
        parent_id=parent_id,
        menu_name=name if name is not None else f"菜单{menu_id}",
        menu_type=menu_type,
        path=path if path is not None else f"path{menu_id}",
        component=component,
        is_frame=is_frame,
        visible=visible,
    )


# --------------------------------------------------------------------------- selectMenuList


class TestSelectMenuListBranches:
    def test_admin_gets_the_unfiltered_query(self) -> None:
        mapper = _FakeMenuMapper()
        service = _service(mapper)
        menu = SysMenu(menu_name="用户")

        service.select_menu_list(menu, 1)

        assert [name for name, _ in mapper.calls] == ["select_menu_list"]
        # 超管分支**不**写 params
        assert menu.params == {}

    def test_normal_user_gets_the_role_join_and_the_user_id_is_written_back(self) -> None:
        """Java: ``menu.getParams().put("userId", userId)`` —— 副作用必须保留。"""
        mapper = _FakeMenuMapper()
        service = _service(mapper)
        menu = SysMenu()

        service.select_menu_list(menu, 7)

        assert [name for name, _ in mapper.calls] == ["select_menu_list_by_user_id"]
        assert menu.params["userId"] == 7
        assert mapper.of("select_menu_list_by_user_id") is menu

    def test_user_id_none_is_not_admin(self) -> None:
        """Java ``SysUser.isAdmin(null)`` 为 ``false`` -> 走按用户查。"""
        mapper = _FakeMenuMapper()
        service = _service(mapper)

        service.select_menu_list(SysMenu(), None)  # type: ignore[arg-type]

        assert [name for name, _ in mapper.calls] == ["select_menu_list_by_user_id"]

    def test_the_single_argument_overload_delegates_with_an_empty_filter(self) -> None:
        mapper = _FakeMenuMapper()
        service = _service(mapper)

        service.select_menu_list_for_user(1)

        passed = mapper.of("select_menu_list")
        assert isinstance(passed, SysMenu)
        assert passed.menu_name is None
        assert passed.params == {}

    def test_the_single_argument_overload_is_not_admin_only(self) -> None:
        mapper = _FakeMenuMapper()
        service = _service(mapper)

        service.select_menu_list_for_user(7)

        passed = mapper.of("select_menu_list_by_user_id")
        assert passed.params["userId"] == 7


# --------------------------------------------------------------------------- selectMenuListByRoleId


class TestSelectMenuListByRoleId:
    def test_strictly_flag_is_taken_from_the_role(self) -> None:
        mapper = _FakeMenuMapper()
        service = _service(mapper, _FakeRoleMapper(_Menu(menu_check_strictly=False)))

        assert service.select_menu_list_by_role_id(2) == [100, 101]

        assert mapper.calls == [("select_menu_list_by_role_id", (2, False))]

    def test_strictly_true_is_passed_through(self) -> None:
        mapper = _FakeMenuMapper()
        service = _service(mapper, _FakeRoleMapper(_Menu(menu_check_strictly=True)))

        service.select_menu_list_by_role_id(2)

        assert mapper.calls == [("select_menu_list_by_role_id", (2, True))]

    def test_missing_role_raises_like_the_java_npe(self) -> None:
        service = _service(_FakeMenuMapper(), _FakeRoleMapper(None))
        service.role_mapper.role = None  # type: ignore[attr-defined]

        with pytest.raises(AttributeError):
            service.select_menu_list_by_role_id(404)


# --------------------------------------------------------------------------- buildMenuTree


class TestBuildMenuTree:
    def test_nests_children_on_the_parent_instance(self) -> None:
        root = _menu(1, 0)
        child = _menu(2, 1)
        grandchild = _menu(3, 2)
        service = _service()

        tree = service.build_menu_tree([root, child, grandchild])

        assert tree == [root]
        assert root.children == [child]
        assert child.children == [grandchild]
        assert grandchild.children == []

    def test_no_root_returns_the_input_unchanged(self) -> None:
        """一个根都没有时 Java ``returnList = menus`` —— 平铺返回，不重新挂根。"""
        a = _menu(1, 2)
        b = _menu(2, 1)
        service = _service()
        menus = [a, b]

        tree = service.build_menu_tree(menus)

        assert tree is menus
        assert a.children == []
        assert b.children == []

    def test_siblings_keep_the_order_of_the_query(self) -> None:
        root = _menu(1, 0)
        first = _menu(3, 1)
        second = _menu(2, 1)
        service = _service()

        service.build_menu_tree([root, first, second])

        assert [child.menu_id for child in root.children] == [3, 2]

    def test_empty_list_stays_empty(self) -> None:
        assert _service().build_menu_tree([]) == []

    def test_two_roots_are_both_returned(self) -> None:
        one = _menu(1, 0)
        two = _menu(2, 0)
        service = _service()

        tree = service.build_menu_tree([one, two])

        assert tree == [one, two]


class TestBuildMenuTreeSelect:
    def test_leaf_has_no_children_key(self) -> None:
        root = _menu(1, 0, name="系统管理")
        child = _menu(2, 1, name="用户管理")
        service = _service()

        tree = service.build_menu_tree_select([root, child])

        dumped = tree[0].model_dump()
        assert dumped == {
            "id": 1,
            "label": "系统管理",
            "children": [{"id": 2, "label": "用户管理"}],
        }

    def test_it_returns_tree_select_instances(self) -> None:
        service = _service()

        tree = service.build_menu_tree_select([_menu(1, 0)])

        assert isinstance(tree[0], TreeSelect)


# --------------------------------------------------------------------------- 名称判重


class TestCheckMenuNameUnique:
    def test_same_id_is_unique(self) -> None:
        mapper = _FakeMenuMapper()
        mapper.unique_row = _menu(1)
        service = _service(mapper)

        assert service.check_menu_name_unique(SysMenu(menu_id=1, menu_name="x")) == (
            UserConstants.UNIQUE_OLD
        )
        assert mapper.calls == [("check_menu_name_unique", ("x", None))]

    def test_different_id_is_not_unique(self) -> None:
        mapper = _FakeMenuMapper()
        mapper.unique_row = _menu(1)
        service = _service(mapper)

        assert service.check_menu_name_unique(SysMenu(menu_id=2, menu_name="x")) == (
            UserConstants.NOT_UNIQUE_OLD
        )

    def test_missing_menu_id_uses_the_minus_one_sentinel(self) -> None:
        """新增时 ``menuId`` 为 ``null`` -> ``-1L``，所以永远撞不上自己。"""
        mapper = _FakeMenuMapper()
        mapper.unique_row = _menu(1)
        service = _service(mapper)

        assert service.check_menu_name_unique(SysMenu(menu_name="x")) == (
            UserConstants.NOT_UNIQUE_OLD
        )

    def test_no_row_is_unique(self) -> None:
        mapper = _FakeMenuMapper()
        service = _service(mapper)

        assert service.check_menu_name_unique(SysMenu(menu_name="x")) == UserConstants.UNIQUE_OLD


# --------------------------------------------------------------------------- 校验与详情


class TestGuards:
    def test_has_child_by_menu_id_is_a_count_comparison(self) -> None:
        mapper = _FakeMenuMapper()
        mapper.child_count = 2
        service = _service(mapper)

        assert service.has_child_by_menu_id(100) is True

    def test_no_child_returns_false(self) -> None:
        mapper = _FakeMenuMapper()
        service = _service(mapper)

        assert service.has_child_by_menu_id(100) is False

    def test_check_menu_exist_role_goes_through_the_role_menu_mapper(self) -> None:
        """Java: ``roleMenuMapper.checkMenuExistRole(menuId)`` —— 不是菜单表的 mapper。"""
        menu_mapper = _FakeMenuMapper()
        role_menu_mapper = _FakeRoleMenuMapper(count=1)
        service = _service(menu_mapper, role_menu_mapper=role_menu_mapper)

        assert service.check_menu_exist_role(100) is True
        assert role_menu_mapper.calls == [("check_menu_exist_role", 100)]
        assert menu_mapper.calls == []

    def test_check_menu_exist_role_false(self) -> None:
        service = _service(role_menu_mapper=_FakeRoleMenuMapper(count=0))

        assert service.check_menu_exist_role(100) is False

    def test_select_menu_by_id_delegates(self) -> None:
        mapper = _FakeMenuMapper()
        mapper.by_id = _menu(100)
        service = _service(mapper)

        assert service.select_menu_by_id(100) is mapper.by_id

    def test_select_menu_by_id_missing_is_none(self) -> None:
        assert _service().select_menu_by_id(404) is None


# --------------------------------------------------------------------------- CRUD 委派


class TestCrudDelegation:
    def test_insert_menu_returns_the_row_count_and_does_not_touch_the_id(self) -> None:
        """```insertMenu``` **没有** ``useGeneratedKeys`` -> ``menu.menu_id`` 保持 ``None``。"""
        mapper = _FakeMenuMapper()
        service = _service(mapper)
        menu = SysMenu(menu_name="新菜单")

        assert service.insert_menu(menu) == 1
        assert menu.menu_id is None
        assert mapper.calls == [("insert_menu", menu)]

    def test_update_menu_delegates(self) -> None:
        mapper = _FakeMenuMapper()
        mapper.update_result = 0
        service = _service(mapper)
        menu = SysMenu(menu_id=100)

        assert service.update_menu(menu) == 0
        assert mapper.calls == [("update_menu", menu)]

    def test_delete_menu_by_id_delegates(self) -> None:
        mapper = _FakeMenuMapper()
        service = _service(mapper)

        assert service.delete_menu_by_id(100) == 1
        assert mapper.calls == [("delete_menu_by_id", 100)]


# --------------------------------------------------------------------------- 路由零件


class TestIsMenuFrame:
    def test_top_level_menu_with_no_frame(self) -> None:
        service = _service()

        assert service.is_menu_frame(_menu(1, 0, menu_type="C", is_frame="1")) is True

    def test_a_child_is_never_a_menu_frame(self) -> None:
        service = _service()

        assert service.is_menu_frame(_menu(1, 5, menu_type="C", is_frame="1")) is False

    def test_a_directory_is_never_a_menu_frame(self) -> None:
        service = _service()

        assert service.is_menu_frame(_menu(1, 0, menu_type="M", is_frame="1")) is False

    def test_an_external_link_is_not_a_menu_frame(self) -> None:
        service = _service()

        assert service.is_menu_frame(_menu(1, 0, menu_type="C", is_frame="0")) is False


class TestIsParentView:
    def test_non_root_directory(self) -> None:
        service = _service()

        assert service.is_parent_view(_menu(1, 5, menu_type="M")) is True

    def test_root_directory_is_not_a_parent_view(self) -> None:
        service = _service()

        assert service.is_parent_view(_menu(1, 0, menu_type="M")) is False

    def test_a_menu_is_not_a_parent_view(self) -> None:
        service = _service()

        assert service.is_parent_view(_menu(1, 5, menu_type="C")) is False


class TestGetRouteName:
    def test_capitalises_the_path(self) -> None:
        service = _service()

        assert service.get_route_name(_menu(1, 5, path="user")) == "User"

    def test_menu_frame_has_an_empty_name(self) -> None:
        """``name: ""`` 会被 ``NON_EMPTY`` 整个吃掉 —— 见 ``RouterVo`` 的 docstring。"""
        service = _service()

        assert service.get_route_name(_menu(1, 0, menu_type="C", path="user")) == ""

    def test_null_path_becomes_null(self) -> None:
        service = _service()

        menu = SysMenu(menu_id=1, parent_id=5, path=None)
        assert service.get_route_name(menu) is None


class TestGetRouterPath:
    def test_top_level_directory_gets_a_leading_slash(self) -> None:
        service = _service()

        assert service.get_router_path(_menu(1, 0, menu_type="M", path="system")) == "/system"

    def test_menu_frame_collapses_to_slash(self) -> None:
        service = _service()

        assert service.get_router_path(_menu(1, 0, menu_type="C", path="user")) == "/"

    def test_a_nested_menu_keeps_its_path(self) -> None:
        service = _service()

        assert service.get_router_path(_menu(1, 5, menu_type="C", path="user")) == "user"

    def test_a_root_directory_that_is_external_keeps_its_path(self) -> None:
        """``isFrame = '0'``（外链）时第一个分支不成立。"""
        service = _service()

        assert (
            service.get_router_path(_menu(1, 0, menu_type="M", path="http://x", is_frame="0"))
            == "http://x"
        )


class TestGetComponent:
    def test_explicit_component_wins(self) -> None:
        service = _service()

        assert (
            service.get_component(_menu(1, 5, component="system/user/index"))
            == "system/user/index"
        )

    def test_nested_directory_without_component_is_parent_view(self) -> None:
        service = _service()

        assert service.get_component(_menu(1, 5, menu_type="M")) == UserConstants.PARENT_VIEW

    def test_everything_else_is_layout(self) -> None:
        service = _service()

        assert service.get_component(_menu(1, 0, menu_type="M")) == UserConstants.LAYOUT

    def test_menu_frame_ignores_the_component(self) -> None:
        """``isMenuFrame`` 为真时即使有 ``component`` 也用 ``Layout``。"""
        service = _service()

        assert (
            service.get_component(_menu(1, 0, menu_type="C", component="system/user/index"))
            == UserConstants.LAYOUT
        )

    def test_whitespace_component_falls_through(self) -> None:
        """``is_not_empty`` 先 trim —— 单个空格等于空串。"""
        service = _service()

        assert service.get_component(_menu(1, 5, menu_type="M", component=" ")) == (
            UserConstants.PARENT_VIEW
        )


# --------------------------------------------------------------------------- buildMenus


class TestBuildMenus:
    def test_directory_with_children_becomes_a_nested_route(self) -> None:
        root = _menu(1, 0, menu_type="M", path="system", name="系统管理")
        child = _menu(2, 1, menu_type="C", path="user", component="system/user/index")
        root.children = [child]
        service = _service()

        routers = service.build_menus([root])

        assert len(routers) == 1
        assert routers[0].always_show is True
        assert routers[0].redirect == "noRedirect"
        assert routers[0].path == "/system"
        assert routers[0].name == "System"
        assert routers[0].meta is not None
        assert routers[0].meta.title == "系统管理"
        assert len(routers[0].children or []) == 1

    def test_directory_without_children_is_not_nested(self) -> None:
        root = _menu(1, 0, menu_type="M", path="system")
        service = _service()

        routers = service.build_menus([root])

        assert routers[0].always_show is None
        assert routers[0].redirect is None
        assert routers[0].children is None

    def test_menu_frame_gets_one_synthetic_child_and_no_meta(self) -> None:
        root = _menu(1, 0, menu_type="C", path="user", component="system/user/index")
        service = _service()

        routers = service.build_menus([root])

        router = routers[0]
        assert router.meta is None
        assert router.path == "/"
        assert router.name == ""
        assert len(router.children or []) == 1
        assert router.children[0].path == "user"
        assert router.children[0].component == "system/user/index"
        assert router.children[0].name == "User"
        assert router.children[0].meta is not None

    def test_hidden_follows_the_visible_flag(self) -> None:
        service = _service()

        routers = service.build_menus([_menu(1, 5, visible="1")])

        assert routers[0].hidden is True

    def test_hidden_is_false_by_default(self) -> None:
        service = _service()

        assert service.build_menus([_menu(1, 5, visible="0")])[0].hidden is False

    def test_no_cache_flag_is_inverted(self) -> None:
        menu = _menu(1, 5)
        menu.is_cache = "1"
        service = _service()

        assert service.build_menus([menu])[0].meta.no_cache is True

    def test_empty_input_returns_an_empty_list(self) -> None:
        assert _service().build_menus([]) == []

    def test_children_are_built_recursively(self) -> None:
        root = _menu(1, 0, menu_type="M", path="system")
        middle = _menu(2, 1, menu_type="M", path="user")
        leaf = _menu(3, 2, menu_type="C", path="list", component="system/user/list")
        root.children = [middle]
        middle.children = [leaf]
        service = _service()

        routers = service.build_menus([root])

        middle_vo = (routers[0].children or [])[0]
        assert isinstance(middle_vo, RouterVo)
        # 只有 parentId == 0 的目录才补前导 "/"；这一层的 parentId 是 1。
        assert middle_vo.path == "user"
        assert (middle_vo.children or [])[0].component == "system/user/list"


# --------------------------------------------------------------------------- getChildPerms


class TestGetChildPerms:
    def test_orphans_are_dropped_not_reparented(self) -> None:
        """父节点不在结果集里的菜单会被静默丢掉 —— 停用目录就是靠这个隐藏子树。"""
        root = _menu(1, 0)
        orphan = _menu(9, 404)
        service = _service()

        tree = service.get_child_perms([root, orphan], 0)

        assert tree == [root]
        assert all(item.menu_id != 9 for item in tree)

    def test_only_the_requested_parent_is_kept(self) -> None:
        root = _menu(1, 0)
        child = _menu(2, 1)
        service = _service()

        tree = service.get_child_perms([root, child], 1)

        assert tree == [child]

    def test_empty_input_returns_an_empty_list(self) -> None:
        assert _service().get_child_perms([], 0) == []


# --------------------------------------------------------------------------- 权限拆分（回归）


class TestSelectMenuPermsByUserId:
    def test_comma_separated_values_are_split(self) -> None:
        mapper = _FakeMenuMapper()
        mapper.perms = ["system:user:list", "system:user:add,system:user:edit"]
        service = _service(mapper)

        assert service.select_menu_perms_by_user_id(7) == {
            "system:user:list",
            "system:user:add",
            "system:user:edit",
        }

    def test_whitespace_only_values_are_dropped(self) -> None:
        mapper = _FakeMenuMapper()
        mapper.perms = ["   ", None, ""]
        service = _service(mapper)

        assert service.select_menu_perms_by_user_id(7) == set()

    def test_empty_segments_are_kept(self) -> None:
        """```split(",")``` 作用在未 trim 的原串上 —— ``"a,,b"`` -> ``{"a", "", "b"}``。"""
        mapper = _FakeMenuMapper()
        mapper.perms = ["a,,b"]
        service = _service(mapper)

        assert service.select_menu_perms_by_user_id(7) == {"a", "", "b"}
