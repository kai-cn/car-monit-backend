"""``SysUpgradeInfoService`` -- 审计列、租户盖章与三类返回值.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUpgradeInfoServiceImpl.java

被钉住的五个点
--------------
1. ``saveSysUpgradeInfo`` 的判据是 ``isNotEmpty(id)`` —— ``None`` / ``""`` / ``"   "``
   都走**新增**分支并生成新 UUID。
2. 新增时补 ``id`` / ``delFlag='0'`` / ``epsId`` / **``tenantId``** / 四个审计列。
   ``tenantId`` 是本模块**独有**的（``SysIndexMenu`` 只盖 ``epsId``）—— 漏了会让
   新升级公告对同租户的人不可见。
3. 改的时候只动 ``updateBy`` / ``updateTime``，**不**回填 ``createTime``。
4. 返回的是 ``AjaxResult.success``（**不是** ``toAjax``）—— ``count == 0`` 也是 200。
5. ``deleteSysUpgradeInfoById`` 是**孤儿方法**（控制器只调 ``ByIds``），照留给它写测试。
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
from app.system.domain.sys_upgrade_info import SysUpgradeInfo
from app.system.service.sys_upgrade_info_service import (
    SysUpgradeInfoService,
    get_upgrade_info_service,
    reset_upgrade_info_service,
)

# --------------------------------------------------------------------------- fakes


class _FakeUpgradeInfoMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.by_id_result: Optional[SysUpgradeInfo] = None
        self.list_result: List[SysUpgradeInfo] = []
        self.newest_result: Optional[SysUpgradeInfo] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_by_id_result = 1
        self.delete_by_ids_result = 1

    def select_sys_upgrade_info_by_id(self, id: Any) -> Optional[SysUpgradeInfo]:
        self.calls.append(("select_sys_upgrade_info_by_id", id))
        return self.by_id_result

    def select_sys_upgrade_info_list(self, entity: SysUpgradeInfo) -> List[SysUpgradeInfo]:
        self.calls.append(("select_sys_upgrade_info_list", entity.model_copy(deep=True)))
        return self.list_result

    def select_sys_upgrade_info_newest(self, entity: SysUpgradeInfo) -> Optional[SysUpgradeInfo]:
        self.calls.append(("select_sys_upgrade_info_newest", entity.model_copy(deep=True)))
        return self.newest_result

    def insert_sys_upgrade_info(self, entity: SysUpgradeInfo) -> int:
        self.calls.append(("insert_sys_upgrade_info", entity.model_copy(deep=True)))
        return self.insert_result

    def update_sys_upgrade_info(self, entity: SysUpgradeInfo) -> int:
        self.calls.append(("update_sys_upgrade_info", entity.model_copy(deep=True)))
        return self.update_result

    def delete_sys_upgrade_info_by_id(self, id: Any) -> int:
        self.calls.append(("delete_sys_upgrade_info_by_id", id))
        return self.delete_by_id_result

    def delete_sys_upgrade_info_by_ids(self, ids: Sequence[Any]) -> int:
        self.calls.append(("delete_sys_upgrade_info_by_ids", list(ids)))
        return self.delete_by_ids_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def _clear_context() -> Any:
    SecurityContextHolder.clear_context()
    yield
    SecurityContextHolder.clear_context()


@pytest.fixture
def mapper() -> _FakeUpgradeInfoMapper:
    return _FakeUpgradeInfoMapper()


@pytest.fixture
def service(mapper: _FakeUpgradeInfoMapper) -> SysUpgradeInfoService:
    return SysUpgradeInfoService(upgrade_info_mapper=mapper)


def authenticate(user_id: int = 2, dept_id: int = 103, tenant_id: int = 100) -> SysUser:
    user = SysUser(user_id=user_id, user_name="ry", dept_id=dept_id, tenant_id=tenant_id)
    login_user = LoginUser(user=user, permissions={"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


# --------------------------------------------------------------------------- 查询


class TestSelect:
    def test_select_by_id_delegates(self, service: SysUpgradeInfoService, mapper: Any) -> None:
        mapper.by_id_result = SysUpgradeInfo(id="u-1")

        assert service.select_sys_upgrade_info_by_id("u-1").id == "u-1"
        assert mapper.of("select_sys_upgrade_info_by_id") == [
            ("select_sys_upgrade_info_by_id", "u-1")
        ]

    def test_the_list_does_not_stamp_the_tenant(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        """盖租户的动作在**控制器**里，service 只是纯转发（与 indexmenu 相反）。"""
        authenticate(tenant_id=100)

        service.select_sys_upgrade_info_list(SysUpgradeInfo(tenant_id=999))

        assert mapper.of("select_sys_upgrade_info_list")[0][1].tenant_id == 999

    def test_the_list_returns_the_mapper_rows_verbatim(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        mapper.list_result = [SysUpgradeInfo(ver="1.2.3")]

        rows = service.select_sys_upgrade_info_list(SysUpgradeInfo())

        assert [row.ver for row in rows] == ["1.2.3"]

    def test_newest_delegates_and_may_be_none(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        assert service.select_sys_upgrade_info_newest(SysUpgradeInfo()) is None
        assert len(mapper.of("select_sys_upgrade_info_newest")) == 1

    def test_newest_returns_the_mapper_hit(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        mapper.newest_result = SysUpgradeInfo(id="u-1", ver="1.2.3")

        assert service.select_sys_upgrade_info_newest(SysUpgradeInfo()).ver == "1.2.3"


# --------------------------------------------------------------------------- saveSysUpgradeInfo


class TestSave:
    def test_an_existing_id_takes_the_update_branch(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        authenticate(user_id=2)

        response = service.save_sys_upgrade_info(SysUpgradeInfo(id="u-1", ver="1.2.4"))

        assert mapper.of("update_sys_upgrade_info") != []
        assert mapper.of("insert_sys_upgrade_info") == []
        stored = mapper.of("update_sys_upgrade_info")[0][1]
        assert stored.update_by == 2
        assert stored.update_time is not None
        # 改的时候**不动** createBy / createTime / delFlag
        assert (stored.create_by, stored.create_time, stored.del_flag) == (None, None, None)
        assert response == {"code": 200, "msg": "操作成功！", "data": "u-1"}

    @pytest.mark.parametrize("blank_id", [None, "", "   "])
    def test_a_blank_id_takes_the_insert_branch(
        self, service: SysUpgradeInfoService, mapper: Any, blank_id: Optional[str]
    ) -> None:
        """``isNotEmpty("")`` / ``isNotEmpty("   ")`` 都是假 —— 空串也算"没有 id"。"""
        authenticate()

        service.save_sys_upgrade_info(SysUpgradeInfo(id=blank_id))

        assert mapper.of("insert_sys_upgrade_info") != []
        assert mapper.of("update_sys_upgrade_info") == []

    def test_the_insert_branch_fills_the_audit_columns(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        authenticate(user_id=2, dept_id=103, tenant_id=100)

        service.save_sys_upgrade_info(SysUpgradeInfo(ver="1.2.3"))

        stored = mapper.of("insert_sys_upgrade_info")[0][1]
        assert stored.del_flag == "0"
        assert stored.eps_id == 103
        assert stored.create_by == 2
        assert stored.update_by == 2
        assert stored.create_time is not None
        assert stored.create_time == stored.update_time

    def test_the_insert_branch_stamps_the_tenant(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        """本模块独有的 ``setTenantId(SecurityUtils.getTenantId())``。"""
        authenticate(tenant_id=100)

        service.save_sys_upgrade_info(SysUpgradeInfo(tenant_id=999))

        assert mapper.of("insert_sys_upgrade_info")[0][1].tenant_id == 100

    def test_the_generated_id_is_a_32_char_uuid(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        authenticate()

        service.save_sys_upgrade_info(SysUpgradeInfo())

        stored = mapper.of("insert_sys_upgrade_info")[0][1]
        assert isinstance(stored.id, str)
        assert len(stored.id) == 32

    def test_the_new_id_is_returned_as_data(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        authenticate()

        response = service.save_sys_upgrade_info(SysUpgradeInfo())

        generated = mapper.of("insert_sys_upgrade_info")[0][1].id
        assert response == {"code": 200, "msg": "操作成功！", "data": generated}

    def test_the_success_message_uses_a_full_width_bang(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        authenticate()

        assert service.save_sys_upgrade_info(SysUpgradeInfo(id="u-1"))["msg"] == "操作成功！"

    def test_the_business_fields_are_passed_through(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        authenticate()

        service.save_sys_upgrade_info(SysUpgradeInfo(ver="1.2.3", info="修复", back_col1="1"))

        stored = mapper.of("insert_sys_upgrade_info")[0][1]
        assert (stored.ver, stored.info, stored.back_col1) == ("1.2.3", "修复", "1")


# --------------------------------------------------------------------------- delete


class TestDelete:
    def test_delete_by_ids_returns_the_row_count(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        mapper.delete_by_ids_result = 3

        assert service.delete_sys_upgrade_info_by_ids(["u-1", "u-2"]) == {
            "code": 200,
            "msg": "操作成功",
            "data": 3,
        }
        assert mapper.of("delete_sys_upgrade_info_by_ids") == [
            ("delete_sys_upgrade_info_by_ids", ["u-1", "u-2"])
        ]

    def test_a_zero_count_is_still_a_success(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        """用的是 ``AjaxResult.success`` 而不是 ``toAjax`` —— 0 也回 200。"""
        mapper.delete_by_ids_result = 0

        assert service.delete_sys_upgrade_info_by_ids(["u-1"]) == {
            "code": 200,
            "msg": "操作成功",
            "data": 0,
        }

    def test_delete_by_id_returns_the_row_count(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        """孤儿方法：控制器不调，但行为与 ``ByIds`` 一致。"""
        mapper.delete_by_id_result = 1

        assert service.delete_sys_upgrade_info_by_id("u-1") == {
            "code": 200,
            "msg": "操作成功",
            "data": 1,
        }
        assert mapper.of("delete_sys_upgrade_info_by_id") == [
            ("delete_sys_upgrade_info_by_id", "u-1")
        ]

    def test_delete_by_id_zero_is_still_a_success(
        self, service: SysUpgradeInfoService, mapper: Any
    ) -> None:
        mapper.delete_by_id_result = 0

        assert service.delete_sys_upgrade_info_by_id("u-1")["code"] == 200


# --------------------------------------------------------------------------- 单例


class TestSingleton:
    def test_get_returns_the_same_instance(self) -> None:
        reset_upgrade_info_service()
        try:
            assert get_upgrade_info_service() is get_upgrade_info_service()
        finally:
            reset_upgrade_info_service()

    def test_the_constructor_does_not_connect(self) -> None:
        """``SysUpgradeInfoService()`` 不碰数据库（惰性 datasource）。"""
        assert isinstance(SysUpgradeInfoService().upgrade_info_mapper, object)
