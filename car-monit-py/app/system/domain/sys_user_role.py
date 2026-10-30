"""用户和角色关联 sys_user_role.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUserRole.java

Java 里是**纯 POJO**（不继承 ``BaseEntity``），只用于给
``SysUserRoleMapper.batchUserRole`` 组装 ``(user_id, role_id)`` 行；
它从不出现在任何 HTTP 响应里，因此这里用 ``dataclass`` 而不是 pydantic 模型——
没有校验、没有序列化别名，与 Java 的"哑数据载体"职责一致。

对应的岗位版同构类是 :class:`app.system.domain.sys_user_post.SysUserPost`。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SysUserRole:
    """Java: ``SysUserRole``."""

    #: 用户ID
    user_id: Optional[int] = None
    #: 角色ID
    role_id: Optional[int] = None


__all__ = ["SysUserRole"]
