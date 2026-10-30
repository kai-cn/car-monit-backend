"""``SysUserService`` -- ``SysUserServiceImpl`` 的等价实现.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/.../service/impl/SysUserServiceImpl.java

这一层测什么
------------
Mapper 的 SQL 已经由 ``test_sys_user_mapper.py`` 钉住了，所以这里全部用假 Mapper，
只测**调用顺序**和**分支判断**。三处最容易被"顺手优化"掉的地方：

* ``updateUser`` 的顺序是"删角色 -> 加角色 -> 删岗位 -> 加岗位 -> 更新主表"，
  换一下就会在某个环节读到已删/未建的行；
* ``updateUserStatus`` / ``resetPwd`` / ``updateUserProfile`` 走的都是 ``updateUser``
  （整行动态更新），XML 里那条 ``updateUserStatus`` 是死语句 —— 别改用它；
* ``checkUserAllowed`` 只看 ``userId == 1``，而 ``checkPhoneUnique`` 用 ``user_id == -1``
  作为"新建用户"的哨兵，两者不是同一个判据。

``selectUserList`` 上的 ``@DataScope`` 已经改成显式调用，这里顺带验证切面语义（管理员不过滤、
``dataScope=1`` 清空片段、同一实体复用时片段是 ``put`` **覆盖**而不是 ``AND`` 叠加）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pytest

from app.common.constant.constants import PROCUREMENT_MANAGER_ROLE_KEY
from app.common.constant.user_constants import DEFAULT_PWD, NOT_UNIQUE_OLD, UNIQUE_OLD
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.exception.exceptions import CustomException
from app.framework.aspectj.data_scope_aspect import DATA_SCOPE
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.common.core.domain.model.login_user import LoginUser
from app.system.domain.sys_user_post import SysUserPost
from app.system.domain.sys_user_role import SysUserRole
from app.system.service.sys_user_service import (
    ACCOUNT_INVALID_MESSAGE,
    CHECK_USER_ALLOWED_MESSAGE,
    FORGOT_PWD_FAILED_MESSAGE,
    IMPORT_FAILURE_PREFIX,
    IMPORT_INIT_PASSWORD_KEY,
    IMPORT_SUCCESS_PREFIX,
    IMPORT_USER_EMPTY_MESSAGE,
    RESET_PWD_FAILED_MESSAGE,
    VCODE_INVALID_MESSAGE,
    SysUserService,
)

# --------------------------------------------------------------------------- fakes


class _FakeUserMapper:
    """``SysUserMapper`` 的代言人：记录调用、返回预置结果。"""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.user_list_result: List[SysUser] = []
        self.user_name_unique_count = 0
        self.phone_info: Optional[SysUser] = None
        self.email_info: Optional[SysUser] = None
        self.insert_result = 1
        self.inserted: Optional[SysUser] = None
        self.update_result = 1
        self.updated: Optional[SysUser] = None
        self.updated_by_buss_id: Optional[SysUser] = None
        self.updated_by_buss_id_type: Optional[SysUser] = None
        self.delete_result = 1
        self.update_pwd_result = 1
        self.update_pwd_args: Optional[tuple] = None
        self.reset_pwd_result = 1
        self.avatar_result = 1
        self.pwd_judge_result: Optional[SysUser] = None
        self.user_by_id: Optional[SysUser] = None
        self.user_by_name: Optional[SysUser] = None
        #: 按账号精确预置查询结果（优先于 ``user_by_name``）—— ``importUser`` 逐行查库，
        #: 一个恒定返回值会让每一行都“已存在”。
        self.existing_users: Dict[str, SysUser] = {}
        self.lastrowid = 99

    # -- selects
    def select_user_list(self, user: SysUser) -> List[SysUser]:
        self.calls.append(("select_user_list", user))
        return list(self.user_list_result)

    def select_user_by_id(self, user_id: int) -> Optional[SysUser]:
        self.calls.append(("select_user_by_id", user_id))
        return self.user_by_id

    def select_user_by_user_name(self, user_name: str) -> Optional[SysUser]:
        self.calls.append(("select_user_by_user_name", user_name))
        if user_name in self.existing_users:
            return self.existing_users[user_name]
        return self.user_by_name

    def select_user_by_cert_entity_id(self, cert_entity_id: str) -> Optional[SysUser]:
        self.calls.append(("select_user_by_cert_entity_id", cert_entity_id))
        return self.user_by_name

    def check_user_name_unique(self, user_name: str) -> int:
        self.calls.append(("check_user_name_unique", user_name))
        return self.user_name_unique_count

    def check_phone_unique(self, phonenumber: str) -> Optional[SysUser]:
        self.calls.append(("check_phone_unique", phonenumber))
        return self.phone_info

    def check_email_unique(self, email: str) -> Optional[SysUser]:
        self.calls.append(("check_email_unique", email))
        return self.email_info

    # -- writes
    def insert_user(self, user: SysUser) -> int:
        self.calls.append(("insert_user", user))
        self.inserted = user
        # Java: useGeneratedKeys 回写 userId
        user.user_id = self.lastrowid
        return self.insert_result

    def update_user(self, user: SysUser) -> int:
        self.calls.append(("update_user", user))
        self.updated = user
        return self.update_result

    def update_user_info_by_buss_id(self, user: SysUser) -> int:
        self.calls.append(("update_user_info_by_buss_id", user))
        self.updated_by_buss_id = user
        return self.update_result

    def update_user_info_by_buss_id_and_user_type(self, user: SysUser) -> int:
        self.calls.append(("update_user_info_by_buss_id_and_user_type", user))
        self.updated_by_buss_id_type = user
        return self.update_result

    def delete_user_by_id(self, user_id: int) -> int:
        self.calls.append(("delete_user_by_id", user_id))
        return self.delete_result

    def delete_user_by_ids(self, user_ids: Sequence[int]) -> int:
        self.calls.append(("delete_user_by_ids", list(user_ids)))
        return self.delete_result

    def update_user_pwd(self, phonenumber: str, password: str, user_name: str) -> int:
        self.calls.append(("update_user_pwd", phonenumber, password, user_name))
        self.update_pwd_args = (phonenumber, password, user_name)
        return self.update_pwd_result

    def reset_user_pwd(self, user_name: str, password: str) -> int:
        self.calls.append(("reset_user_pwd", user_name, password))
        return self.reset_pwd_result

    def update_user_avatar(self, user_name: str, avatar: str) -> int:
        self.calls.append(("update_user_avatar", user_name, avatar))
        return self.avatar_result

    def select_pwd_judge(self, user_id: int) -> Optional[SysUser]:
        self.calls.append(("select_pwd_judge", user_id))
        return self.pwd_judge_result


class _FakeRoleMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.roles_by_user_name: List[SysRole] = []
        self.role_list_by_user_id: List[int] = []
        self.role_by_id: Optional[SysRole] = None

    def select_roles_by_user_name(self, user_name: str) -> List[SysRole]:
        self.calls.append(("select_roles_by_user_name", user_name))
        return list(self.roles_by_user_name)

    def select_role_list_by_user_id(self, user_id: int) -> List[int]:
        self.calls.append(("select_role_list_by_user_id", user_id))
        return list(self.role_list_by_user_id)

    def select_role_by_id(self, role_id: int) -> Optional[SysRole]:
        self.calls.append(("select_role_by_id", role_id))
        return self.role_by_id


class _FakePostMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.posts_by_user_name: List[Any] = []

    def select_posts_by_user_name(self, user_name: str) -> List[Any]:
        self.calls.append(("select_posts_by_user_name", user_name))
        return list(self.posts_by_user_name)


class _FakeUserRoleMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.batch_payload: List[SysUserRole] = []
        self.delete_result = 1

    def delete_user_role_by_user_id(self, user_id: int) -> int:
        self.calls.append(("delete_user_role_by_user_id", user_id))
        return self.delete_result

    def delete_user_role(self, user_ids: Sequence[int]) -> int:
        self.calls.append(("delete_user_role", list(user_ids)))
        return self.delete_result

    def batch_user_role(self, rows: List[SysUserRole]) -> int:
        self.calls.append(("batch_user_role", len(rows)))
        self.batch_payload = list(rows)
        return len(rows)


class _FakeUserPostMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.batch_payload: List[SysUserPost] = []
        self.delete_result = 1

    def delete_user_post_by_user_id(self, user_id: int) -> int:
        self.calls.append(("delete_user_post_by_user_id", user_id))
        return self.delete_result

    def delete_user_post(self, user_ids: Sequence[int]) -> int:
        self.calls.append(("delete_user_post", list(user_ids)))
        return self.delete_result

    def batch_user_post(self, rows: List[SysUserPost]) -> int:
        self.calls.append(("batch_user_post", len(rows)))
        self.batch_payload = list(rows)
        return len(rows)


class _FakeDeptMapper:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.dept_by_id: Optional[SysDept] = None

    def select_dept_by_id(self, dept_id: int) -> Optional[SysDept]:
        self.calls.append(("select_dept_by_id", dept_id))
        return self.dept_by_id


class _FakeDeptService:
    def __init__(self, head_office: Optional[List[SysDept]] = None) -> None:
        self.head_office = head_office
        self.calls = 0

    def select_head_office(self) -> Optional[List[SysDept]]:
        self.calls += 1
        return self.head_office


class _FakeRoleService:
    def __init__(self, role_list: Optional[List[SysRole]] = None) -> None:
        self.role_list = role_list or []
        self.calls: List[SysRole] = []

    def select_role_list(self, role: SysRole) -> List[SysRole]:
        self.calls.append(role)
        return list(self.role_list)


class _FakeRedisCache:
    def __init__(self, values: Optional[Dict[str, Any]] = None) -> None:
        self.values = values or {}
        self.calls: List[str] = []

    def get_cache_object(self, key: str) -> Any:
        self.calls.append(key)
        return self.values.get(key)


class _FakeConfigService:
    """``ISysConfigService`` 里只有 ``importUser`` 用到的那一个方法."""

    def __init__(self, init_password: Optional[str] = "123456") -> None:
        self.init_password = init_password
        self.calls: List[Optional[str]] = []

    def select_config_by_key(self, config_key: Optional[str]) -> Optional[str]:
        self.calls.append(config_key)
        return self.init_password


class _Bundle:
    """一次性持有所有假协作者，省掉每个用例 8 行构造。"""

    def __init__(self) -> None:
        self.mapper = _FakeUserMapper()
        self.role_mapper = _FakeRoleMapper()
        self.post_mapper = _FakePostMapper()
        self.user_role_mapper = _FakeUserRoleMapper()
        self.user_post_mapper = _FakeUserPostMapper()
        self.dept_mapper = _FakeDeptMapper()
        self.redis = _FakeRedisCache()
        self.dept_service = _FakeDeptService()
        self.role_service = _FakeRoleService()
        self.config_service = _FakeConfigService()
        self.service = SysUserService(
            mapper=self.mapper,
            role_mapper=self.role_mapper,
            post_mapper=self.post_mapper,
            user_role_mapper=self.user_role_mapper,
            user_post_mapper=self.user_post_mapper,
            dept_mapper=self.dept_mapper,
            redis_cache=self.redis,
            dept_service=self.dept_service,
            role_service=self.role_service,
            config_service=self.config_service,
        )

    def order(self, *names: str) -> List[str]:
        """按调用顺序返回指定这几类调用的名字。"""
        return [call[0] for call in self.mapper.calls if call[0] in names]


@pytest.fixture(autouse=True)
def _isolate() -> Any:
    SecurityContextHolder.clear_context()
    yield
    SecurityContextHolder.clear_context()


@pytest.fixture()
def bundle() -> _Bundle:
    return _Bundle()


def authenticate(user: SysUser, permissions: Optional[set] = None) -> LoginUser:
    login_user = LoginUser(user=user, permissions=permissions or set())
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return login_user


# --------------------------------------------------------------------------- @DataScope


class TestSelectUserListDataScope:
    """Java: ``@DataScope(deptAlias = "d", userAlias = "u")`` 在方法体之前执行。"""

    def test_the_fragment_is_written_into_the_entity_params(
        self, bundle: _Bundle
    ) -> None:
        authenticate(
            SysUser(
                user_id=2,
                dept_id=105,
                roles=[SysRole(role_id=2, data_scope="5")],
            )
        )
        user = SysUser()

        bundle.service.select_user_list(user)

        assert user.params[DATA_SCOPE] == " AND (u.user_id = 2 )"

    def test_an_admin_is_never_filtered(self, bundle: _Bundle) -> None:
        authenticate(SysUser(user_id=1, roles=[SysRole(role_id=2, data_scope="5")]))
        user = SysUser()

        bundle.service.select_user_list(user)

        assert DATA_SCOPE not in user.params

    def test_no_login_means_no_filter(self, bundle: _Bundle) -> None:
        user = SysUser()

        bundle.service.select_user_list(user)

        assert DATA_SCOPE not in user.params

    def test_data_scope_all_clears_an_earlier_fragment(
        self, bundle: _Bundle
    ) -> None:
        """``dataScope=1`` 时 Java ``break`` 并把已拼接的内容清空 -> 不写 params。"""
        authenticate(
            SysUser(
                user_id=2,
                dept_id=105,
                roles=[SysRole(role_id=3, data_scope="1")],
            )
        )
        user = SysUser()

        bundle.service.select_user_list(user)

        assert DATA_SCOPE not in user.params

    def test_a_second_call_overwrites_the_fragment(self, bundle: _Bundle) -> None:
        """Java 是 ``params.put(...)``，不是 ``append`` —— 两次结果相同，不会叠加。"""
        authenticate(SysUser(user_id=2, roles=[SysRole(role_id=2, data_scope="3")]))
        user = SysUser()

        bundle.service.select_user_list(user)
        bundle.service.select_user_list(user)

        assert user.params[DATA_SCOPE] == " AND (d.dept_id = null )"

    def test_a_stale_fragment_survives_a_second_call_that_produces_none(
        self, bundle: _Bundle
    ) -> None:
        """本项目没有 ``@After clearDataScope``：第二次没生成片段时，旧的会留着。"""
        login_user = authenticate(
            SysUser(user_id=2, roles=[SysRole(role_id=2, data_scope="3")])
        )
        user = SysUser()

        bundle.service.select_user_list(user)
        # 角色权限被改成“全部数据”，第二次不会生成任何片段
        login_user.user.roles = [SysRole(role_id=3, data_scope="1")]
        bundle.service.select_user_list(user)

        assert user.params[DATA_SCOPE] == " AND (d.dept_id = null )"

    def test_the_mapper_is_always_called(self, bundle: _Bundle) -> None:
        authenticate(SysUser(user_id=2, roles=[SysRole(role_id=2, data_scope="1")]))

        bundle.service.select_user_list(SysUser())

        assert bundle.order("select_user_list") == ["select_user_list"]


# --------------------------------------------------------------------------- delegations


class TestDelegations:
    def test_select_user_by_id(self, bundle: _Bundle) -> None:
        bundle.mapper.user_by_id = SysUser(user_id=2, user_name="ry")

        user = bundle.service.select_user_by_id(2)

        assert user is not None and user.user_name == "ry"
        assert bundle.mapper.calls == [("select_user_by_id", 2)]

    def test_select_user_by_user_name(self, bundle: _Bundle) -> None:
        bundle.mapper.user_by_name = SysUser(user_id=2)

        assert bundle.service.select_user_by_user_name("ry") is not None
        assert bundle.mapper.calls == [("select_user_by_user_name", "ry")]

    def test_select_user_by_cert_entity_id(self, bundle: _Bundle) -> None:
        bundle.mapper.user_by_name = SysUser(user_id=2)

        assert bundle.service.select_user_by_cert_entity_id("CERT") is not None
        assert bundle.mapper.calls == [("select_user_by_cert_entity_id", "CERT")]

    def test_select_user_role_group_joins_role_names(
        self, bundle: _Bundle
    ) -> None:
        bundle.role_mapper.roles_by_user_name = [
            SysRole(role_id=1, role_name="管理员"),
            SysRole(role_id=2, role_name="普通角色"),
        ]

        assert bundle.service.select_user_role_group("ry") == "管理员,普通角色"

    def test_select_user_role_group_is_empty_without_roles(
        self, bundle: _Bundle
    ) -> None:
        assert bundle.service.select_user_role_group("ry") == ""

    def test_select_user_post_group_joins_post_names(
        self, bundle: _Bundle
    ) -> None:
        class _Post:
            def __init__(self, name: str) -> None:
                self.post_name = name

        bundle.post_mapper.posts_by_user_name = [_Post("ceo"), _Post("se")]

        assert bundle.service.select_user_post_group("ry") == "ceo,se"


# --------------------------------------------------------------------------- uniqueness


class TestUniqueness:
    def test_a_taken_user_name_is_not_unique(self, bundle: _Bundle) -> None:
        bundle.mapper.user_name_unique_count = 1
        assert bundle.service.check_user_name_unique("ry") == NOT_UNIQUE_OLD

    def test_a_free_user_name_is_unique(self, bundle: _Bundle) -> None:
        assert bundle.service.check_user_name_unique("ry") == UNIQUE_OLD

    def test_a_phone_belonging_to_another_user_is_not_unique(
        self, bundle: _Bundle
    ) -> None:
        bundle.mapper.phone_info = SysUser(user_id=5, phonenumber="158")

        assert bundle.service.check_phone_unique(SysUser(user_id=2, phonenumber="158")) == NOT_UNIQUE_OLD

    def test_a_phone_belonging_to_the_same_user_is_unique(
        self, bundle: _Bundle
    ) -> None:
        bundle.mapper.phone_info = SysUser(user_id=2, phonenumber="158")

        assert bundle.service.check_phone_unique(SysUser(user_id=2, phonenumber="158")) == UNIQUE_OLD

    def test_a_new_user_compares_against_the_minus_one_sentinel(
        self, bundle: _Bundle
    ) -> None:
        """Java: ``Long userId = user.getUserId() == null ? -1L : user.getUserId();``."""
        bundle.mapper.phone_info = SysUser(user_id=5, phonenumber="158")

        assert bundle.service.check_phone_unique(SysUser(phonenumber="158")) == NOT_UNIQUE_OLD

    def test_a_free_phone_is_unique(self, bundle: _Bundle) -> None:
        assert bundle.service.check_phone_unique(SysUser(phonenumber="158")) == UNIQUE_OLD

    def test_the_same_rules_apply_to_email(self, bundle: _Bundle) -> None:
        bundle.mapper.email_info = SysUser(user_id=5, email="a@b.c")

        assert bundle.service.check_email_unique(SysUser(user_id=2, email="a@b.c")) == NOT_UNIQUE_OLD
        assert bundle.service.check_email_unique(SysUser(user_id=5, email="a@b.c")) == UNIQUE_OLD


# --------------------------------------------------------------------------- checkUserAllowed


class TestCheckUserAllowed:
    def test_user_id_one_is_refused(self, bundle: _Bundle) -> None:
        with pytest.raises(CustomException) as caught:
            bundle.service.check_user_allowed(SysUser(user_id=1))

        assert str(caught.value) == CHECK_USER_ALLOWED_MESSAGE

    def test_any_other_user_passes(self, bundle: _Bundle) -> None:
        bundle.service.check_user_allowed(SysUser(user_id=2))

    def test_a_user_without_an_id_passes(self, bundle: _Bundle) -> None:
        """Java: ``if (StringUtils.isNotNull(userId) && user.isAdmin())``."""
        bundle.service.check_user_allowed(SysUser())


# --------------------------------------------------------------------------- insert / update


class TestInsertUser:
    def test_the_department_supplies_buss_name_and_tenant(
        self, bundle: _Bundle
    ) -> None:
        bundle.dept_mapper.dept_by_id = SysDept(dept_id=105, dept_name="研发部门", tenant_id=100)
        user = SysUser(dept_id=105, user_name="ry")

        bundle.service.insert_user(user)

        assert (user.buss_name, user.tenant_id) == ("研发部门", 100)

    def test_without_a_department_no_lookup_happens(
        self, bundle: _Bundle
    ) -> None:
        user = SysUser(user_name="ry")

        bundle.service.insert_user(user)

        assert bundle.dept_mapper.calls == []
        assert user.buss_name is None

    def test_post_and_role_links_are_written_after_the_user(
        self, bundle: _Bundle
    ) -> None:
        user = SysUser(user_name="ry", role_ids=[1, 2], post_ids=[3])

        bundle.service.insert_user(user)

        assert bundle.order("insert_user") == ["insert_user"]
        assert [call[0] for call in bundle.user_role_mapper.calls] == ["batch_user_role"]
        assert [call[0] for call in bundle.user_post_mapper.calls] == ["batch_user_post"]
        assert [(r.user_id, r.role_id) for r in bundle.user_role_mapper.batch_payload] == [
            (99, 1),
            (99, 2),
        ]
        assert [(p.user_id, p.post_id) for p in bundle.user_post_mapper.batch_payload] == [(99, 3)]

    def test_null_link_arrays_write_nothing(self, bundle: _Bundle) -> None:
        bundle.service.insert_user(SysUser(user_name="ry"))

        assert bundle.user_role_mapper.calls == []
        assert bundle.user_post_mapper.calls == []

    def test_the_mapper_rowcount_is_returned(self, bundle: _Bundle) -> None:
        bundle.mapper.insert_result = 1

        assert bundle.service.insert_user(SysUser(user_name="ry")) == 1


class TestUpdateUser:
    def test_the_link_tables_are_rebuilt_in_java_order(
        self, bundle: _Bundle
    ) -> None:
        user = SysUser(user_id=2, role_ids=[1], post_ids=[3])

        bundle.service.update_user(user)

        assert [call[0] for call in bundle.user_role_mapper.calls] == [
            "delete_user_role_by_user_id",
            "batch_user_role",
        ]
        assert [call[0] for call in bundle.user_post_mapper.calls] == [
            "delete_user_post_by_user_id",
            "batch_user_post",
        ]
        assert bundle.mapper.updated is user

    def test_the_department_is_re_resolved_for_the_denormalised_name(
        self, bundle: _Bundle
    ) -> None:
        bundle.dept_mapper.dept_by_id = SysDept(dept_id=105, dept_name="研发部门", tenant_id=100)
        user = SysUser(user_id=2, dept_id=105)

        bundle.service.update_user(user)

        assert (user.buss_name, user.tenant_id) == ("研发部门", 100)

    def test_update_user_status_goes_through_update_user(
        self, bundle: _Bundle
    ) -> None:
        """XML 里那条 ``updateUserStatus`` 没有调用者 —— 别改用它。"""
        user = SysUser(user_id=2, status="1")

        bundle.service.update_user_status(user)

        assert bundle.order("update_user") == ["update_user"]

    def test_reset_pwd_goes_through_update_user(self, bundle: _Bundle) -> None:
        bundle.service.reset_pwd(SysUser(user_id=2, password="hash"))

        assert bundle.order("update_user") == ["update_user"]

    def test_update_user_profile_goes_through_update_user(
        self, bundle: _Bundle
    ) -> None:
        bundle.service.update_user_profile(SysUser(user_id=2, nick_name="新"))

        assert bundle.order("update_user") == ["update_user"]

    def test_avatar_returns_true_only_when_a_row_changed(
        self, bundle: _Bundle
    ) -> None:
        assert bundle.service.update_user_avatar("ry", "/a.png") is True
        bundle.mapper.avatar_result = 0
        assert bundle.service.update_user_avatar("ry", "/a.png") is False

    def test_update_by_buss_id_variants_delegate(self, bundle: _Bundle) -> None:
        user = SysUser(buss_id="B1", nick_name="专家")

        assert bundle.service.update_user_info_by_buss_id(user) == 1
        bundle.service.update_user_info_by_buss_id_and_user_type(user)

        assert bundle.mapper.updated_by_buss_id is user
        assert bundle.mapper.updated_by_buss_id_type is user


# --------------------------------------------------------------------------- deletes


class TestDeleteUser:
    def test_single_delete_clears_the_links_first(
        self, bundle: _Bundle
    ) -> None:
        bundle.service.delete_user_by_id(3)

        assert [call[0] for call in bundle.user_role_mapper.calls] == [
            "delete_user_role_by_user_id"
        ]
        assert [call[0] for call in bundle.user_post_mapper.calls] == [
            "delete_user_post_by_user_id"
        ]
        assert bundle.order("delete_user_by_id") == ["delete_user_by_id"]

    def test_batch_delete_checks_every_id_before_deleting(
        self, bundle: _Bundle
    ) -> None:
        with pytest.raises(CustomException):
            bundle.service.delete_user_by_ids([2, 1, 3])

        # 管理员在第二个位置被发现，业务表一行都没动
        assert bundle.user_role_mapper.calls == []
        assert bundle.mapper.calls == []

    def test_batch_delete_passes_the_whole_array_to_each_mapper(
        self, bundle: _Bundle
    ) -> None:
        bundle.service.delete_user_by_ids([2, 3])

        assert bundle.user_role_mapper.calls == [("delete_user_role", [2, 3])]
        assert bundle.user_post_mapper.calls == [("delete_user_post", [2, 3])]
        assert bundle.mapper.calls[-1] == ("delete_user_by_ids", [2, 3])


# --------------------------------------------------------------------------- current user


class TestSelectCurrentUser:
    def test_a_head_office_member_is_flagged(self, bundle: _Bundle) -> None:
        authenticate(SysUser(user_id=2, user_name="ry", dept_id=100))
        bundle.dept_service.head_office = [SysDept(dept_id=100), SysDept(dept_id=101)]

        current = bundle.service.select_current_user()

        assert current.head_office is True

    def test_a_non_head_office_member_is_not_flagged(
        self, bundle: _Bundle
    ) -> None:
        authenticate(SysUser(user_id=2, user_name="ry", dept_id=200))
        bundle.dept_service.head_office = [SysDept(dept_id=100)]

        assert bundle.service.select_current_user().head_office is False

    def test_no_head_office_at_all_leaves_the_flag_false(
        self, bundle: _Bundle
    ) -> None:
        authenticate(SysUser(user_id=2, user_name="ry", dept_id=100))
        bundle.dept_service.head_office = None

        assert bundle.service.select_current_user().head_office is False

    def test_the_procurement_manager_flag_needs_the_role(
        self, bundle: _Bundle
    ) -> None:
        authenticate(SysUser(user_id=2, user_name="ry", dept_id=100))
        bundle.role_service.role_list = [SysRole(role_id=7, role_key=PROCUREMENT_MANAGER_ROLE_KEY)]
        bundle.role_mapper.roles_by_user_name = [SysRole(role_id=7, role_key=PROCUREMENT_MANAGER_ROLE_KEY)]

        current = bundle.service.select_current_user()

        assert current.procurement_manager is True
        # 查询条件就是采购经理的角色 key
        assert bundle.role_service.calls[0].role_key == PROCUREMENT_MANAGER_ROLE_KEY

    def test_a_missing_cgjl_role_short_circuits_the_second_query(
        self, bundle: _Bundle
    ) -> None:
        """连"采购经理"这个角色都没有时，Java 不再查用户角色。"""
        authenticate(SysUser(user_id=2, user_name="ry"))
        bundle.role_service.role_list = []

        current = bundle.service.select_current_user()

        assert current.procurement_manager is False
        assert bundle.role_mapper.calls == []

    def test_a_user_without_the_role_is_not_the_procurement_manager(
        self, bundle: _Bundle
    ) -> None:
        authenticate(SysUser(user_id=2, user_name="ry"))
        bundle.role_service.role_list = [SysRole(role_id=7)]
        bundle.role_mapper.roles_by_user_name = [SysRole(role_id=8)]

        assert bundle.service.select_current_user().procurement_manager is False

    def test_only_four_fields_are_returned(self, bundle: _Bundle) -> None:
        """Java 返回的是新 ``SysUser``，其余字段都是默认值。"""
        authenticate(SysUser(user_id=2, user_name="ry", nick_name="若依", dept_id=100))

        current = bundle.service.select_current_user()

        assert current.user_id == 2
        assert current.nick_name is None
        assert current.user_name is None
        assert current.pj_flag == 0


# --------------------------------------------------------------------------- password recovery


class TestUpdateUserPwd:
    def test_a_missing_vcode_is_rejected(self, bundle: _Bundle) -> None:
        result = bundle.service.update_user_pwd(
            SysUser(phonenumber="158", remark="1234")
        )

        assert result == {"code": 500, "msg": VCODE_INVALID_MESSAGE}
        assert bundle.mapper.calls == []

    def test_a_mismatched_vcode_is_rejected(self, bundle: _Bundle) -> None:
        bundle.redis.values["158"] = "9999"

        result = bundle.service.update_user_pwd(
            SysUser(phonenumber="158", remark="1234")
        )

        assert result["msg"] == VCODE_INVALID_MESSAGE

    def test_an_account_that_matches_no_row_is_rejected(
        self, bundle: _Bundle
    ) -> None:
        bundle.redis.values["158"] = "1234"
        bundle.mapper.user_list_result = []

        result = bundle.service.update_user_pwd(
            SysUser(phonenumber="158", remark="1234", user_name="ry")
        )

        assert result["msg"] == ACCOUNT_INVALID_MESSAGE

    def test_two_matching_rows_are_also_rejected(
        self, bundle: _Bundle
    ) -> None:
        """``len(sysUsers) == 0 || len(sysUsers) > 1`` —— 账号+手机号必须唯一定位。"""
        bundle.redis.values["158"] = "1234"
        bundle.mapper.user_list_result = [SysUser(user_id=2), SysUser(user_id=3)]

        result = bundle.service.update_user_pwd(
            SysUser(phonenumber="158", remark="1234", user_name="ry")
        )

        assert result["msg"] == ACCOUNT_INVALID_MESSAGE

    def test_a_successful_reset_returns_the_default_password(
        self, bundle: _Bundle
    ) -> None:
        bundle.redis.values["158"] = "1234"
        bundle.mapper.user_list_result = [SysUser(user_id=2)]

        result = bundle.service.update_user_pwd(
            SysUser(phonenumber="158", remark="1234", user_name="ry")
        )

        assert result["code"] == 200
        assert result["msg"] == "密码已重置为"
        assert result["data"] == DEFAULT_PWD
        phone, password, user_name = bundle.mapper.update_pwd_args or ("", "", "")
        assert (phone, user_name) == ("158", "ry")
        # 落库的是 bcrypt 摘要，不是明文
        assert password != DEFAULT_PWD
        assert password.startswith("$2")

    def test_a_zero_rowcount_reports_the_failure(self, bundle: _Bundle) -> None:
        bundle.redis.values["158"] = "1234"
        bundle.mapper.user_list_result = [SysUser(user_id=2)]
        bundle.mapper.update_pwd_result = 0

        result = bundle.service.update_user_pwd(
            SysUser(phonenumber="158", remark="1234", user_name="ry")
        )

        assert result["msg"] == RESET_PWD_FAILED_MESSAGE


class TestForgotPassword:
    def test_the_vcode_comparison_ignores_case(self, bundle: _Bundle) -> None:
        bundle.redis.values["158"] = "AbCd"
        bundle.mapper.user_list_result = [SysUser(user_id=2)]

        result = bundle.service.forgot_password(
            SysUser(phonenumber="158", remark="abcd", user_name="ry", password="Abc12345!")
        )

        assert result["code"] == 200

    def test_the_new_password_is_echoed_in_clear_text(
        self, bundle: _Bundle
    ) -> None:
        bundle.redis.values["158"] = "1234"
        bundle.mapper.user_list_result = [SysUser(user_id=2)]

        result = bundle.service.forgot_password(
            SysUser(phonenumber="158", remark="1234", user_name="ry", password="Abc12345!")
        )

        assert result["msg"] == "密码已重置为: "
        assert result["data"] == "Abc12345!"
        phone, stored, _ = bundle.mapper.update_pwd_args or ("", "", "")
        assert stored != "Abc12345!"
        assert stored.startswith("$2")

    def test_a_failure_uses_the_half_width_message(self, bundle: _Bundle) -> None:
        """注意与 ``updateUserPwd`` 的**全角**感叹号不同。"""
        bundle.redis.values["158"] = "1234"
        bundle.mapper.user_list_result = [SysUser(user_id=2)]
        bundle.mapper.update_pwd_result = 0

        result = bundle.service.forgot_password(
            SysUser(phonenumber="158", remark="1234", user_name="ry", password="Abc12345!")
        )

        assert result["msg"] == FORGOT_PWD_FAILED_MESSAGE

    def test_a_missing_vcode_is_rejected(self, bundle: _Bundle) -> None:
        result = bundle.service.forgot_password(
            SysUser(phonenumber="158", remark=None, password="Abc12345!")
        )

        assert result["msg"] == VCODE_INVALID_MESSAGE


# --------------------------------------------------------------------------- 导入用户


class TestImportUser:
    """Java: ``SysUserServiceImpl#importUser(List<SysUser>, Boolean, String)``.

    控制器 ``importData`` 端点的全部业务逻辑都在这里，控制器只做 Excel 解析。
    """

    def test_an_empty_list_is_rejected(self, bundle: _Bundle) -> None:
        with pytest.raises(CustomException) as exc_info:
            bundle.service.import_user([], False, "ry")

        assert exc_info.value.args[0] == IMPORT_USER_EMPTY_MESSAGE

    def test_none_is_rejected_like_an_empty_list(self, bundle: _Bundle) -> None:
        """Java: ``StringUtils.isNull(userList) || userList.size() == 0`` —— 两个判据."""
        with pytest.raises(CustomException) as exc_info:
            bundle.service.import_user(None, False, "ry")

        assert exc_info.value.args[0] == IMPORT_USER_EMPTY_MESSAGE

    def test_the_init_password_comes_from_sys_config(self, bundle: _Bundle) -> None:
        bundle.service.import_user([SysUser(user_name="new1")], False, "ry")

        assert bundle.config_service.calls == [IMPORT_INIT_PASSWORD_KEY]
        assert IMPORT_INIT_PASSWORD_KEY == "sys.user.initPassword"

    def test_a_new_user_is_inserted_with_the_encrypted_init_password(
        self, bundle: _Bundle
    ) -> None:
        message = bundle.service.import_user([SysUser(user_name="new1")], False, "ry")

        inserted = bundle.mapper.inserted
        assert inserted is not None
        assert inserted.user_name == "new1"
        # bcrypt 哈希，不是明文
        assert inserted.password is not None
        assert inserted.password.startswith("$2")
        assert inserted.create_by == "ry"
        assert message == IMPORT_SUCCESS_PREFIX.format(1) + "<br/>1、账号 new1 导入成功"
        assert message.startswith("恭喜您，数据已全部导入成功！共 1 条")

    def test_an_existing_user_without_update_support_fails(self, bundle: _Bundle) -> None:
        bundle.mapper.user_by_name = SysUser(user_id=2, user_name="new1")

        with pytest.raises(CustomException) as exc_info:
            bundle.service.import_user([SysUser(user_name="new1")], False, "ry")

        assert bundle.mapper.inserted is None
        assert bundle.mapper.updated is None
        assert exc_info.value.args[0] == (
            IMPORT_FAILURE_PREFIX.format(1) + "<br/>1、账号 new1 已存在"
        )

    def test_an_existing_user_with_update_support_is_updated(self, bundle: _Bundle) -> None:
        bundle.mapper.user_by_name = SysUser(user_id=2, user_name="new1")

        message = bundle.service.import_user([SysUser(user_name="new1")], True, "ry")

        assert bundle.mapper.updated is not None
        assert bundle.mapper.updated.update_by == "ry"
        assert message == IMPORT_SUCCESS_PREFIX.format(1) + "<br/>1、账号 new1 更新成功"

    def test_each_row_is_looked_up_by_user_name(self, bundle: _Bundle) -> None:
        bundle.service.import_user(
            [SysUser(user_name="a"), SysUser(user_name="b")], False, "ry"
        )

        assert bundle.order("select_user_by_user_name") == [
            "select_user_by_user_name",
            "select_user_by_user_name",
        ]

    def test_a_failure_on_one_row_still_raises_after_processing_the_rest(
        self, bundle: _Bundle
    ) -> None:
        """每行独立 ``try/catch`` —— 单行失败不中断整批.

        两行都成功之后才汇总抛错；成功计数与失败计数**各自独立**编号。
        """
        bundle.mapper.existing_users["taken"] = SysUser(user_id=2, user_name="taken")

        with pytest.raises(CustomException) as exc_info:
            bundle.service.import_user(
                [SysUser(user_name="ok1"), SysUser(user_name="taken")], False, "ry"
            )

        # 第一行插进去了（失败不中断），第二行报“已存在”
        assert bundle.mapper.inserted is not None
        assert exc_info.value.args[0] == (
            IMPORT_FAILURE_PREFIX.format(1) + "<br/>1、账号 taken 已存在"
        )

    def test_an_exception_inside_the_loop_is_captured_per_row(self, bundle: _Bundle) -> None:
        """Java: ``catch (Exception e)`` -> 明细串里拼上异常信息.

        ``insertUser`` 内部的 ``deptId`` 查询返回 ``None`` 时会 NPE —— 用这个复刻。
        """
        users = [SysUser(user_name="boom", dept_id=999)]

        with pytest.raises(CustomException) as exc_info:
            bundle.service.import_user(users, False, "ry")

        message = exc_info.value.args[0]
        assert message.startswith(IMPORT_FAILURE_PREFIX.format(1))
        assert "<br/>1、账号 boom 导入失败：" in message

    def test_a_null_user_name_renders_the_literal_null(self, bundle: _Bundle) -> None:
        """Java 字符串拼接 ``"..." + null`` 得到字面量 ``"null"``，不抛 NPE."""
        message = bundle.service.import_user([SysUser(user_name=None)], False, "ry")

        assert "账号 null 导入成功" in message

    def test_the_success_counter_numbers_successes_only(self, bundle: _Bundle) -> None:
        bundle.mapper.existing_users["taken"] = SysUser(user_id=2, user_name="taken")

        message = bundle.service.import_user(
            [SysUser(user_name="ok1"), SysUser(user_name="ok2")], False, "ry"
        )

        # 成功行的编号只数成功——失败行不占号
        assert message == (
            IMPORT_SUCCESS_PREFIX.format(2)
            + "<br/>1、账号 ok1 导入成功"
            + "<br/>2、账号 ok2 导入成功"
        )


# --------------------------------------------------------------------------- misc


class TestPasswordJudge:
    def test_select_pwd_judge_delegates(self, bundle: _Bundle) -> None:
        bundle.mapper.pwd_judge_result = SysUser(pj_flag=3)

        result = bundle.service.select_pwd_judge(2)

        assert result is not None and result.pj_flag == 3
        assert bundle.mapper.calls == [("select_pwd_judge", 2)]


class TestSingleton:
    def test_the_process_wide_service_is_cached(self) -> None:
        from app.system.service import sys_user_service as module

        module.reset_user_service()
        try:
            assert module.get_user_service() is module.get_user_service()
            module.reset_user_service()
            assert module.get_user_service() is not None
        finally:
            module.reset_user_service()
