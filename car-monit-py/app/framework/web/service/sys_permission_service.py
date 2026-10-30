"""用户权限处理 / the shortcut that gives ``admin`` every permission.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysPermissionService.java

Two callers, two different destinations:

* ``UserDetailsServiceImpl.createLoginUser`` calls :meth:`get_menu_permission` while building
the ``LoginUser``, so the value cached in Redis under ``login_tokens:<uuid>`` already holds the
resolved permissions. They are not recomputed per request -- changing a role does not affect an
already-issued token until the user logs in again, which is the Java behaviour.
* ``SysLoginController.getInfo`` calls both methods on every ``GET /getInfo``; the results go
into the response body only, never back into the cached ``LoginUser``.

Why ``{"admin"}`` and ``{"*:*:*"}`` are different strings
---------------------------------------------------------
They are checked in different places and are **not** interchangeable:

* ``LoginUser.permissions`` (from :meth:`get_menu_permission`) is matched by
  ``SecurityUtils``/``PermissionService`` against ``@PreAuthorize("@ss.hasPermi('system:user:list')")``.
  ``"*:*:*"`` is the wildcard those helpers special-case.
* ``LoginUser.roles`` (from :meth:`get_role_permission`) is matched by
  ``@PreAuthorize("@ss.hasRole('admin')")``, so the literal must be ``"admin"``.

Swapping them would silently break every ``hasRole`` annotation for user ``admin``.

The non-admin branch returns whatever the database holds, including an **empty** set when the
user has no rows -- ``selectRolePermissionByUserId`` still returns ``["admin"]``-free data, and
``SysRoleServiceImpl`` never injects a default. A user without roles therefore has no
authorities at all, and Spring Security treats "no granted authority" as "denies everything"
rather than as an error.
"""

from __future__ import annotations

from typing import Optional, Set

from app.common.core.domain.entity.sys_user import SysUser
from app.system.service.sys_menu_service import SysMenuService, get_menu_service
from app.system.service.sys_role_service import SysRoleService, get_role_service

#: Java: ``roles.add("admin")`` -- the string ``@ss.hasRole('admin')`` compares against.
ADMIN_ROLE = "admin"

#: Java: ``perms.add("*:*:*")`` -- the wildcard ``@ss.hasPermi`` treats as "all".
ALL_PERMISSION = "*:*:*"


class SysPermissionService:
    """Java: ``@Component SysPermissionService``."""

    def __init__(
        self,
        role_service: Optional[SysRoleService] = None,
        menu_service: Optional[SysMenuService] = None,
    ) -> None:
        self._role_service = role_service
        self._menu_service = menu_service

    # Java: @Autowired private ISysRoleService roleService
    @property
    def role_service(self) -> SysRoleService:
        if self._role_service is None:
            self._role_service = get_role_service()
        return self._role_service

    # Java: @Autowired private ISysMenuService menuService
    @property
    def menu_service(self) -> SysMenuService:
        if self._menu_service is None:
            self._menu_service = get_menu_service()
        return self._menu_service

    # Java: public Set<String> getRolePermission(SysUser user)
    def get_role_permission(self, user: SysUser) -> Set[str]:
        """Roles of ``user``; ``{"admin"}`` short-circuits the query for user id 1.

        ``Set<String>`` is a ``HashSet`` in Java, i.e. **unordered**. A ``set`` keeps the same
        guarantee; iterating it must not be relied on to produce a stable order, and nothing in
        the codebase does (``LoginUser`` serialises it as a JSON array whose order is whatever
        the hash table yields).
        """
        roles: Set[str] = set()
        # 管理员拥有所有权限
        if user.admin:
            roles.add(ADMIN_ROLE)
        else:
            roles.update(self.role_service.select_role_permission_by_user_id(user.user_id))
        return roles

    # Java: public Set<String> getMenuPermission(SysUser user)
    def get_menu_permission(self, user: SysUser) -> Set[str]:
        """Menu permission strings of ``user``; ``{"*:*:*"}`` for user id 1."""
        perms: Set[str] = set()
        # 管理员拥有所有权限
        if user.admin:
            perms.add(ALL_PERMISSION)
        else:
            perms.update(self.menu_service.select_menu_perms_by_user_id(user.user_id))
        return perms


_SERVICE: Optional[SysPermissionService] = None


def get_permission_service() -> SysPermissionService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysPermissionService()
    return _SERVICE


def reset_permission_service() -> None:
    """Test helper: drop the cached service so fake role/menu services can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "ADMIN_ROLE",
    "ALL_PERMISSION",
    "SysPermissionService",
    "get_permission_service",
    "reset_permission_service",
]
