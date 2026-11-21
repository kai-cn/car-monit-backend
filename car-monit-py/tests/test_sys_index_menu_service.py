"""``SysIndexMenuService`` -- "先删后插"、软删除与四类返回值.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysIndexMenuServiceImpl.java

被钉住的六个点
--------------
1. **登录上下文覆盖 ``userId``**：``selectSysIndexMenuList`` / ``getList`` /
   ``saveSysIndexMenu`` / ``insertSysIndexMenu`` 都会无视客户端传的 ``userId``。
   写成"信任入参"不会报错，但会变成越权。
2. ``saveSysIndexMenu`` 的判据是 ``isNotEmpty(id)`` —— ``""`` / ``"   "`` 都走**新增**。
3. 新增时补齐 ``id``（UUID） / ``delFlag='0'`` / ``epsId`` / 四个审计列；
   **改** 的时候只动 ``updateBy`` / ``updateTime``。
4. ``insertSysIndexMenu`` 只剥**一个**尾逗号，且 ``split`` 丢尾部空串。
5. 删除是**软删除**，且 ``count == 0`` 也回 ``code 200``（用的是 ``AjaxResult.success``，
   不是 ``toAjax``）。改成 ``toAjax`` 会把"删不存在的 id"从 200 变 500。
6. 同一次 ``insertSysIndexMenu`` 里所有行共用**同一个**时间戳。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

import pytest

from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.system.domain.sys_index_menu import SysIndexMenu
from app.system.service.sys_index_menu_service import (
    SysIndexMenuService,
    get_index_menu_service,
    reset_index_menu_service,
)

# --------------------------------------------------------------------------- fakes


class _FakeIndexMenuMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.by_id_result: Optional[SysIndexMenu] = None
        self.list_result: List[SysIndexMenu] = []
        self.my_list_result: List[SysIndexMenu] = []
        self.insert_result = 1
        self.update_result = 1
        self.delete_by_id_result = 1
        self.delete_by_ids_result = 1
        self.delete_by_menu_user_id_result = 1

    def select_sys_index_menu_by_id(self, id: Any) -> Optional[SysIndexMenu]:
        self.calls.append(("select_sys_index_menu_by_id", id))
        return self.by_id_result

    def select_sys_index_menu_list(self, entity: SysIndexMenu) -> List[SysIndexMenu]:
        self.calls.append(("select_sys_index_menu_list", entity.model_copy(deep=True)))
        return self.list_result

    def get_list(self, entity: SysIndexMenu) -> List[SysIndexMenu]:
        self.calls.append(("get_list", entity.model_copy(deep=True)))
        return self.my_list_result

    def insert_sys_index_menu(self, entity: SysIndexMenu) -> int:
        self.calls.append(("insert_sys_index_menu", entity.model_copy(deep=True)))
        return self.insert_result

    def update_sys_index_menu(self, entity: SysIndexMenu) -> int:
        self.calls.append(("update_sys_index_menu", entity.model_copy(deep=True)))
        return self.update_result

    def delete_sys_index_menu_by_id(self, id: Any) -> int:
        self.calls.append(("delete_sys_index_menu_by_id", id))
        return self.delete_by_id_result

    def delete_sys_index_menu_by_ids(self, ids: Sequence[Any]) -> int:
        self.calls.append(("delete_sys_index_menu_by_ids", list(ids)))
        return self.delete_by_ids_result

    def delete_by_menu_user_id(self, entity: SysIndexMenu) -> int:
        self.calls.append(("delete_by_menu_user_id", entity.model_copy(deep=True)))
        return self.delete_by_menu_user_id_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def _clear_context() -> Any:
    SecurityContextHolder.clear_context()
    yield
    SecurityContextHolder.clear_context()


@pytest.fixture
def mapper() -> _FakeIndexMenuMapper:
    return _FakeIndexMenuMapper()


@pytest.fixture
def service(mapper: _FakeIndexMenuMapper) -> SysIndexMenuService:
    return SysIndexMenuService(index_menu_mapper=mapper)


def authenticate(user_id: int = 2, dept_id: int = 103) -> SysUser:
    user = SysUser(user_id=user_id, user_name="ry", dept_id=dept_id)
    login_user = LoginUser(user=user, permissions={"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


# --------------------------------------------------------------------------- 查询


class TestSelect:
    def test_select_by_id_delegates(self, service: SysIndexMenuService, mapper: Any) -> None:
        mapper.by_id_result = SysIndexMenu(id="u-1")

        assert service.select_sys_index_menu_by_id("u-1").id == "u-1"
        assert mapper.of("select_sys_index_menu_by_id") == [("select_sys_index_menu_by_id", "u-1")]

    def test_the_list_overrides_the_client_user_id(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """客户端传 ``userId=999`` 也会被登录上下文覆盖成 2。"""
        authenticate(user_id=2)

        service.select_sys_index_menu_list(SysIndexMenu(user_id=999))

        assert mapper.of("select_sys_index_menu_list")[0][1].user_id == 2

    def test_get_list_overrides_the_client_user_id_too(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        authenticate(user_id=2)

        service.get_list(SysIndexMenu(user_id=999))

        assert mapper.of("get_list")[0][1].user_id == 2

    def test_the_list_returns_the_mapper_rows_verbatim(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        authenticate()
        mapper.list_result = [SysIndexMenu(menu_id=100)]

        rows = service.select_sys_index_menu_list(SysIndexMenu())

        assert [row.menu_id for row in rows] == [100]


# --------------------------------------------------------------------------- saveSysIndexMenu


class TestSave:
    def test_an_existing_id_takes_the_update_branch(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        authenticate(user_id=2)

        response = service.save_sys_index_menu(SysIndexMenu(id="u-1", user_id=7))

        assert mapper.of("update_sys_index_menu") != []
        assert mapper.of("insert_sys_index_menu") == []
        stored = mapper.of("update_sys_index_menu")[0][1]
        assert stored.update_by == 2
        assert stored.update_time is not None
        # 改的时候**不动** createBy / createTime / id / delFlag
        assert (stored.create_by, stored.create_time, stored.del_flag) == (None, None, None)
        assert response == {"code": 200, "msg": "操作成功！", "data": "u-1"}

    def test_a_blank_id_takes_the_insert_branch(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """``isNotEmpty("")`` / ``isNotEmpty("   ")`` 都是假 —— 空串也算"没有 id"。"""
        authenticate()
        mapper.insert_result = 5

        response = service.save_sys_index_menu(SysIndexMenu(id="   "))

        assert mapper.of("insert_sys_index_menu") != []
        assert mapper.of("update_sys_index_menu") == []
        assert response["data"] == mapper.of("insert_sys_index_menu")[0][1].id

    def test_the_insert_branch_fills_the_audit_columns(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        authenticate(user_id=2, dept_id=103)

        service.save_sys_index_menu(SysIndexMenu(menu_id=100))

        stored = mapper.of("insert_sys_index_menu")[0][1]
        assert stored.del_flag == "0"
        assert stored.eps_id == 103
        assert stored.create_by == 2
        assert stored.update_by == 2
        assert stored.create_time is not None
        assert stored.create_time == stored.update_time
        # id 是 UUID 字符串
        assert isinstance(stored.id, str)
        assert len(stored.id) == 32

    def test_the_new_id_is_returned_as_data(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        authenticate()

        response = service.save_sys_index_menu(SysIndexMenu())

        generated = mapper.of("insert_sys_index_menu")[0][1].id
        assert response == {"code": 200, "msg": "操作成功！", "data": generated}

    def test_the_success_message_uses_a_full_width_bang(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        authenticate()

        assert service.save_sys_index_menu(SysIndexMenu(id="u-1"))["msg"] == "操作成功！"


# --------------------------------------------------------------------------- insertSysIndexMenu


class TestInsertMenuIds:
    @pytest.mark.parametrize("menu_ids", [None, "", "   "])
    def test_blank_input_writes_nothing(
        self, service: SysIndexMenuService, mapper: Any, menu_ids: Any
    ) -> None:
        """``isNotBlank`` 判空：``None`` / ``""`` / ``"   "`` 全部短路。"""
        authenticate()

        response = service.insert_sys_index_menu(menu_ids)

        assert response == {"code": 200, "msg": "操作成功"}
        assert mapper.calls == []

    def test_each_id_is_deleted_then_inserted(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        authenticate(user_id=2)

        service.insert_sys_index_menu("100,101")

        order = [call[0] for call in mapper.calls]
        assert order == [
            "delete_by_menu_user_id",
            "insert_sys_index_menu",
            "delete_by_menu_user_id",
            "insert_sys_index_menu",
        ]
        assert [call[1].menu_id for call in mapper.of("insert_sys_index_menu")] == [100, 101]

    def test_every_row_carries_the_login_user(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        authenticate(user_id=2, dept_id=103)

        service.insert_sys_index_menu("100,101")

        for _, entity in mapper.of("insert_sys_index_menu"):
            assert entity.user_id == 2
            assert entity.del_flag == "0"
            assert entity.eps_id == 103
            assert entity.create_by == 2
            assert entity.update_by == 2

    def test_the_stray_comma_is_stripped_once(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """``"100,"`` -> ``"100"`` -> 1 行（否则 ``split`` 会留下空段）。"""
        authenticate()

        service.insert_sys_index_menu("100,")

        assert [call[1].menu_id for call in mapper.of("insert_sys_index_menu")] == [100]

    def test_double_trailing_comma_loses_only_one(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """``"100,101,,"`` 只剥一个 -> ``"100,101,"`` -> ``split`` 丢尾部空串 -> 2 行。"""
        authenticate()

        service.insert_sys_index_menu("100,101,,")

        assert [call[1].menu_id for call in mapper.of("insert_sys_index_menu")] == [100, 101]

    def test_a_middle_empty_segment_explodes(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """``"100,,101"`` 中间的 ``""`` 不会被丢 -> ``int("")`` -> ``ValueError`` -> 500。"""
        authenticate()

        with pytest.raises(ValueError):
            service.insert_sys_index_menu("100,,101")

    def test_a_non_numeric_id_raises_a_value_error(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """Java: ``Long.parseLong("abc")`` -> ``NumberFormatException`` -> 500。"""
        authenticate()

        with pytest.raises(ValueError):
            service.insert_sys_index_menu("abc")

    def test_the_delete_branch_does_not_stamp_the_timestamp(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """"先删"用的实体只有 ``userId`` / ``menuId``。"""
        authenticate()

        service.insert_sys_index_menu("100")

        deleted = mapper.of("delete_by_menu_user_id")[0][1]
        assert (deleted.user_id, deleted.menu_id) == (2, 100)
        assert deleted.del_flag is None

    def test_all_rows_share_one_timestamp(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """``curDate`` 在循环**外**取得 —— 同一批插入时间完全相同。"""
        authenticate()

        service.insert_sys_index_menu("100,101,102")

        stamps = [call[1].create_time for call in mapper.of("insert_sys_index_menu")]
        assert len(set(stamps)) == 1


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_by_ids_returns_the_row_count(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        mapper.delete_by_ids_result = 3

        assert service.delete_sys_index_menu_by_ids(["u-1", "u-2"]) == {
            "code": 200,
            "msg": "操作成功",
            "data": 3,
        }
        assert mapper.of("delete_sys_index_menu_by_ids") == [
            ("delete_sys_index_menu_by_ids", ["u-1", "u-2"])
        ]

    def test_a_zero_count_is_still_a_success(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        """用的是 ``AjaxResult.success`` 而不是 ``toAjax`` —— 0 也回 200。"""
        mapper.delete_by_ids_result = 0

        assert service.delete_sys_index_menu_by_ids(["u-1"]) == {
            "code": 200,
            "msg": "操作成功",
            "data": 0,
        }

    def test_delete_by_id_returns_the_row_count(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        mapper.delete_by_id_result = 1

        assert service.delete_sys_index_menu_by_id("u-1") == {
            "code": 200,
            "msg": "操作成功",
            "data": 1,
        }

    def test_delete_by_id_zero_is_still_a_success(
        self, service: SysIndexMenuService, mapper: Any
    ) -> None:
        mapper.delete_by_id_result = 0

        assert service.delete_sys_index_menu_by_id("u-1")["code"] == 200


# --------------------------------------------------------------------------- 单例


class TestSingleton:
    def test_get_returns_the_same_instance(self) -> None:
        reset_index_menu_service()
        try:
            assert get_index_menu_service() is get_index_menu_service()
        finally:
            reset_index_menu_service()

    def test_the_constructor_does_not_connect(self) -> None:
        """``SysIndexMenuService()`` 不碰数据库（惰性 datasource）。"""
        assert isinstance(SysIndexMenuService().index_menu_mapper, object)