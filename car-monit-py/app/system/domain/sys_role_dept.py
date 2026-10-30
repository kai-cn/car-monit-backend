"""角色和部门关联 sys_role_dept（数据权限）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysRoleDept.java

纯 POJO，只为 ``SysRoleDeptMapper.batchRoleDept`` 组装 ``(role_id, dept_id)`` 行。

这张表是 ``data_scope = '2'``（自定义数据权限）的**数据来源**：
``DataScopeAspect`` 拼出的片段是
``OR d.dept_id IN ( SELECT dept_id FROM sys_role_dept WHERE role_id = ? )``。
所以 ``SysRoleServiceImpl.authDataScope`` 的"先删后插"直接决定了这个角色的数据可见范围。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SysRoleDept:
    """Java: ``SysRoleDept``."""

    #: 角色ID
    role_id: Optional[int] = None
    #: 部门ID
    dept_id: Optional[int] = None


__all__ = ["SysRoleDept"]
