"""角色和菜单关联 sys_role_menu.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysRoleMenu.java

与 :class:`app.system.domain.sys_user_role.SysUserRole` 一样，Java 里是**纯 POJO**
（不继承 ``BaseEntity``），只用于给 ``SysRoleMenuMapper.batchRoleMenu`` 组装
``(role_id, menu_id)`` 行；它从不出现在任何 HTTP 响应里，所以这里也是 ``dataclass``：
没有校验、没有序列化别名。

``roleId`` / ``menuId`` 在 Java 里都是 ``Long``（包装类型），因此可以为 ``null`` ——
``batchRoleMenu`` 会把 ``null`` 原样写进 SQL 参数，由 MySQL 的 ``NOT NULL`` 约束报错。
这里同样是 ``Optional[int]``，不做提前校验。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SysRoleMenu:
    """Java: ``SysRoleMenu``."""

    #: 角色ID
    role_id: Optional[int] = None
    #: 菜单ID
    menu_id: Optional[int] = None


__all__ = ["SysRoleMenu"]
