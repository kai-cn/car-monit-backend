"""角色和部门关联 mapper（数据权限）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysRoleDeptMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysRoleDeptMapper.xml

四条语句全在这里，调用方是 ``SysRoleServiceImpl.authDataScope``（先删后插）与
``deleteRoleById`` / ``deleteRoleByIds``（顺带删）。
``selectCountRoleDeptByDeptId`` 由 ``sys_dept`` 的删除校验使用（"部门已分配角色"），
一起来自同一份 XML。

用法提示
--------
``sys_role_dept`` **只**在 ``sys_role.data_scope = '2'``（自定义数据权限）时有意义；
其它三种范围（全部 / 本部门 / 本部门及以下）由 ``DataScopeAspect`` 直接按 ``dept_id``
拼 SQL，不读这张表。因此 ``authDataScope`` 无条件清空再插入，即使本次范围不是 ``2``。
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from sqlalchemy import text

from app.config.database import session_scope
from app.system.domain.sys_role_dept import SysRoleDept

_SELECT_COUNT_ROLE_DEPT_BY_DEPT_ID = """
	    select count(1) from sys_role_dept where dept_id=:dept_id
"""

_DELETE_ROLE_DEPT_BY_ROLE_ID = """
		delete from sys_role_dept where role_id=:role_id
"""


def _in_clause(column: str, values: Sequence[int], prefix: str) -> tuple[str, Dict[str, int]]:
    """``<foreach open="(" separator="," close=")">`` -> ``(:p0, :p1, ...)``."""
    placeholders = ", ".join(f":{prefix}{index}" for index in range(len(values)))
    params = {f"{prefix}{index}": value for index, value in enumerate(values)}
    return f"{column} in ({placeholders})", params


class SysRoleDeptMapper:
    """Java: ``interface SysRoleDeptMapper``."""

    # Java: int selectCountRoleDeptByDeptId(Long deptId)
    def select_count_role_dept_by_dept_id(self, dept_id: int) -> int:
        with session_scope() as session:
            return int(
                session.execute(text(_SELECT_COUNT_ROLE_DEPT_BY_DEPT_ID), {"dept_id": dept_id}).scalar() or 0
            )

    # Java: int deleteRoleDeptByRoleId(Long roleId)
    def delete_role_dept_by_role_id(self, role_id: int) -> int:
        with session_scope() as session:
            result = session.execute(text(_DELETE_ROLE_DEPT_BY_ROLE_ID), {"role_id": role_id})
            return result.rowcount or 0

    # Java: int deleteRoleDept(Long[] roleIds)
    def delete_role_dept(self, role_ids: Sequence[int]) -> int:
        clause, params = _in_clause("role_id", role_ids, "p")
        with session_scope() as session:
            result = session.execute(text(f"delete from sys_role_dept where {clause}"), params)
            return result.rowcount or 0

    # Java: int batchRoleDept(List<SysRoleDept> roleDeptList)
    def batch_role_dept(self, role_dept_list: List[SysRoleDept]) -> int:
        if not role_dept_list:
            # 同 batchRoleMenu：空列表在 Java 里是 SQL 语法错，调用方已判 size() > 0。
            return 0
        rows = [{"role_id": item.role_id, "dept_id": item.dept_id} for item in role_dept_list]
        with session_scope() as session:
            result = session.execute(
                text("insert into sys_role_dept(role_id, dept_id) values (:role_id, :dept_id)"),
                rows,
            )
            return result.rowcount or 0


__all__ = ["SysRoleDeptMapper"]
