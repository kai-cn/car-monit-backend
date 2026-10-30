"""角色和菜单关联 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysRoleMenuMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysRoleMenuMapper.xml

四条语句全在这里（本文件只有这四条），调用方是 ``SysRoleServiceImpl``：``insertRole`` /
``updateRole`` 写关联，``deleteRoleById`` / ``deleteRoleByIds`` 删关联。
``checkMenuExistRole`` 由 ``sys_menu`` 模块的删除校验使用，一起来自同一份 XML。

``batchRoleMenu`` 与 ``<foreach>``
---------------------------------
MyBatis 展开成 ``insert into sys_role_menu(role_id, menu_id) values (?,?),(?,?)...``。
Python 侧逐行展开命名参数（``executemany`` 会保留循环顺序），与
:meth:`app.system.mapper.sys_user_role_mapper.SysUserRoleMapper.batch_user_role` 同一写法。

空列表时 Java 会拼出 ``values`` 后面什么都没有 -> MySQL 语法错；调用方
``SysRoleServiceImpl.insertRoleMenu`` 已经判过 ``list.size() > 0``，这里同样返回 0
而**不**发语句。
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from sqlalchemy import text

from app.config.database import session_scope
from app.system.domain.sys_role_menu import SysRoleMenu

_CHECK_MENU_EXIST_ROLE = """
	    select count(1) from sys_role_menu where menu_id = :menu_id
"""

_DELETE_ROLE_MENU_BY_ROLE_ID = """
		delete from sys_role_menu where role_id=:role_id
"""


def _in_clause(column: str, values: Sequence[int], prefix: str) -> tuple[str, Dict[str, int]]:
    """``<foreach open="(" separator="," close=")">`` -> ``(:p0, :p1, ...)``."""
    placeholders = ", ".join(f":{prefix}{index}" for index in range(len(values)))
    params = {f"{prefix}{index}": value for index, value in enumerate(values)}
    return f"{column} in ({placeholders})", params


class SysRoleMenuMapper:
    """Java: ``interface SysRoleMenuMapper``."""

    # Java: int checkMenuExistRole(Long menuId)
    def check_menu_exist_role(self, menu_id: int) -> int:
        with session_scope() as session:
            return int(session.execute(text(_CHECK_MENU_EXIST_ROLE), {"menu_id": menu_id}).scalar() or 0)

    # Java: int deleteRoleMenuByRoleId(Long roleId)
    def delete_role_menu_by_role_id(self, role_id: int) -> int:
        with session_scope() as session:
            result = session.execute(text(_DELETE_ROLE_MENU_BY_ROLE_ID), {"role_id": role_id})
            return result.rowcount or 0

    # Java: int deleteRoleMenu(Long[] roleIds)
    def delete_role_menu(self, role_ids: Sequence[int]) -> int:
        """批量删除。空数组会生成 ``in ()`` 并让 MySQL 报语法错 —— Java 侧一样，
        这里不额外保护（``deleteRoleByIds`` 的调用方保证至少一个 id）。"""
        clause, params = _in_clause("role_id", role_ids, "p")
        with session_scope() as session:
            result = session.execute(text(f"delete from sys_role_menu where {clause}"), params)
            return result.rowcount or 0

    # Java: int batchRoleMenu(List<SysRoleMenu> roleMenuList)
    def batch_role_menu(self, role_menu_list: List[SysRoleMenu]) -> int:
        if not role_menu_list:
            # Java: <foreach> 为空 -> ``values`` 后无内容 -> SQL 语法错。
            # 调用方 SysRoleServiceImpl.insertRoleMenu 已判 size() > 0。
            return 0
        rows = [{"role_id": item.role_id, "menu_id": item.menu_id} for item in role_menu_list]
        with session_scope() as session:
            result = session.execute(
                text("insert into sys_role_menu(role_id, menu_id) values (:role_id, :menu_id)"),
                rows,
            )
            return result.rowcount or 0


__all__ = ["SysRoleMenuMapper"]
