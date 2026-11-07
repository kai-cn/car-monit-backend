"""角色 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysRoleService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysRoleServiceImpl.java

Java original
-------------
``selectRolePermissionByUserId`` turns the user's roles into a set of **role keys**, splitting
each ``role_key`` on commas because one role row may declare several keys::

    List<SysRole> perms = roleMapper.selectRolePermissionByUserId(userId);
    Set<String> permsSet = new HashSet<>();
    for (SysRole perm : perms) {
        if (StringUtils.isNotNull(perm)) {
            permsSet.addAll(Arrays.asList(perm.getRoleKey().trim().split(",")));
        }
    }

``roleKey`` is ``NOT NULL`` in the schema, so ``getRoleKey().trim()`` cannot NPE here; the
Python port keeps the same assumption instead of inventing a fallback.

Where the result is used
------------------------
``SysPermissionService.getRolePermission`` (admin short-circuits to ``{"admin"}``). Milestone 1
does not expose a role-key-based check yet, but ``GET /getInfo`` returns the set, so it has to
be built from the very first login.

``selectRoleAll`` 为什么必须走 ``selectRoleList``
----------------------------------------------
Java 里它是::

    return SpringUtils.getAopProxy(this).selectRoleList(new SysRole());

刻意绕了一圈 AOP 代理，就是为了让 ``@DataScope`` 生效。因此 Python 版也必须调用
:meth:`select_role_list`（内部会 ``apply_data_scope``），**不能**直接
``roleMapper.selectRoleAll()`` —— 后者的 SQL 没有 ``${params.dataScope}``，会多返回角色。
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Set

from app.common.constant.user_constants import NOT_UNIQUE_OLD, UNIQUE_OLD
from app.common.core.domain.entity.sys_role import SysRole
from app.common.exception.exceptions import CustomException
from app.common.utils.string_utils import java_trim
from app.framework.aspectj.data_scope_aspect import apply_data_scope
from app.system.domain.sys_role_dept import SysRoleDept
from app.system.domain.sys_role_menu import SysRoleMenu
from app.system.mapper.sys_role_dept_mapper import SysRoleDeptMapper
from app.system.mapper.sys_role_mapper import SysRoleMapper
from app.system.mapper.sys_role_menu_mapper import SysRoleMenuMapper
from app.system.mapper.sys_user_role_mapper import SysUserRoleMapper
from app.config.database import transactional

#: Java: ``Constants.ROLE_DELIMETER``.
ROLE_DELIMETER = ","

#: Java: ``checkRoleAllowed`` 的文案（超级管理员角色不可操作）。
ROLE_NOT_ALLOWED_MESSAGE = "不允许操作超级管理员角色"


class SysRoleService:
    """Java: ``ISysRoleService`` (impl: ``SysRoleServiceImpl``)."""

    def __init__(
        self,
        mapper: Optional[SysRoleMapper] = None,
        role_menu_mapper: Optional[SysRoleMenuMapper] = None,
        user_role_mapper: Optional[SysUserRoleMapper] = None,
        role_dept_mapper: Optional[SysRoleDeptMapper] = None,
    ) -> None:
        self._mapper = mapper or SysRoleMapper()
        self._role_menu_mapper = role_menu_mapper or SysRoleMenuMapper()
        self._user_role_mapper = user_role_mapper or SysUserRoleMapper()
        self._role_dept_mapper = role_dept_mapper or SysRoleDeptMapper()

    @property
    def mapper(self) -> SysRoleMapper:
        return self._mapper

    # Java: @Autowired private SysRoleMenuMapper roleMenuMapper
    @property
    def role_menu_mapper(self) -> SysRoleMenuMapper:
        return self._role_menu_mapper

    # Java: @Autowired private SysUserRoleMapper userRoleMapper
    @property
    def user_role_mapper(self) -> SysUserRoleMapper:
        return self._user_role_mapper

    # Java: @Autowired private SysRoleDeptMapper roleDeptMapper
    @property
    def role_dept_mapper(self) -> SysRoleDeptMapper:
        return self._role_dept_mapper

    # Java: public Set<String> selectRolePermissionByUserId(Long userId)
    def select_role_permission_by_user_id(self, user_id: int) -> Set[str]:
        """Role keys granted to a user (not role ids, and not role names)."""
        perms_set: Set[str] = set()
        for role in self._mapper.select_role_permission_by_user_id(user_id):
            if role is not None:
                perms_set.update(java_trim(role.role_key).split(ROLE_DELIMETER))
        return perms_set

    # Java: public List<SysRole> selectRoleList(SysRole role)
    def select_role_list(self, role: SysRole) -> List[SysRole]:
        """根据条件分页查询角色数据.

        Java: ``@DataScope(deptAlias = "d")``。本方法**真的**会用到片段：
        ``SysRoleMapper.xml#selectRoleList`` 里的 ``${params.dataScope}`` 没有被注释。
        """
        apply_data_scope(role, "d")
        return self._mapper.select_role_list(role)

    # Java: public List<SysRole> selectRoleAll()
    def select_role_all(self) -> List[SysRole]:
        """查询所有角色.

        Java 走 ``SpringUtils.getAopProxy(this).selectRoleList(new SysRole())``，即为让
        ``@DataScope`` 生效而故意经过代理。这里直接调 :meth:`select_role_list`，
        数据权限结果一致。
        """
        return self.select_role_list(SysRole())

    # Java: public List<Integer> selectRoleListByUserId(Long userId)
    def select_role_list_by_user_id(self, user_id: int) -> List[int]:
        """角色下拉框回显用的**角色 id 列表**。"""
        return self._mapper.select_role_list_by_user_id(user_id)

    # Java: public SysRole selectRoleById(Long roleId)
    def select_role_by_id(self, role_id: int) -> Optional[SysRole]:
        return self._mapper.select_role_by_id(role_id)

    # Java: public List<SysRole> selectRolesByUserName(String userName)
    def select_roles_by_user_name(self, user_name: str) -> List[SysRole]:
        return self._mapper.select_roles_by_user_name(user_name)

    # ------------------------------------------------------------------ 校验

    # Java: String checkRoleNameUnique(SysRole role)
    def check_role_name_unique(self, role: SysRole) -> str:
        """角色名称唯一性。返回 ``"1"``（重名）/ ``"0"``（可用）。

        缺省用 ``-1`` 查自己：新增时 ``roleId`` 为空，任何同名行都算重名；修改时把
        “自己那一行”排除在重名之外。与 :meth:`SysDeptService.check_dept_name_unique`
        同构，只是这里 Mapper 返回整行而不是计数。
        """
        role_id = -1 if role.role_id is None else role.role_id
        info = self._mapper.check_role_name_unique(role.role_name)
        if info is not None and info.role_id != role_id:
            return NOT_UNIQUE_OLD
        return UNIQUE_OLD

    # Java: String checkRoleKeyUnique(SysRole role)
    def check_role_key_unique(self, role: SysRole) -> str:
        """权限字符唯一性，判据同 :meth:`check_role_name_unique`。"""
        role_id = -1 if role.role_id is None else role.role_id
        info = self._mapper.check_role_key_unique(role.role_key)
        if info is not None and info.role_id != role_id:
            return NOT_UNIQUE_OLD
        return UNIQUE_OLD

    # Java: void checkRoleAllowed(SysRole role)
    def check_role_allowed(self, role: SysRole) -> None:
        """禁止操作超级管理员角色。

        两个条件缺一不可：``roleId`` 非空**且**等于 ``1``。所以 ``roleId`` 缺省的请求
        （理论上不可能，但别“优化”掉）不会报错；而 ``roleId = 1`` 一律抛
        ``CustomException`` -> HTTP 200 + ``code 500`` + ``不允许操作超级管理员角色``。
        """
        if role.role_id is not None and role.is_admin(role.role_id):
            raise CustomException(ROLE_NOT_ALLOWED_MESSAGE)

    # Java: int countUserRoleByRoleId(Long roleId)
    def count_user_role_by_role_id(self, role_id: int) -> int:
        return self._user_role_mapper.count_user_role_by_role_id(role_id)

    # Java: int countUserRoleByRoleIdUserId(Long roleId, Long userId)
    def count_user_role_by_role_id_user_id(self, role_id: int, user_id: int) -> int:
        return self._user_role_mapper.count_user_role_by_role_id_user_id(role_id, user_id)

    # ------------------------------------------------------------------ 增删改

    # Java: int insertRole(SysRole role)
    @transactional
    def insert_role(self, role: SysRole) -> int:
        """新增角色 + 菜单关联。

        Java: ``@Transactional``。返回值是 **insertRoleMenu 的行数**，不是 insert 的行数
        （插入本身恒为 1 行）—— 所以没有勾选任何菜单时返回 ``1``，接口仍是“操作成功”。
        """
        # 新增角色信息
        self._mapper.insert_role(role)
        return self.insert_role_menu(role)

    # Java: int updateRole(SysRole role)
    @transactional
    def update_role(self, role: SysRole) -> int:
        """修改角色 + 重建菜单关联（先全删再插，**不是**合并）。"""
        # 修改角色信息
        self._mapper.update_role(role)
        # 删除角色与菜单关联
        self._role_menu_mapper.delete_role_menu_by_role_id(role.role_id)
        return self.insert_role_menu(role)

    # Java: int updateRoleStatus(SysRole role)
    def update_role_status(self, role: SysRole) -> int:
        """状态修改走的是整行动态更新（``updateRole``），不动菜单关联。"""
        return self._mapper.update_role(role)

    # Java: int authDataScope(SysRole role)
    @transactional
    def auth_data_scope(self, role: SysRole) -> int:
        """修改数据权限：先删 ``sys_role_dept`` 再按 ``deptIds`` 重建。

        不管本次 ``dataScope`` 是不是 ``2``（自定义），都先清空这张表 —— Java 原样。
        因此把范围从 ``2`` 改成 ``1`` 会把旧的自定义部门一起清掉。
        """
        # 修改角色信息
        self._mapper.update_role(role)
        # 删除角色与部门关联
        self._role_dept_mapper.delete_role_dept_by_role_id(role.role_id)
        # 新增角色和部门信息（数据权限）
        return self.insert_role_dept(role)

    # Java: public int insertRoleMenu(SysRole role)
    def insert_role_menu(self, role: SysRole) -> int:
        """新增角色菜单信息。Java 里没有 ``private``，所以是公开方法；保持公开。

        ``rows`` 初值就是 ``1``：一个菜单都没选时直接返回 1，与 Java 一致。
        ``role.menu_ids`` 为 ``None`` 时 Java 的 ``for-each`` 会 NPE（接口 500），
        所以这里**不**写 ``role.menu_ids or []``。
        """
        rows = 1
        # 新增用户与角色管理
        menu_list: List[SysRoleMenu] = []
        for menu_id in role.menu_ids:  # type: ignore[union-attr]
            menu_list.append(SysRoleMenu(role_id=role.role_id, menu_id=menu_id))
        if len(menu_list) > 0:
            rows = self._role_menu_mapper.batch_role_menu(menu_list)
        return rows

    # Java: public int insertRoleDept(SysRole role)
    def insert_role_dept(self, role: SysRole) -> int:
        """新增角色部门信息（数据权限）。同 :meth:`insert_role_menu`：空集合返回 1。"""
        rows = 1
        # 新增角色与部门（数据权限）管理
        dept_list: List[SysRoleDept] = []
        for dept_id in role.dept_ids:  # type: ignore[union-attr]
            dept_list.append(SysRoleDept(role_id=role.role_id, dept_id=dept_id))
        if len(dept_list) > 0:
            rows = self._role_dept_mapper.batch_role_dept(dept_list)
        return rows

    # Java: int deleteRoleById(Long roleId)
    @transactional
    def delete_role_by_id(self, role_id: int) -> int:
        """删除单个角色（软删），先清两张关联表。

        注意：这个方法**不做** ``checkRoleAllowed`` 与“已分配”校验 ——
        Java 里只有 ``deleteRoleByIds`` 里有那两道拦截，单删版本是内部/管理后台专用的
        捷径。控制器只调 ``deleteRoleByIds``。
        """
        # 删除角色与菜单关联
        self._role_menu_mapper.delete_role_menu_by_role_id(role_id)
        # 删除角色与部门关联
        self._role_dept_mapper.delete_role_dept_by_role_id(role_id)
        return self._mapper.delete_role_by_id(role_id)

    # Java: int deleteRoleByIds(Long[] roleIds)
    @transactional
    def delete_role_by_ids(self, role_ids: Sequence[int]) -> int:
        """批量删除。先**逐个**校验，全部通过才动数据。

        三道拦截与它们的顺序（决定了报错文案）：

        1. ``checkRoleAllowed`` —— ``roleId == 1`` -> ``不允许操作超级管理员角色``；
        2. ``countUserRoleByRoleId > 0`` -> ``%s已分配,不能删除``（``%s`` 是**角色名称**）；
        3. 任一角色不过就直接抛异常，前面的校验可能已经跑过，但一条数据都没删。

        ``role.getRoleName()`` 在角色不存在时会 NPE（``selectRoleById`` 返回 ``null``）
        —— Python 侧对应 ``AttributeError``，同样落到通用处理器（HTTP 200 + 500）。
        """
        for role_id in role_ids:
            self.check_role_allowed(SysRole(role_id=role_id))
            role = self.select_role_by_id(role_id)
            if self.count_user_role_by_role_id(role_id) > 0:
                raise CustomException("%s已分配,不能删除" % role.role_name)
        # 删除角色与菜单关联
        self._role_menu_mapper.delete_role_menu(role_ids)
        # 删除角色与部门关联
        self._role_dept_mapper.delete_role_dept(role_ids)
        return self._mapper.delete_role_by_ids(role_ids)


_SERVICE: Optional[SysRoleService] = None


def get_role_service() -> SysRoleService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysRoleService()
    return _SERVICE


def reset_role_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysRoleService",
    "ROLE_DELIMETER",
    "ROLE_NOT_ALLOWED_MESSAGE",
    "get_role_service",
    "reset_role_service",
]
