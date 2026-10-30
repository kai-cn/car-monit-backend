"""用户和角色关联 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUserRoleMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysUserRoleMapper.xml

``sys_user`` 的新增/修改/删除都要同步这张关联表，因此这里迁移其中 4 条语句：
``deleteUserRoleByUserId`` / ``deleteUserRole``（批量）/ ``batchUserRole`` /
``countUserRoleByRoleId``。``getUserRoleMap``、``deleteUserRoleInfo`` 等属于角色
模块，随该模块迁移。

``batchUserRole`` 与 ``<foreach>``
---------------------------------
MyBatis 的 ``<foreach>`` 会拼出 ``values (?,?),(?,?)...``。Python 里必须**逐行
展开成占位符**，不能把 id 直接格式化进 SQL —— 这正是 ``text()`` + ``executemany``
或动态 ``:p0_0, :p0_1`` 的用途。下面的实现按行展开命名参数，行数不设上限，
与 MyBatis 一致（MyBatis 也不分批）。
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from sqlalchemy import text

from app.config.database import session_scope
from app.system.domain.sys_user_role import SysUserRole

_DELETE_USER_ROLE_BY_USER_ID = """
		delete from sys_user_role where user_id=:user_id
"""

_COUNT_USER_ROLE_BY_ROLE_ID = """
	    select count(1) from sys_user_role where role_id=:role_id  
"""

_COUNT_USER_ROLE_BY_ROLE_ID_USER_ID = """
	    select count(1) from sys_user_role where role_id=:role_id and user_id = :user_id
"""


def _in_clause(column: str, values: Sequence[int], prefix: str) -> tuple[str, Dict[str, int]]:
    """``<foreach ... open="(" separator="," close=")">`` -> ``(:p0, :p1, ...)``."""
    placeholders = ", ".join(f":{prefix}{index}" for index in range(len(values)))
    params = {f"{prefix}{index}": value for index, value in enumerate(values)}
    return f"{column} in ({placeholders})", params


class SysUserRoleMapper:
    """Java: ``interface SysUserRoleMapper`` (the ``sys_user`` slice)."""

    # Java: int deleteUserRoleByUserId(Long userId)
    def delete_user_role_by_user_id(self, user_id: int) -> int:
        with session_scope() as session:
            result = session.execute(text(_DELETE_USER_ROLE_BY_USER_ID), {"user_id": user_id})
            return result.rowcount or 0

    # Java: int deleteUserRole(Long[] userIds)
    def delete_user_role(self, user_ids: Sequence[int]) -> int:
        """批量删除。``<foreach collection="array">`` 在空数组时会生成 ``in ()``
        并让 MySQL 报语法错——Java 侧同样如此，这里保留该行为。"""
        clause, params = _in_clause("user_id", user_ids, "p")
        with session_scope() as session:
            result = session.execute(text(f"delete from sys_user_role where {clause}"), params)
            return result.rowcount or 0

    # Java: int batchUserRole(List<SysUserRole> userRoleList)
    def batch_user_role(self, user_role_list: List[SysUserRole]) -> int:
        if not user_role_list:
            # Java: <foreach> 为空时会拼出 ``values`` 后无内容 -> SQL 语法错。
            # 调用方 SysUserServiceImpl.insertUserRole 已经判过 size() > 0。
            return 0
        rows = [{"user_id": item.user_id, "role_id": item.role_id} for item in user_role_list]
        with session_scope() as session:
            result = session.execute(
                text("insert into sys_user_role(user_id, role_id) values (:user_id, :role_id)"),
                rows,
            )
            return result.rowcount or 0

    # Java: int countUserRoleByRoleId(Long roleId)
    def count_user_role_by_role_id(self, role_id: int) -> int:
        with session_scope() as session:
            return int(session.execute(text(_COUNT_USER_ROLE_BY_ROLE_ID), {"role_id": role_id}).scalar() or 0)

    # Java: int countUserRoleByRoleIdUserId(Long roleId, Long userId)
    def count_user_role_by_role_id_user_id(self, role_id: int, user_id: int) -> int:
        """角色管理切片补的语句：判断"某用户是否拥有某角色"。"""
        with session_scope() as session:
            result = session.execute(
                text(_COUNT_USER_ROLE_BY_ROLE_ID_USER_ID), {"role_id": role_id, "user_id": user_id}
            )
            return int(result.scalar() or 0)


__all__ = ["SysUserRoleMapper"]
