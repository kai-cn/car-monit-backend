"""菜单 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysMenuService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysMenuServiceImpl.java

Java 侧两处方法全部迁移：``ISysMenuService`` 接口 **15 个**，``SysMenuServiceImpl``
另有 7 个不在接口里的 public 方法（``getRouteName`` / ``getRouterPath`` / ``getComponent`` /
``isMenuFrame`` / ``isParentView`` / ``getChildPerms`` 等），合计 **22 个 public 方法**。

按用途分四组：

=========================================  ==========================================
Java                                       用途
=========================================  ==========================================
``selectMenuList(Long)``                   ``roleMenuTreeselect`` 用（无其他条件）
``selectMenuList(SysMenu, Long)``           管理页（根据 ``userId == 1`` 二选一）
``selectMenuPermsByUserId``               装 ``LoginUser``
``selectMenuTreeByUserId`` + ``buildMenus`` ``GET /getRouters``
``selectMenuListByRoleId``                 角色菜单树回填
``buildMenuTree`` / ``buildMenuTreeSelect`` ``treeselect`` / ``roleMenuTreeselect``
``selectMenuById`` / ``hasChildByMenuId``   详情 / 删除校验
``checkMenuExistRole``                     删除校验（转调 ``sys_role_menu``）
``insertMenu`` / ``updateMenu`` / ``deleteMenuById``
``checkMenuNameUnique``
``getRouteName`` / ``getRouterPath`` / ``getComponent`` / ``isMenuFrame`` /
``isParentView`` / ``getChildPerms``       路由构建的六个零件
=========================================  ==========================================

重载改名
--------
Java 的两个 ``selectMenuList`` 在 Python 里不能同名，因此：

======================  ==============================
Java                     Python
======================  ==============================
``selectMenuList(Long)``  :meth:`select_menu_list_for_user`
``selectMenuList(a, b)``  :meth:`select_menu_list`
======================  ==============================

``selectMenuPermsByRoleId`` 是**多迁的一层**
-------------------------------------------
Java 的 ``ISysMenuService`` / ``SysMenuServiceImpl`` 都**没有**这个方法，
``SysMenuMapper`` 接口也没有 —— 只有 XML 里那个孤立的 ``<select id="selectMenuPermsByRoleId">``。
Python 侧保留了 :meth:`select_menu_perms_by_role_id`（与上面那个方法对称、无调用者），
并在注释里标明“无 Java 对应” —— 它不参与任何端点，不影响行为。

``selectMenuPermsByUserId``
--------------------------
Java 读一行一个 ``perms`` 字符串，再*逐个按逗号拆*（一个菜单可以授多个权限）::

        List<String> perms = menuMapper.selectMenuPermsByUserId(userId);
        Set<String> permsSet = new HashSet<>();
        for (String perm : perms) {
            if (StringUtils.isNotEmpty(perm)) {
                permsSet.addAll(Arrays.asList(perm.trim().split(",")));
            }
        }

两个细节是故意保留的：

* ``isNotEmpty`` 是 RuoYi 自己的 ``StringUtils.isNotEmpty``，它**先 trim** ——
  ``perms`` 为 ``"   "`` 的行会被丢掉。
* ``split(",")`` 作用在**未 trim** 的原串上，会保留空段，于是 ``"a,,b"`` 得到
  ``{"a", "", "b"}``。只有整串被 trim，各段不会。

结果是 Java 的 ``HashSet``，即无序；Python 的 ``set`` 对应。

``selectMenuTreeByUserId`` + ``buildMenus``
------------------------------------------
``GET /getRouters`` 的管线。两阶段变换，不能混：

1. 行 -> **平铺列表**（超管走 ``selectMenuTreeAll``，其他人走 ``selectMenuTreeByUserId``），
   已按 ``parent_id, order_num`` 排好；
2. 平铺 -> **树**（``getChildPerms``），再 树 -> **RouterVo**（``buildMenus``）。

``getChildPerms`` 只留 ``parentId`` 恰好为 ``0`` 的节点（Java 传的是字面量 ``0L``）。
因此父节点不在结果集里的菜单（例如父目录被停用）会被**静默丢掉**，不会重新挂到
根下。这是 Java 行为，而且是**载重**的：停用一个目录就是靠它隐藏整个子树。

``selectMenuList`` 的两分支
---------------------------
::

        if (SysUser.isAdmin(userId)) {
            menuList = menuMapper.selectMenuList(menu);
        } else {
            menu.getParams().put("userId", userId);
            menuList = menuMapper.selectMenuListByUserId(menu);
        }

非超管分支**会写回** ``menu.params["userId"]``，并且用的是带三张表 ``left join``
的 SQL —— 也就是说“菜单管理”页对非超管而言看不到未授权的菜单。超管看全表。
"""

from __future__ import annotations

from typing import List, Optional, Set

from app.common.constant import user_constants as UserConstants
from app.common.core.domain.entity.sys_menu import SysMenu
from app.common.core.domain.tree_select import TreeSelect
from app.common.utils.security_utils import is_admin
from app.common.utils.string_utils import capitalize, is_empty, is_not_empty, java_trim
from app.system.domain.vo.meta_vo import MetaVo
from app.system.domain.vo.router_vo import RouterVo
from app.system.mapper.sys_menu_mapper import SysMenuMapper
from app.system.mapper.sys_role_mapper import SysRoleMapper
from app.system.mapper.sys_role_menu_mapper import SysRoleMenuMapper

#: Java: ``Constants.PERMISSION_DELIMETER``.
PERMISSION_DELIMETER = ","

#: Java: ``SysMenuServiceImpl.PREMISSION_STRING`` -- note the typo, it is Java's.
#: Only used by ``SysMenuController#roleMenuTreeselect``, migrated with the menu module.
PREMISSION_STRING = 'perms["{0}"]'

#: Java: ``router.setRedirect("noRedirect")`` -- the literal the Vue side compares against.
NO_REDIRECT = "noRedirect"


class SysMenuService:
    """Java: ``ISysMenuService`` (impl: ``SysMenuServiceImpl``)."""

    def __init__(
        self,
        mapper: Optional[SysMenuMapper] = None,
        role_mapper: Optional[SysRoleMapper] = None,
        role_menu_mapper: Optional[SysRoleMenuMapper] = None,
    ) -> None:
        self._mapper = mapper or SysMenuMapper()
        self._role_mapper = role_mapper or SysRoleMapper()
        self._role_menu_mapper = role_menu_mapper or SysRoleMenuMapper()

    @property
    def mapper(self) -> SysMenuMapper:
        return self._mapper

    # Java: @Autowired private SysRoleMapper roleMapper
    @property
    def role_mapper(self) -> SysRoleMapper:
        return self._role_mapper

    # Java: @Autowired private SysRoleMenuMapper roleMenuMapper
    @property
    def role_menu_mapper(self) -> SysRoleMenuMapper:
        return self._role_menu_mapper

    # ---------------------------------------------------------------- 管理页列表

    # Java: public List<SysMenu> selectMenuList(Long userId)
    def select_menu_list_for_user(self, user_id: int) -> List[SysMenu]:
        """Java 的单参重载 ``selectMenuList(Long userId)``；转调双参版本。

        名字里的 ``for_user`` 是为了避开 Python 不支持重载这件事（见模块 docstring）。
        """
        return self.select_menu_list(SysMenu(), user_id)

    # Java: public List<SysMenu> selectMenuList(SysMenu menu, Long userId)
    def select_menu_list(self, menu: SysMenu, user_id: int) -> List[SysMenu]:
        """超管走全表，其他人走“已授权菜单”的那条 SQL。

        非超管分支会把 ``userId`` 写进 ``menu.params`` —— 这是**副作用**，
        Java 原文如此（``menu.getParams().put("userId", userId)``）。
        """
        if is_admin(user_id):
            return self._mapper.select_menu_list(menu)
        menu.params["userId"] = user_id
        return self._mapper.select_menu_list_by_user_id(menu)

    # ---------------------------------------------------------------- 权限与树

    # Java: public Set<String> selectMenuPermsByUserId(Long userId)
    def select_menu_perms_by_user_id(self, user_id: int) -> Set[str]:
        """All permissions granted to a user through its roles."""
        perms_set: Set[str] = set()
        for perm in self._mapper.select_menu_perms_by_user_id(user_id):
            # Java: StringUtils.isNotEmpty(perm) -- trims before deciding.
            if is_not_empty(perm):
                perms_set.update(java_trim(perm).split(PERMISSION_DELIMETER))
        return perms_set

    # Java: 无 —— ISysMenuService / SysMenuMapper 都没有这个方法，只有 XML 的孤立 statement
    def select_menu_perms_by_role_id(self, role_id: int) -> Set[str]:
        """**无 Java 对应**：为 XML 里那个孤儿 ``<select id="selectMenuPermsByRoleId">`` 留的
        对称包装，全项目**无调用者**（见模块 docstring）。
        """
        perms_set: Set[str] = set()
        for perm in self._mapper.select_menu_perms_by_role_id(role_id):
            if is_not_empty(perm):
                perms_set.update(java_trim(perm).split(PERMISSION_DELIMETER))
        return perms_set

    # Java: public List<SysMenu> selectMenuTreeByUserId(Long userId)
    def select_menu_tree_by_user_id(self, user_id: int) -> List[SysMenu]:
        """Flat rows -> tree rooted at ``parentId == 0``.

        Admin (``userId == 1``) sees every enabled menu; everyone else only what their
        **enabled** roles grant. The mapper already applied ``order by m.parent_id,
        m.order_num``, so no sorting happens here.
        """
        if is_admin(user_id):
            menus = self._mapper.select_menu_tree_all()
        else:
            menus = self._mapper.select_menu_tree_by_user_id(user_id)
        return self.get_child_perms(menus, 0)

    # Java: public List<RouterVo> buildMenus(List<SysMenu> menus)
    def build_menus(self, menus: List[SysMenu]) -> List[RouterVo]:
        """Tree -> Vue router entries.

        The three branches, in Java's order:

        1. a **directory with children** -> nesting route: ``alwaysShow`` + ``redirect`` +
           recursive ``children``;
        2. a **top-level menu item** (``isMenuFrame``) -> one synthetic child and ``meta``
           cleared on the parent, so the sidebar renders a flat link;
        3. anything else -> just the computed name/path/component/meta.
        """
        routers: List[RouterVo] = []
        for menu in menus:
            router = RouterVo()
            # Java: router.setHidden("1".equals(menu.getVisible()))
            router.hidden = "1" == menu.visible
            router.name = self.get_route_name(menu)
            router.path = self.get_router_path(menu)
            router.component = self.get_component(menu)
            router.meta = self._build_meta(menu)

            child_menus = menu.children
            if len(child_menus) > 0 and UserConstants.TYPE_DIR == menu.menu_type:
                router.always_show = True
                router.redirect = NO_REDIRECT
                router.children = self.build_menus(child_menus)
            elif self.is_menu_frame(menu):
                # Java: router.setMeta(null) -- ``meta`` carries the title of the *parent*
                # route, which for a menu frame has no sidebar entry of its own.
                router.meta = None
                child = RouterVo()
                child.path = menu.path
                child.component = menu.component
                child.name = capitalize(menu.path)
                child.meta = self._build_meta(menu)
                router.children = [child]

            routers.append(router)
        return routers

    # Java: public List<Integer> selectMenuListByRoleId(Long roleId)
    def select_menu_list_by_role_id(self, role_id: int) -> List[int]:
        """角色已勾选的菜单 id。

        Java 先查角色、把 ``isMenuCheckStrictly()`` 一起传下去 ——
        这个开关决定“父节点勾了就不返回子节点”。角色不存在时 Java NPE，
        这里抛 ``AttributeError``（同一回事）。
        """
        role = self._role_mapper.select_role_by_id(role_id)
        return self._mapper.select_menu_list_by_role_id(role_id, role.menu_check_strictly)

    # Java: public List<SysMenu> buildMenuTree(List<SysMenu> menus)
    def build_menu_tree(self, menus: List[SysMenu]) -> List[SysMenu]:
        """把平铺列表就地建成树，返回根节点列表。

        ``parentId`` 不在本列表里的就是根。**一个根都没有时返回入参本身**
        （Java: ``returnList = menus``），此时列表是扁平的、每个节点的 ``children``
        还是 ``[]`` —— 前端会平铺展示。

        与 ``buildDeptTree`` 一字不差，但**故意不合并**，两个模块各自演化。
        """
        return_list: List[SysMenu] = []
        temp_list: List[Optional[int]] = []
        for menu in menus:
            temp_list.append(menu.menu_id)
        for menu in menus:
            # 如果是顶级节点, 遍历该父节点的所有子节点
            if menu.parent_id not in temp_list:
                self._recursion_fn(menus, menu)
                return_list.append(menu)
        if not return_list:
            return_list = menus
        return return_list

    # Java: public List<TreeSelect> buildMenuTreeSelect(List<SysMenu> menus)
    def build_menu_tree_select(self, menus: List[SysMenu]) -> List[TreeSelect]:
        """树 -> 下拉树。叶子节点的 ``children`` 键会整个消失（``NON_EMPTY``）。"""
        menu_trees = self.build_menu_tree(menus)
        return [TreeSelect.of_menu(menu) for menu in menu_trees]

    # ---------------------------------------------------------------- 详情与校验

    # Java: public SysMenu selectMenuById(Long menuId)
    def select_menu_by_id(self, menu_id: Optional[int]) -> Optional[SysMenu]:
        return self._mapper.select_menu_by_id(menu_id)

    # Java: public boolean hasChildByMenuId(Long menuId)
    def has_child_by_menu_id(self, menu_id: int) -> bool:
        return self._mapper.has_child_by_menu_id(menu_id) > 0

    # Java: public boolean checkMenuExistRole(Long menuId)
    def check_menu_exist_role(self, menu_id: int) -> bool:
        """菜单是否已被某个角色引用。走的是 **``sys_role_menu`` 的 mapper**，不是菜单表。"""
        return self._role_menu_mapper.check_menu_exist_role(menu_id) > 0

    # Java: public String checkMenuNameUnique(SysMenu menu)
    def check_menu_name_unique(self, menu: SysMenu) -> str:
        """``"1"`` = 冲突，``"0"`` = 唯一。

        ``menuId`` 缺失时用 ``-1`` 作哨兵（Java ``-1L``）—— 主键不可能是负数，
        所以“新增”永远撞不上“自己”。
        """
        menu_id = -1 if menu.menu_id is None else menu.menu_id
        info = self._mapper.check_menu_name_unique(menu.menu_name, menu.parent_id)
        if info is not None and info.menu_id != menu_id:
            return UserConstants.NOT_UNIQUE_OLD
        return UserConstants.UNIQUE_OLD

    # ---------------------------------------------------------------- 增删改

    # Java: public int insertMenu(SysMenu menu)
    def insert_menu(self, menu: SysMenu) -> int:
        """返回受影响行数（恒为 1）。**不回写** ``menu.menu_id``（§29）。"""
        return self._mapper.insert_menu(menu)

    # Java: public int updateMenu(SysMenu menu)
    def update_menu(self, menu: SysMenu) -> int:
        return self._mapper.update_menu(menu)

    # Java: public int deleteMenuById(Long menuId)
    def delete_menu_by_id(self, menu_id: int) -> int:
        """**物理删除**。``sys_menu`` 没有 ``del_flag``（``sys_dept`` / ``sys_role`` 有）。"""
        return self._mapper.delete_menu_by_id(menu_id)

    # ---------------------------------------------------------------- 路由零件

    # Java: public String getRouteName(SysMenu menu)
    def get_route_name(self, menu: SysMenu) -> Optional[str]:
        router_name = capitalize(menu.path)
        # 非外链并且是一级目录（类型为目录）-- the name is left empty on purpose: Vue uses
        # the parent's name as the route name, and a menu frame has no parent wrapper.
        if self.is_menu_frame(menu):
            router_name = ""
        return router_name

    # Java: public String getRouterPath(SysMenu menu)
    def get_router_path(self, menu: SysMenu) -> Optional[str]:
        router_path = menu.path
        # 非外链并且是一级目录（类型为目录）: prefix with "/" so Vue treats it as absolute.
        if (
            menu.parent_id == 0
            and UserConstants.TYPE_DIR == menu.menu_type
            and UserConstants.NO_FRAME == menu.is_frame
        ):
            # Java: "/" + menu.getPath(). Java string concatenation turns null into the
            # literal "null"; mirrored so a malformed row produces the same route.
            router_path = "/" + (menu.path if menu.path is not None else "null")
        # 非外链并且是一级目录（类型为菜单）
        elif self.is_menu_frame(menu):
            router_path = "/"
        return router_path

    # Java: public String getComponent(SysMenu menu)
    def get_component(self, menu: SysMenu) -> str:
        component = UserConstants.LAYOUT
        if is_not_empty(menu.component) and not self.is_menu_frame(menu):
            component = menu.component
        elif is_empty(menu.component) and self.is_parent_view(menu):
            component = UserConstants.PARENT_VIEW
        return component

    # Java: public boolean isMenuFrame(SysMenu menu)
    def is_menu_frame(self, menu: SysMenu) -> bool:
        """是否为菜单内部跳转.

        Java calls ``menu.getIsFrame().equals(NO_FRAME)`` and would NPE on a null
        ``is_frame``; comparing with ``==`` answers ``False`` instead. The column is
        ``NOT NULL DEFAULT '1'`` in ``sys_menu``, so the branch is unreachable.
        """
        return (
            menu.parent_id == 0
            and UserConstants.TYPE_MENU == menu.menu_type
            and menu.is_frame == UserConstants.NO_FRAME
        )

    # Java: public boolean isParentView(SysMenu menu)
    def is_parent_view(self, menu: SysMenu) -> bool:
        return menu.parent_id != 0 and UserConstants.TYPE_DIR == menu.menu_type

    # Java: public List<SysMenu> getChildPerms(List<SysMenu> list, Long parentId)
    def get_child_perms(self, menu_list: List[SysMenu], parent_id: int) -> List[SysMenu]:
        """Keep the direct children of ``parent_id`` and attach their descendants."""
        return_list: List[SysMenu] = []
        for menu in menu_list:
            # Java: t.getParentId().longValue() == parentId.longValue() -- NPE on null.
            if menu.parent_id is not None and menu.parent_id == parent_id:
                self._recursion_fn(menu_list, menu)
                return_list.append(menu)
        return return_list

    # Java: private void recursionFn(List<SysMenu> list, SysMenu t)
    def _recursion_fn(self, menu_list: List[SysMenu], menu: SysMenu) -> None:
        child_list = self._get_child_list(menu_list, menu)
        # Java: t.setChildren(childList) -- overwrites the entity, does not append.
        menu.children = child_list
        for child in child_list:
            if self._has_child(menu_list, child):
                self._recursion_fn(menu_list, child)

    # Java: private List<SysMenu> getChildList(List<SysMenu> list, SysMenu t)
    def _get_child_list(
        self, menu_list: List[SysMenu], menu: SysMenu
    ) -> List[SysMenu]:
        return [
            candidate
            for candidate in menu_list
            if candidate.parent_id is not None and candidate.parent_id == menu.menu_id
        ]

    # Java: private boolean hasChild(List<SysMenu> list, SysMenu t)
    def _has_child(self, menu_list: List[SysMenu], menu: SysMenu) -> bool:
        return len(self._get_child_list(menu_list, menu)) > 0

    @staticmethod
    def _build_meta(menu: SysMenu) -> MetaVo:
        """Java: ``new MetaVo(menu.getMenuName(), menu.getIcon(), "1".equals(menu.getIsCache()))``."""
        return MetaVo(
            title=menu.menu_name,
            icon=menu.icon,
            no_cache="1" == menu.is_cache,
        )


_SERVICE: Optional[SysMenuService] = None


def get_menu_service() -> SysMenuService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysMenuService()
    return _SERVICE


def reset_menu_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysMenuService",
    "PERMISSION_DELIMETER",
    "PREMISSION_STRING",
    "NO_REDIRECT",
    "get_menu_service",
    "reset_menu_service",
]
