"""用户与岗位关联 sys_user_post.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUserPost.java

与 :class:`app.system.domain.sys_user_role.SysUserRole` 同构：纯数据载体，
只为 ``SysUserPostMapper.batchUserPost`` 组装 ``(user_id, post_id)`` 行。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SysUserPost:
    """Java: ``SysUserPost``."""

    #: 用户ID
    user_id: Optional[int] = None
    #: 岗位ID
    post_id: Optional[int] = None


__all__ = ["SysUserPost"]
