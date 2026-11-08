"""``SysPostService`` -- ``SysPostServiceImpl`` 的等价实现.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/.../service/impl/SysPostServiceImpl.java

这一层测什么
------------
SQL 已经由 ``test_sys_post_mapper.py`` 钉住了，所以这里全部用假 Mapper，
只测**分支判断**和**调用顺序**。三处最容易被"顺手优化"掉的地方：

* ``checkPostNameUnique`` / ``checkPostCodeUnique`` 返回的是字符串 ``"0"``/``"1"``，
  不是 ``bool``。把 ``postId == null`` 折成 ``-1L`` 之后，"没有同名行"和
  "同名的就是我这一行"走的是同一个分支 —— 不能改成"先判 ``info != null`` 再判 id"。
* ``deletePostByIds`` 是**先查岗位、再查占用**，而且只要有一个岗位已分配，
  **整批都不删**（异常直接抛出，后面的 id 连查都不查）。
* ``countUserPostById`` 走 ``SysUserPostMapper``（另一张表 ``sys_user_post``），
  不是 ``SysPostMapper`` —— 注入错了会在单岗位删除时静默变成 0。
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import pytest

from app.common.constant.user_constants import NOT_UNIQUE_OLD, UNIQUE_OLD
from app.common.exception.exceptions import CustomException
from app.system.domain.sys_post import SysPost
from app.system.service.sys_post_service import SysPostService, reset_post_service

# --------------------------------------------------------------------------- fakes


class _FakePostMapper:
    """``SysPostMapper`` 的代言人：记录调用、返回预置结果。"""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.post_list_result: List[SysPost] = []
        self.post_list_arg: Optional[SysPost] = None
        self.post_all_result: List[SysPost] = []
        self.post_by_id: Optional[SysPost] = None
        self.post_ids_by_user_id: List[int] = []
        self.posts_by_user_name: List[SysPost] = []
        self.name_unique_info: Optional[SysPost] = None
        self.code_unique_info: Optional[SysPost] = None
        self.delete_by_id_result = 1
        self.delete_by_ids_result = 2
        self.deleted_by_ids: Optional[Sequence[int]] = None
        self.insert_result = 1
        self.inserted: Optional[SysPost] = None
        self.update_result = 1
        self.updated: Optional[SysPost] = None
        self.lastrowid = 42

    # -- selects
    def select_post_list(self, post: SysPost) -> List[SysPost]:
        self.calls.append(("select_post_list", post))
        self.post_list_arg = post
        return list(self.post_list_result)

    def select_post_all(self) -> List[SysPost]:
        self.calls.append(("select_post_all",))
        return list(self.post_all_result)

    def select_post_by_id(self, post_id: int) -> Optional[SysPost]:
        self.calls.append(("select_post_by_id", post_id))
        return self.post_by_id

    def select_post_list_by_user_id(self, user_id: int) -> List[int]:
        self.calls.append(("select_post_list_by_user_id", user_id))
        return list(self.post_ids_by_user_id)

    def select_posts_by_user_name(self, user_name: str) -> List[SysPost]:
        self.calls.append(("select_posts_by_user_name", user_name))
        return list(self.posts_by_user_name)

    # -- 唯一性
    def check_post_name_unique(self, post_name: str) -> Optional[SysPost]:
        self.calls.append(("check_post_name_unique", post_name))
        return self.name_unique_info

    def check_post_code_unique(self, post_code: str) -> Optional[SysPost]:
        self.calls.append(("check_post_code_unique", post_code))
        return self.code_unique_info

    # -- writes
    def delete_post_by_id(self, post_id: int) -> int:
        self.calls.append(("delete_post_by_id", post_id))
        return self.delete_by_id_result

    def delete_post_by_ids(self, post_ids: Sequence[int]) -> int:
        self.calls.append(("delete_post_by_ids", list(post_ids)))
        self.deleted_by_ids = post_ids
        return self.delete_by_ids_result

    def insert_post(self, post: SysPost) -> int:
        self.calls.append(("insert_post", post))
        self.inserted = post
        post.post_id = self.lastrowid
        return self.insert_result

    def update_post(self, post: SysPost) -> int:
        self.calls.append(("update_post", post))
        self.updated = post
        return self.update_result


class _FakeUserPostMapper:
    """``SysUserPostMapper``：本切片只会用到 ``countUserPostById``。"""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.count_by_post_id: dict = {}
        self.default_count = 0

    def count_user_post_by_id(self, post_id: int) -> int:
        self.calls.append(("count_user_post_by_id", post_id))
        return self.count_by_post_id.get(post_id, self.default_count)


def _service() -> tuple:
    mapper = _FakePostMapper()
    user_post_mapper = _FakeUserPostMapper()
    return SysPostService(mapper, user_post_mapper), mapper, user_post_mapper


# --------------------------------------------------------------------------- 转发


class TestDelegation:
    """11 个方法里有 8 个是一行转发；这里确认它真的转发到了**指定的**那个 mapper。"""

    def test_select_post_list_passes_the_entity_through(self) -> None:
        service, mapper, _ = _service()
        mapper.post_list_result = [SysPost(post_id=1, post_name="董事长")]

        rows = service.select_post_list(SysPost(status="0"))

        assert [post.post_id for post in rows] == [1]
        assert mapper.post_list_arg.status == "0"

    def test_select_post_all(self) -> None:
        service, mapper, _ = _service()
        mapper.post_all_result = [SysPost(post_id=1), SysPost(post_id=2)]

        assert [post.post_id for post in service.select_post_all()] == [1, 2]
        assert mapper.calls == [("select_post_all",)]

    def test_select_post_by_id(self) -> None:
        service, mapper, _ = _service()
        mapper.post_by_id = SysPost(post_id=7, post_name="项目经理")

        post = service.select_post_by_id(7)

        assert post is not None and post.post_name == "项目经理"
        assert mapper.calls == [("select_post_by_id", 7)]

    def test_select_post_list_by_user_id_returns_ids_not_entities(self) -> None:
        service, mapper, _ = _service()
        mapper.post_ids_by_user_id = [3, 4]

        assert service.select_post_list_by_user_id(9) == [3, 4]
        assert mapper.calls == [("select_post_list_by_user_id", 9)]

    def test_select_posts_by_user_name(self) -> None:
        service, mapper, _ = _service()
        mapper.posts_by_user_name = [SysPost(post_name="人事")]

        posts = service.select_posts_by_user_name("ry")

        assert [post.post_name for post in posts] == ["人事"]
        assert mapper.calls == [("select_posts_by_user_name", "ry")]

    def test_insert_post_returns_the_rowcount_and_backfills_the_id(self) -> None:
        service, mapper, _ = _service()
        post = SysPost(post_name="新岗位")

        affected = service.insert_post(post)

        assert affected == 1
        # Java: useGeneratedKeys="true" keyProperty="postId"
        assert post.post_id == 42
        assert mapper.inserted is post

    def test_update_post(self) -> None:
        service, _, _ = _service()
        post = SysPost(post_id=5, post_name="改名")

        assert service.update_post(post) == 1

    def test_single_delete_does_not_check_assignments(self) -> None:
        """``deletePostById`` 是直接删，**没有**"已分配"校验（校验在批量版本里）。"""
        service, mapper, user_post_mapper = _service()
        mapper.delete_by_id_result = 3

        assert service.delete_post_by_id(6) == 3
        assert user_post_mapper.calls == []


# --------------------------------------------------------------------------- 唯一性


class TestCheckPostNameUnique:
    """返回值是 ``"1"``（已存在）/ ``"0"``（可用），不是 bool。"""

    def test_no_row_means_unique(self) -> None:
        service, _, _ = _service()

        assert service.check_post_name_unique(SysPost(post_name="董事长")) == UNIQUE_OLD
        assert UNIQUE_OLD == "0"

    def test_no_row_means_unique_for_an_existing_entity_too(self) -> None:
        service, _, _ = _service()

        assert service.check_post_name_unique(SysPost(post_id=8, post_name="董事长")) == "0"

    def test_a_different_row_holding_the_name_is_not_unique(self) -> None:
        service, mapper, _ = _service()
        mapper.name_unique_info = SysPost(post_id=8, post_name="董事长")

        assert service.check_post_name_unique(SysPost(post_name="董事长")) == NOT_UNIQUE_OLD
        assert NOT_UNIQUE_OLD == "1"

    def test_my_own_row_is_unique(self) -> None:
        """编辑时不改名字，查回来的就是自己 -> 不算占用。"""
        service, mapper, _ = _service()
        mapper.name_unique_info = SysPost(post_id=8, post_name="董事长")

        assert service.check_post_name_unique(SysPost(post_id=8, post_name="董事长")) == "0"

    def test_the_null_id_sentinel_is_minus_one(self) -> None:
        """``postId == null`` 折成 ``-1L``；只要查回来的行不是 -1 就算占用。

        用 ``-1`` 而不是 ``0`` 是因为 MySQL 自增从 1 开始，
        而 ``0`` 在部分 ORM 里会被当成"未设置"。
        """
        service, mapper, _ = _service()
        # -1 是哨兵本身，等于"没有别人"
        mapper.name_unique_info = SysPost(post_id=-1, post_name="董事长")
        assert service.check_post_name_unique(SysPost(post_name="董事长")) == "0"

        # 换成任何别的 id 就要判成占用
        mapper.name_unique_info = SysPost(post_id=0, post_name="董事长")
        assert service.check_post_name_unique(SysPost(post_name="董事长")) == "1"

    def test_the_name_is_what_gets_looked_up(self) -> None:
        service, mapper, _ = _service()

        service.check_post_name_unique(SysPost(post_id=8, post_name="董事长", post_code="ceo"))

        assert mapper.calls == [("check_post_name_unique", "董事长")]


class TestCheckPostCodeUnique:
    """与 name 版同构，只是查 ``post_code``。"""

    def test_no_row_means_unique(self) -> None:
        service, _, _ = _service()

        assert service.check_post_code_unique(SysPost(post_code="ceo")) == "0"

    def test_a_different_row_holding_the_code_is_not_unique(self) -> None:
        service, mapper, _ = _service()
        mapper.code_unique_info = SysPost(post_id=8, post_code="ceo")

        assert service.check_post_code_unique(SysPost(post_code="ceo")) == "1"

    def test_my_own_row_is_unique(self) -> None:
        service, mapper, _ = _service()
        mapper.code_unique_info = SysPost(post_id=8, post_code="ceo")

        assert service.check_post_code_unique(SysPost(post_id=8, post_code="ceo")) == "0"

    def test_the_null_id_sentinel_is_minus_one(self) -> None:
        service, mapper, _ = _service()
        mapper.code_unique_info = SysPost(post_id=-1, post_code="ceo")

        assert service.check_post_code_unique(SysPost(post_code="ceo")) == "0"


# --------------------------------------------------------------------------- 删除


class TestDeletePostByIds:
    """``deletePostByIds`` 是唯一带业务校验的写方法。"""

    def test_unassigned_posts_are_deleted_in_one_statement(self) -> None:
        service, mapper, user_post_mapper = _service()
        mapper.post_by_id = SysPost(post_id=5, post_name="项目经理")
        mapper.delete_by_ids_result = 2

        affected = service.delete_post_by_ids([5, 6])

        assert affected == 2
        # 整批一条 delete，不是循环单删。
        assert mapper.deleted_by_ids == [5, 6]
        assert [call[0] for call in mapper.calls].count("delete_post_by_ids") == 1
        # 每个 id 都要查一次占用。
        assert [call[1] for call in user_post_mapper.calls] == [5, 6]

    def test_an_assigned_post_aborts_the_whole_batch(self) -> None:
        service, mapper, user_post_mapper = _service()
        mapper.post_by_id = SysPost(post_id=5, post_name="项目经理")
        user_post_mapper.count_by_post_id = {5: 2}

        with pytest.raises(CustomException) as error:
            service.delete_post_by_ids([5, 6])

        # Java: throw new CustomException(String.format("%1$s已分配,不能删除", post.getPostName()))
        assert "项目经理已分配,不能删除" in str(error.value)
        # 一个都没删。
        assert mapper.deleted_by_ids is None
        assert "delete_post_by_ids" not in [call[0] for call in mapper.calls]

    def test_the_loop_stops_at_the_first_assigned_post(self) -> None:
        """第一个就命中 -> 后面的 id 连 ``selectPostById`` 都不做。"""
        service, mapper, user_post_mapper = _service()
        mapper.post_by_id = SysPost(post_id=5, post_name="项目经理")
        user_post_mapper.count_by_post_id = {5: 1}

        with pytest.raises(CustomException):
            service.delete_post_by_ids([5, 6, 7])

        assert [call[1] for call in user_post_mapper.calls] == [5]
        assert [call for call in mapper.calls if call[0] == "select_post_by_id"] == [
            ("select_post_by_id", 5)
        ]

    def test_select_comes_before_count(self) -> None:
        """顺序不能换：``post.getPostName()`` 依赖前一条查询。"""
        order: List[str] = []

        class _OrderedPostMapper(_FakePostMapper):
            def select_post_by_id(self, post_id: int) -> Optional[SysPost]:
                order.append("select")
                return super().select_post_by_id(post_id)

        class _OrderedUserPostMapper(_FakeUserPostMapper):
            def count_user_post_by_id(self, post_id: int) -> int:
                order.append("count")
                return super().count_user_post_by_id(post_id)

        service = SysPostService(_OrderedPostMapper(), _OrderedUserPostMapper())

        service.delete_post_by_ids([5])

        assert order == ["select", "count"]

    def test_a_missing_post_with_users_raises_attribute_error(self) -> None:
        """岗位不存在却仍查到占用时，Java 在 ``post.getPostName()`` 处 NPE。

        这里让 ``None.post_name`` 抛 ``AttributeError`` —— 同样是 500，
        与"已分配,不能删除"的文案区分开。
        """
        service, mapper, user_post_mapper = _service()
        mapper.post_by_id = None
        user_post_mapper.count_by_post_id = {5: 1}

        with pytest.raises(AttributeError):
            service.delete_post_by_ids([5])

    def test_a_missing_post_without_users_is_still_deleted(self) -> None:
        """不存在的 id 也照样进 delete（Java 同样不判空），只是影响 0 行。"""
        service, mapper, _ = _service()
        mapper.post_by_id = None
        mapper.delete_by_ids_result = 0

        assert service.delete_post_by_ids([999]) == 0
        assert mapper.deleted_by_ids == [999]

    def test_an_empty_batch_skips_the_checks_and_delegates(self) -> None:
        """空数组不进入校验循环，但**仍然**转发给 mapper（Java 也不判空）。"""
        service, mapper, user_post_mapper = _service()
        mapper.delete_by_ids_result = 0

        assert service.delete_post_by_ids([]) == 0
        assert user_post_mapper.calls == []
        assert mapper.deleted_by_ids == []


# --------------------------------------------------------------------------- 装配


class TestServiceSingleton:
    """与 Spring 的默认单例作用域对齐（``get_post_service``）。"""

    def test_the_two_mappers_are_wired_by_default(self) -> None:
        service = SysPostService()

        assert service.mapper is not None
        assert service.user_post_mapper is not None
        # 两个依赖是**不同**的 mapper，别把 sys_user_post 的查询挂到 sys_post 上。
        assert service.mapper is not service.user_post_mapper

    def test_the_cached_service_can_be_dropped(self) -> None:
        from app.system.service import sys_post_service as module

        first = module.get_post_service()
        assert module.get_post_service() is first

        reset_post_service()

        assert module.get_post_service() is not first
        reset_post_service()
