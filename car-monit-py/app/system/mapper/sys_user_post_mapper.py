"""用户与岗位关联 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUserPostMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysUserPostMapper.xml

与 :mod:`app.system.mapper.sys_user_role_mapper` 完全同构：删除（单个 / 批量）、
批量新增、按岗位统计。``sys_user`` 的新增/修改/删除都要同步这张表。
"""

from __future__ import annotations

from typing import List, Sequence

from sqlalchemy import text

from app.config.database import session_scope
from app.system.domain.sys_user_post import SysUserPost
from app.system.mapper.sys_user_role_mapper import _in_clause

_DELETE_USER_POST_BY_USER_ID = """
		delete from sys_user_post where user_id=:user_id
"""

_COUNT_USER_POST_BY_ID = """
	    select count(1) from sys_user_post where post_id=:post_id  
"""


class SysUserPostMapper:
    """Java: ``interface SysUserPostMapper``."""

    # Java: int deleteUserPostByUserId(Long userId)
    def delete_user_post_by_user_id(self, user_id: int) -> int:
        with session_scope() as session:
            result = session.execute(text(_DELETE_USER_POST_BY_USER_ID), {"user_id": user_id})
            return result.rowcount or 0

    # Java: int deleteUserPost(Long[] userIds)
    def delete_user_post(self, user_ids: Sequence[int]) -> int:
        clause, params = _in_clause("user_id", user_ids, "p")
        with session_scope() as session:
            result = session.execute(text(f"delete from sys_user_post where {clause}"), params)
            return result.rowcount or 0

    # Java: int batchUserPost(List<SysUserPost> userPostList)
    def batch_user_post(self, user_post_list: List[SysUserPost]) -> int:
        if not user_post_list:
            return 0
        rows = [{"user_id": item.user_id, "post_id": item.post_id} for item in user_post_list]
        with session_scope() as session:
            result = session.execute(
                text("insert into sys_user_post(user_id, post_id) values (:user_id, :post_id)"),
                rows,
            )
            return result.rowcount or 0

    # Java: int countUserPostById(Long postId)
    def count_user_post_by_id(self, post_id: int) -> int:
        with session_scope() as session:
            return int(session.execute(text(_COUNT_USER_POST_BY_ID), {"post_id": post_id}).scalar() or 0)


__all__ = ["SysUserPostMapper"]
