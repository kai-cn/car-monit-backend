"""岗位 service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysPostService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysPostServiceImpl.java

``ISysPostService`` 共 11 个方法，本模块**全部迁移**（``sys_user`` 切片先迁了 3 条只读的，
``sys_post`` 切片补齐 CRUD 与唯一性校验）。

绝大多数方法是一行转发，真正有逻辑的只有两处：

``checkPostNameUnique`` / ``checkPostCodeUnique``
    返回的是**字符串** ``"0"`` / ``"1"``，不是 bool。``"-1L"`` 那一步是把"新增"
    统一成"和自己比"，于是"名字没被占用"和"名字就是我自己"走同一条分支::

        Long postId = StringUtils.isNull(post.getPostId()) ? -1L : post.getPostId();
        SysPost info = postMapper.checkPostNameUnique(post.getPostName());
        if (StringUtils.isNotNull(info) && info.getPostId().longValue() != postId.longValue())
        {
            return UserConstants.NOT_UNIQUE_OLD;
        }
        return UserConstants.UNIQUE_OLD;

``deletePostByIds``
    先逐个查"这个岗位是否还挂着人"，挂了就抛 ``CustomException("xx已分配,不能删除")``，
    **整批都不删**。注意异常里用的是 ``post.getPostName()``，若 ``postId`` 不存在，
    Java 会在 ``post.getPostName()`` 处 NPE（同样是 500），这里也让它抛 ``AttributeError``。

``countUserPostById`` 在 Java 里走的是 ``SysUserPostMapper``（另一张表），
所以这个 service 有两个 mapper 依赖。
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from app.common.constant import user_constants as UserConstants
from app.common.exception.exceptions import CustomException
from app.system.domain.sys_post import SysPost
from app.system.mapper.sys_post_mapper import SysPostMapper
from app.system.mapper.sys_user_post_mapper import SysUserPostMapper


class SysPostService:
    """Java: ``ISysPostService`` (impl: ``SysPostServiceImpl``)."""

    def __init__(
        self,
        mapper: Optional[SysPostMapper] = None,
        user_post_mapper: Optional[SysUserPostMapper] = None,
    ) -> None:
        self._mapper = mapper or SysPostMapper()
        self._user_post_mapper = user_post_mapper or SysUserPostMapper()

    @property
    def mapper(self) -> SysPostMapper:
        return self._mapper

    @property
    def user_post_mapper(self) -> SysUserPostMapper:
        return self._user_post_mapper

    # Java: List<SysPost> selectPostList(SysPost post)
    def select_post_list(self, post: SysPost) -> List[SysPost]:
        """查询岗位信息集合。分页由调用方的 ``startPage()`` + mapper 的 ``take_page`` 完成。"""
        return self._mapper.select_post_list(post)

    # Java: List<SysPost> selectPostAll()
    def select_post_all(self) -> List[SysPost]:
        return self._mapper.select_post_all()

    # Java: SysPost selectPostById(Long postId)
    def select_post_by_id(self, post_id: int) -> Optional[SysPost]:
        return self._mapper.select_post_by_id(post_id)

    # Java: List<Integer> selectPostListByUserId(Long userId)
    def select_post_list_by_user_id(self, user_id: int) -> List[int]:
        return self._mapper.select_post_list_by_user_id(user_id)

    # Java: List<SysPost> selectPostsByUserName(String userName)
    def select_posts_by_user_name(self, user_name: str) -> List[SysPost]:
        return self._mapper.select_posts_by_user_name(user_name)

    # Java: String checkPostNameUnique(SysPost post)
    def check_post_name_unique(self, post: SysPost) -> str:
        """``"1"`` = 已存在，``"0"`` = 可用（``UserConstants.NOT_UNIQUE_OLD`` / ``UNIQUE_OLD``）。"""
        post_id = -1 if post.post_id is None else post.post_id
        info = self._mapper.check_post_name_unique(post.post_name)
        if info is not None and info.post_id != post_id:
            return UserConstants.NOT_UNIQUE_OLD
        return UserConstants.UNIQUE_OLD

    # Java: String checkPostCodeUnique(SysPost post)
    def check_post_code_unique(self, post: SysPost) -> str:
        post_id = -1 if post.post_id is None else post.post_id
        info = self._mapper.check_post_code_unique(post.post_code)
        if info is not None and info.post_id != post_id:
            return UserConstants.NOT_UNIQUE_OLD
        return UserConstants.UNIQUE_OLD

    # Java: int countUserPostById(Long postId)
    def count_user_post_by_id(self, post_id: int) -> int:
        return self._user_post_mapper.count_user_post_by_id(post_id)

    # Java: int deletePostById(Long postId)
    def delete_post_by_id(self, post_id: int) -> int:
        return self._mapper.delete_post_by_id(post_id)

    # Java: int deletePostByIds(Long[] postIds)
    def delete_post_by_ids(self, post_ids: Sequence[int]) -> int:
        """逐个校验"是否已分配给用户"，任一个已分配就整批拒绝。

        Java 先 ``selectPostById`` 再 ``countUserPostById``，顺序不能换：
        岗位不存在时它会在 ``post.getPostName()`` 处 NPE，而 NPE 与
        ``CustomException`` 的文案完全不同（前者是 JVM 的 NPE 描述）。
        """
        for post_id in post_ids:
            post = self.select_post_by_id(post_id)
            if self.count_user_post_by_id(post_id) > 0:
                # Java: throw new CustomException(String.format("%1$s已分配,不能删除", post.getPostName()))
                raise CustomException(f"{post.post_name}已分配,不能删除")
        return self._mapper.delete_post_by_ids(post_ids)

    # Java: int insertPost(SysPost post)
    def insert_post(self, post: SysPost) -> int:
        return self._mapper.insert_post(post)

    # Java: int updatePost(SysPost post)
    def update_post(self, post: SysPost) -> int:
        return self._mapper.update_post(post)


_SERVICE: Optional[SysPostService] = None


def get_post_service() -> SysPostService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysPostService()
    return _SERVICE


def reset_post_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["SysPostService", "get_post_service", "reset_post_service"]
