"""``SysUserController`` -- ``/system/user`` 的 21 个端点.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/.../web/controller/system/SysUserController.java
#   + ruoyi-common/.../core/controller/BaseController.java

这一层测什么
------------
Service 已经被 ``test_sys_user_service.py`` 覆盖，所以这里全部注入假 Service，只测
**控制器自己的判断**。它们几乎全是"前端约定"，改掉了接口不会报错，只会让页面静默失效：

* ``list`` 强制 ``userType = "1"``；``listAll`` 强制当前租户；``listSameUtil`` 还强制本部门；
* ``listutil`` 不认识 ``flag`` 时把 ``userId`` 置为 ``-1``（查不到任何人，**不是**查全部）；
* ``listTenantIdAll`` 缺租户时用 ``-1`` 而不是留空（留空等于"全租户"）；
* ``getInfo`` 对**被查看的人**判超管来决定是否隐藏 admin 角色；
* ``getroleUser`` **没有** ``startPage()``，所以返回全量而不是分页信封；
* ``bindUky`` 的"已绑定"判据是 ``selectUserList(...)[0].userId != 自己``；
* ``export`` / ``importTemplate`` / ``importData`` 都返回 **``AjaxResult``**（文件名或
  明细串落在 ``msg`` 里），不是文件流。

``@Log`` 注解未迁移
-------------------
``add`` / ``edit`` / ``remove`` / ``resetPwd`` / ``changeStatus`` 在 Java 上带
``@Log(title = "用户管理", ...)``，由 ``LogAspect`` 异步写 ``sys_oper_log``。本阶段没有
``LogAspect``，因此这些操作不会留审计记录 —— 这是已知缺口，不是本文件的断言点。
"""

from __future__ import annotations

from io import BytesIO
from typing import Any, List, Optional, Sequence

import pytest
from openpyxl import Workbook, load_workbook
from starlette.datastructures import UploadFile
from starlette.requests import Request

from app.api.system import sys_user_controller as controller
from app.api.system.sys_user_controller import (
    ADD_EMAIL_EXISTS,
    ADD_PHONE_EXISTS,
    ADD_USER_NAME_EXISTS,
    EDIT_EMAIL_EXISTS,
    EDIT_PHONE_EXISTS,
    PASSWORD_INVALID_MESSAGE,
    UNKNOWN_FLAG_USER_ID,
    add,
    bind_uky,
    change_status,
    edit,
    export,
    get_info,
    get_info_by_id,
    getrole_user,
    import_data,
    import_template,
    list_all,
    list_by_dept,
    list_my,
    list_same_util,
    list_tenant_id_all,
    list_util,
    list_users,
    remove,
    reset_pwd,
    select_current_user,
)
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page
from app.common.exception.exceptions import AccessDeniedException, CustomException, UtilException
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.settings import reset_settings_cache
from app.system.domain.sys_post import SysPost

VALID_PASSWORD = "Abc12345!"


# --------------------------------------------------------------------------- fakes


class _FakeUserService:
    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysUser] = []
        #: 按调用顺序逐个消费；用完后退回 ``list_result``（同一份结果多次查询的场合）。
        self.list_results: List[List[SysUser]] = []
        self.user_by_id: Optional[SysUser] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        self.reset_result = 1
        self.status_result = 1
        self.name_unique = "0"
        self.phone_unique = "0"
        self.email_unique = "0"
        self.current_user = SysUser(user_id=2)
        self.allowed_error: Optional[BaseException] = None
        self.import_result = "恭喜您，数据已全部导入成功！共 0 条，数据如下："
        #: ``(user_list, is_update_support, oper_name)``
        self.imported: Optional[tuple] = None

    def select_user_list(self, user: SysUser) -> List[SysUser]:
        # 复制一份，避免断言被后续 mutate 影响
        self.calls.append(("select_user_list", user.model_copy(deep=True)))
        if self.list_results:
            return self.list_results.pop(0)
        # 注意不能 list() 复制：``PageList`` 的 total 要靠类型本身带出去。
        return self.list_result

    def select_user_by_id(self, user_id: int) -> Optional[SysUser]:
        self.calls.append(("select_user_by_id", user_id))
        return self.user_by_id

    def check_user_allowed(self, user: SysUser) -> None:
        self.calls.append(("check_user_allowed", user.user_id))
        if self.allowed_error is not None:
            raise self.allowed_error

    def check_user_name_unique(self, user_name: str) -> str:
        self.calls.append(("check_user_name_unique", user_name))
        return self.name_unique

    def check_phone_unique(self, user: SysUser) -> str:
        self.calls.append(("check_phone_unique", user.phonenumber))
        return self.phone_unique

    def check_email_unique(self, user: SysUser) -> str:
        self.calls.append(("check_email_unique", user.email))
        return self.email_unique

    def insert_user(self, user: SysUser) -> int:
        self.calls.append(("insert_user", user.model_copy(deep=True)))
        return self.insert_result

    def update_user(self, user: SysUser) -> int:
        self.calls.append(("update_user", user.model_copy(deep=True)))
        return self.update_result

    def update_user_status(self, user: SysUser) -> int:
        self.calls.append(("update_user_status", user.model_copy(deep=True)))
        return self.status_result

    def reset_pwd(self, user: SysUser) -> int:
        self.calls.append(("reset_pwd", user.model_copy(deep=True)))
        return self.reset_result

    def delete_user_by_ids(self, user_ids: Sequence[int]) -> int:
        self.calls.append(("delete_user_by_ids", list(user_ids)))
        return self.delete_result

    def select_current_user(self) -> SysUser:
        self.calls.append(("select_current_user",))
        return self.current_user

    def import_user(
        self, user_list: Sequence[SysUser], is_update_support: bool, oper_name: str
    ) -> str:
        self.calls.append(("import_user", len(user_list), is_update_support, oper_name))
        self.imported = (list(user_list), is_update_support, oper_name)
        return self.import_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _FakeRoleService:
    def __init__(self) -> None:
        self.roles: List[SysRole] = []
        self.role_ids: List[int] = []
        self.calls: List[str] = []

    def select_role_all(self) -> List[SysRole]:
        self.calls.append("select_role_all")
        return list(self.roles)

    def select_role_list_by_user_id(self, user_id: int) -> List[int]:
        self.calls.append("select_role_list_by_user_id")
        return list(self.role_ids)


class _FakePostService:
    def __init__(self) -> None:
        self.posts: List[SysPost] = []
        self.post_ids: List[int] = []
        self.calls: List[str] = []

    def select_post_all(self) -> List[SysPost]:
        self.calls.append("select_post_all")
        return list(self.posts)

    def select_post_list_by_user_id(self, user_id: int) -> List[int]:
        self.calls.append("select_post_list_by_user_id")
        return list(self.post_ids)


class _Bundle:
    def __init__(self) -> None:
        self.user = _FakeUserService()
        self.role = _FakeRoleService()
        self.post = _FakePostService()


@pytest.fixture(autouse=True)
def _isolate(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者与安全上下文。"""
    SecurityContextHolder.clear_context()
    clear_page()
    bundle = _Bundle()
    monkeypatch.setattr(controller, "_USER_SERVICE", bundle.user)
    monkeypatch.setattr(controller, "_ROLE_SERVICE", bundle.role)
    monkeypatch.setattr(controller, "_POST_SERVICE", bundle.post)
    yield bundle
    SecurityContextHolder.clear_context()
    clear_page()
    controller.reset_user_controller()


def authenticate(
    user_id: int = 2,
    user_name: str = "ry",
    permissions: Optional[set] = None,
    **kwargs: Any,
) -> SysUser:
    user = SysUser(user_id=user_id, user_name=user_name, **kwargs)
    login_user = LoginUser(user=user, permissions=permissions or {"*:*:*"})
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def login_user() -> LoginUser:
    return SecurityContextHolder.get_context().get_authentication().get_principal()


# --------------------------------------------------------------------------- 查询端点


class TestListUsers:
    def test_the_user_type_is_forced_to_institution(
        self, _isolate: _Bundle, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java: ``user.setUserType("1"); // 查询机构用户``."""
        authenticate()
        user = SysUser(user_type="9")

        list_users(user)

        assert user.user_type == "1"
        assert _isolate.user.of("select_user_list")[0][1].user_type == "1"

    def test_the_response_is_a_paged_table(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.list_result = [SysUser(user_id=2), SysUser(user_id=3)]

        response = list_users(SysUser())

        assert response.total == 2
        assert response.code == 200
        assert response.msg == "查询成功"
        assert len(response.rows or []) == 2

    def test_a_paged_service_result_supplies_the_real_total(
        self, _isolate: _Bundle
    ) -> None:
        """``getDataTable`` 读的是 ``PageList.total``（``new PageInfo(list).getTotal()``）。"""
        from app.common.core.page.page_helper import PageList

        authenticate()
        _isolate.user.list_result = PageList(
            [SysUser(user_id=2)], total=57, page_num=1, page_size=10
        )

        assert list_users(SysUser()).total == 57


class TestListAll:
    def test_the_current_tenant_is_forced(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(tenant_id=100)
        user = SysUser()

        list_all(user)

        assert user.tenant_id == 100

    def test_the_user_type_is_not_forced(
        self, _isolate: _Bundle
    ) -> None:
        """``listAll`` 要"本单位全部用户"，所以三种 userType 都留着。"""
        authenticate(tenant_id=100)
        user = SysUser(user_type="2")

        list_all(user)

        assert user.user_type == "2"


class TestListTenantIdAll:
    def test_a_missing_tenant_falls_back_to_minus_one(
        self, _isolate: _Bundle
    ) -> None:
        """``-1`` 查不到任何数据 —— 与"查全部"相反，别把它改成 null。"""
        authenticate()
        user = SysUser()

        list_tenant_id_all(user)

        assert user.tenant_id == -1

    def test_an_explicit_tenant_is_kept(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        user = SysUser(tenant_id=7)

        list_tenant_id_all(user)

        assert user.tenant_id == 7


class TestListUtil:
    def test_my_dept_sets_status_type_and_tenant(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(tenant_id=100, dept_id=105)
        user = SysUser(flag="myDept")

        list_util(user)

        assert (user.status, user.user_type, user.tenant_id) == ("0", "1", 100)

    def test_my_dept_cg_behaves_like_my_dept(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(tenant_id=100)
        user = SysUser(flag="myDeptCg")

        list_util(user)

        assert (user.status, user.user_type, user.tenant_id) == ("0", "1", 100)

    def test_sjzb_dept_sets_the_data_id_without_other_filters(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(tenant_id=100)
        user = SysUser(flag="sjzbDept")

        list_util(user)

        assert user.data_id == "100"
        assert user.status is None
        assert user.user_type is None

    def test_sjzb_dept_cg_also_uses_the_data_id(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(tenant_id=100)
        user = SysUser(flag="sjzbDeptCg")

        list_util(user)

        assert user.data_id == "100"

    def test_a_null_tenant_becomes_the_literal_string_null(
        self, _isolate: _Bundle
    ) -> None:
        """Java: ``tenantId + ""`` -> ``"null"``，不是空串。"""
        authenticate(tenant_id=None)
        user = SysUser(flag="sjzbDept")

        list_util(user)

        assert user.data_id == "null"

    def test_all_dept_adds_nothing(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(tenant_id=100)
        user = SysUser(flag="allDept")

        list_util(user)

        assert (user.status, user.user_type, user.tenant_id, user.user_id) == (
            None,
            None,
            None,
            None,
        )

    def test_an_unknown_flag_queries_nobody(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        user = SysUser()

        list_util(user)

        assert user.user_id == UNKNOWN_FLAG_USER_ID
        assert UNKNOWN_FLAG_USER_ID == -1

    def test_the_flag_is_trimmed_before_comparison(
        self, _isolate: _Bundle
    ) -> None:
        """Java: ``CommonUtil.isNull(flag)`` -> ``String.valueOf(x).trim()``."""
        authenticate(tenant_id=100)
        user = SysUser(flag="  myDept  ")

        list_util(user)

        assert user.tenant_id == 100
        assert user.user_id is None


class TestListSameUtil:
    def test_the_department_is_forced_to_the_current_one(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(tenant_id=100, dept_id=105)
        user = SysUser(dept_id=999)

        list_same_util(user)

        assert (user.status, user.user_type, user.tenant_id, user.dept_id) == (
            "0",
            "1",
            100,
            105,
        )


class TestListMy:
    def test_only_the_current_user_is_queried(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=7)
        user = SysUser(user_id=999)

        list_my(user)

        assert user.user_id == 7


class TestListByDept:
    def test_the_department_and_user_type_are_forced(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(dept_id=105)
        user = SysUser()

        list_by_dept(user)

        assert (user.dept_id, user.user_type) == (105, "1")

    def test_exclude_self_sets_the_exclude_id(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=7, dept_id=105)
        user = SysUser(exclude_self=True)

        list_by_dept(user)

        assert user.exclude_id == 7

    def test_exclude_self_false_leaves_it_unset(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=7, dept_id=105)
        user = SysUser(exclude_self=False)

        list_by_dept(user)

        assert user.exclude_id is None

    def test_the_department_name_is_copied_onto_the_flat_field(
        self, _isolate: _Bundle
    ) -> None:
        """前端两种取法（``dept.deptName`` / ``deptName``）都要能读到。"""
        authenticate(dept_id=105)
        _isolate.user.list_result = [
            SysUser(user_id=2, dept=SysDept(dept_id=105, dept_name="研发部门")),
            SysUser(user_id=3, dept=SysDept(dept_id=105, dept_name="")),
        ]

        response = list_by_dept(SysUser())

        rows = response.rows or []
        assert rows[0].dept_name == "研发部门"
        # ``isNotBlank`` 判空，空串不覆盖
        assert rows[1].dept_name is None

    def test_a_user_without_a_department_does_not_break_the_copy(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(dept_id=105)
        _isolate.user.list_result = [SysUser(user_id=2)]

        response = list_by_dept(SysUser())

        assert (response.rows or [])[0].dept_name is None


class TestGetroleUser:
    def test_the_role_code_and_tenant_become_the_query(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(tenant_id=100)

        result = getrole_user("cgjl_manager")

        assert result["code"] == 200
        queried = _isolate.user.of("select_user_list")[0][1]
        assert (queried.role_code, queried.tenant_id) == ("cgjl_manager", 100)

    def test_the_list_is_returned_whole_not_as_a_table(
        self, _isolate: _Bundle
    ) -> None:
        """没有 ``startPage()``，返回 ``AjaxResult.success(list)`` 而不是分页信封。"""
        authenticate(tenant_id=100)
        _isolate.user.list_result = [SysUser(user_id=2), SysUser(user_id=3)]

        result = getrole_user("cgjl_manager")

        assert set(result) == {"code", "msg", "data"}
        assert len(result["data"]) == 2


class TestCurrentUser:
    def test_the_service_result_is_returned_under_data(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.current_user = SysUser(user_id=2, head_office=True)

        result = select_current_user()

        assert result["code"] == 200
        assert result["data"].head_office is True


# --------------------------------------------------------------------------- 详情端点


class TestGetInfo:
    def test_without_an_id_only_the_dropdowns_are_returned(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.role.roles = [SysRole(role_id=2, role_name="普通角色")]
        _isolate.post.posts = [SysPost(post_id=1, post_name="ceo")]

        result = get_info()

        assert set(result) == {"code", "msg", "roles", "posts"}
        assert _isolate.user.calls == []

    def test_an_admin_target_sees_every_role(
        self, _isolate: _Bundle
    ) -> None:
        """判据是**被查看的人**（``SysUser.isAdmin(userId)``），不是当前登录用户。"""
        authenticate(user_id=2)
        _isolate.role.roles = [SysRole(role_id=1, role_name="超级管理员"), SysRole(role_id=2)]

        result = get_info_by_id(1)

        assert [role.role_id for role in result["roles"]] == [1, 2]

    def test_a_normal_target_does_not_see_the_admin_role(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=1, user_name="admin")
        _isolate.role.roles = [SysRole(role_id=1, role_name="超级管理员"), SysRole(role_id=2)]

        result = get_info_by_id(2)

        assert [role.role_id for role in result["roles"]] == [2]

    def test_the_detail_also_returns_the_user_and_both_id_lists(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.user_by_id = SysUser(user_id=2, user_name="ry")
        _isolate.post.post_ids = [1, 2]
        _isolate.role.role_ids = [3]

        result = get_info_by_id(2)

        assert result["data"].user_name == "ry"
        assert result["postIds"] == [1, 2]
        assert result["roleIds"] == [3]

    def test_a_missing_user_returns_data_null_with_the_dropdowns(
        self, _isolate: _Bundle
    ) -> None:
        """``AjaxResult.put(DATA_TAG, null)`` 是 HashMap.put —— 键在、值是 null。"""
        authenticate()
        _isolate.user.user_by_id = None

        result = get_info_by_id(999)

        assert "data" in result
        assert result["data"] is None
        assert "roles" in result and "posts" in result

    def test_the_permission_is_checked_before_anything_else(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(permissions={"system:user:add"})

        with pytest.raises(AccessDeniedException):
            get_info_by_id(2)

        assert _isolate.user.calls == []

    def test_the_admin_role_filter_is_by_id_not_by_key(
        self, _isolate: _Bundle
    ) -> None:
        """``SysRole.isAdmin()`` 是 ``roleId == 1``；角色 key 叫什么都不影响。"""
        authenticate()
        _isolate.role.roles = [SysRole(role_id=1, role_key="not_admin")]

        assert get_info_by_id(2)["roles"] == []


# --------------------------------------------------------------------------- 新增 / 修改


class TestAdd:
    def test_a_duplicate_user_name_is_reported_first(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.name_unique = "1"

        result = add(SysUser(user_name="ry", password=VALID_PASSWORD))

        assert result["code"] == 500
        assert result["msg"] == ADD_USER_NAME_EXISTS.format("ry")
        assert _isolate.user.of("insert_user") == []

    def test_a_duplicate_phone_is_reported_second(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.phone_unique = "1"

        result = add(SysUser(user_name="ry", phonenumber="158", password=VALID_PASSWORD))

        assert result["msg"] == ADD_PHONE_EXISTS.format("ry")

    def test_a_duplicate_email_is_reported_third(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.email_unique = "1"

        result = add(SysUser(user_name="ry", email="a@b.c", password=VALID_PASSWORD))

        assert result["msg"] == ADD_EMAIL_EXISTS.format("ry")

    def test_a_blank_phone_skips_the_uniqueness_query(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()

        add(SysUser(user_name="ry", phonenumber="", email="", password=VALID_PASSWORD))

        assert _isolate.user.of("check_phone_unique") == []
        assert _isolate.user.of("check_email_unique") == []

    def test_a_weak_password_is_rejected_after_the_uniqueness_queries(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()

        result = add(SysUser(user_name="ry", password="abc"))

        assert result == {"code": 500, "msg": PASSWORD_INVALID_MESSAGE}
        assert _isolate.user.of("insert_user") == []

    def test_the_creator_and_the_hash_are_stamped(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_name="admin")
        user = SysUser(user_name="ry", password=VALID_PASSWORD)

        result = add(user)

        assert result["code"] == 200
        inserted = _isolate.user.of("insert_user")[0][1]
        assert inserted.create_by == "admin"
        assert inserted.password != VALID_PASSWORD
        assert inserted.password.startswith("$2")

    def test_a_zero_rowcount_is_an_error_envelope(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.insert_result = 0

        assert add(SysUser(user_name="ry", password=VALID_PASSWORD))["code"] == 500


class TestEdit:
    def test_the_admin_guard_runs_first(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.allowed_error = CustomException("不允许操作超级管理员用户")

        with pytest.raises(CustomException):
            edit(SysUser(user_id=1, password=""))

        assert _isolate.user.of("update_user") == []

    def test_a_duplicate_phone_blocks_the_update(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.phone_unique = "1"

        result = edit(SysUser(user_id=2, user_name="ry", phonenumber="158"))

        assert result["msg"] == EDIT_PHONE_EXISTS.format("ry")
        assert _isolate.user.of("update_user") == []

    def test_a_duplicate_email_blocks_the_update(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.email_unique = "1"

        result = edit(SysUser(user_id=2, user_name="ry", email="a@b.c"))

        assert result["msg"] == EDIT_EMAIL_EXISTS.format("ry")

    def test_the_updater_is_stamped_and_the_password_is_not_touched(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_name="admin")
        user = SysUser(user_id=2, nick_name="新昵称")

        result = edit(user)

        assert result["code"] == 200
        updated = _isolate.user.of("update_user")[0][1]
        assert updated.update_by == "admin"
        assert updated.password is None


class TestRemove:
    def test_the_path_variable_is_split_into_ids(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()

        result = remove("2,3,4")

        assert result["code"] == 200
        assert _isolate.user.of("delete_user_by_ids")[0][1] == [2, 3, 4]

    def test_a_single_id_is_fine(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()

        remove("2")

        assert _isolate.user.of("delete_user_by_ids")[0][1] == [2]

    def test_a_non_numeric_id_raises_like_spring_binding(
        self, _isolate: _Bundle
    ) -> None:
        """Java: ``NumberFormatException`` -> 500. Python: ``ValueError`` -> 500."""
        authenticate()

        with pytest.raises(ValueError):
            remove("abc")

    def test_a_zero_rowcount_is_an_error_envelope(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.delete_result = 0

        assert remove("2")["code"] == 500


class TestResetPwd:
    def test_a_weak_password_is_rejected_before_the_admin_guard(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()

        result = reset_pwd(SysUser(user_id=1, password="abc"))

        assert result == {"code": 500, "msg": PASSWORD_INVALID_MESSAGE}
        assert _isolate.user.calls == []

    def test_the_new_password_is_hashed(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_name="admin")

        result = reset_pwd(SysUser(user_id=2, password=VALID_PASSWORD))

        assert result["code"] == 200
        reset = _isolate.user.of("reset_pwd")[0][1]
        assert reset.password.startswith("$2")
        assert reset.update_by == "admin"

    def test_the_admin_guard_runs_after_the_password_check(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.allowed_error = CustomException("不允许操作超级管理员用户")

        with pytest.raises(CustomException):
            reset_pwd(SysUser(user_id=1, password=VALID_PASSWORD))


class TestChangeStatus:
    def test_the_updater_is_stamped_and_status_is_forwarded(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_name="admin")

        result = change_status(SysUser(user_id=2, status="1"))

        assert result["code"] == 200
        updated = _isolate.user.of("update_user_status")[0][1]
        assert (updated.status, updated.update_by) == ("1", "admin")

    def test_the_admin_guard_runs_first(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.allowed_error = CustomException("不允许操作超级管理员用户")

        with pytest.raises(CustomException):
            change_status(SysUser(user_id=1, status="1"))


class TestBindUky:
    def test_a_missing_cert_entity_id_is_rejected(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=2)

        result = bind_uky(SysUser(cert_id="SN1"))

        assert result["msg"] == "唯一实体标识不能为空"
        assert _isolate.user.of("update_user_status") == []

    def test_a_missing_cert_id_is_rejected(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=2)

        result = bind_uky(SysUser(cert_entity_id="CERT1"))

        assert result["msg"] == "密码卡/USD-Key序列号不能为空"

    def test_a_cert_entity_id_owned_by_someone_else_is_rejected(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=2)
        _isolate.user.list_result = [SysUser(user_id=9)]

        result = bind_uky(SysUser(cert_entity_id="CERT1", cert_id="SN1"))

        assert result["msg"] == "唯一实体标识已绑定，请确认！"
        assert _isolate.user.of("update_user_status") == []

    def test_a_cert_id_owned_by_someone_else_is_rejected(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=2)
        # 第一次查 cert_entity_id 查不到，第二次查 cert_id 命中别人
        _isolate.user.list_results = [[], [SysUser(user_id=9)]]

        result = bind_uky(SysUser(cert_entity_id="CERT1", cert_id="SN1"))

        assert result["msg"] == "密码卡/USD-Key序列号已绑定，请确认！"

    def test_rebinding_your_own_certificate_is_allowed(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=2, user_name="admin")
        _isolate.user.list_result = [SysUser(user_id=2)]

        result = bind_uky(SysUser(cert_entity_id="CERT1", cert_id="SN1"))

        assert result["code"] == 200
        updated = _isolate.user.of("update_user_status")[0][1]
        assert (updated.user_id, updated.cert_entity_id, updated.cert_id) == (
            2,
            "CERT1",
            "SN1",
        )

    def test_without_a_user_id_the_current_user_is_bound(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_id=7, user_name="admin")
        _isolate.user.list_result = []

        bind_uky(SysUser(cert_entity_id="CERT1", cert_id="SN1"))

        updated = _isolate.user.of("update_user_status")[0][1]
        assert updated.user_id == 7

    def test_the_two_queries_have_no_pagination(
        self, _isolate: _Bundle
    ) -> None:
        """``bindUky`` 没有 ``startPage()``，取全量。"""
        authenticate(user_id=2)
        _isolate.user.list_result = []

        bind_uky(SysUser(cert_entity_id="CERT1", cert_id="SN1"))

        queried = [call[1] for call in _isolate.user.of("select_user_list")]
        assert [q.cert_entity_id for q in queried] == ["CERT1", None]
        assert [q.cert_id for q in queried] == [None, "SN1"]


# --------------------------------------------------------------------------- 参数绑定


class TestQueryBinding:
    """``SysUser user`` 形参由 Spring 的 query-string 绑定完成；这里只验证接上了。"""

    def test_the_binding_honours_the_java_property_names(self) -> None:
        from app.common.core.controller.base_controller import bind_query_params

        class _Query:
            def multi_items(self) -> List[tuple]:
                return [
                    ("userName", "ry"),
                    ("status", "0"),
                    ("excludeSelf", "true"),
                    ("params[beginTime]", "2024-01-01"),
                    ("unknown", "x"),
                ]

        user = bind_query_params(SysUser, _Query())

        assert user.user_name == "ry"
        assert user.status == "0"
        assert user.exclude_self is True
        assert user.params == {"beginTime": "2024-01-01"}

    def test_an_empty_numeric_parameter_becomes_none(self) -> None:
        """Spring 的 ``StringToNumberConverterFactory`` 对空串返回 null。"""
        from app.common.core.controller.base_controller import bind_query_params

        user = bind_query_params(SysUser, {"userId": "", "deptId": "105"})

        assert user.user_id is None
        assert user.dept_id == 105


# --------------------------------------------------------------------------- HTTP 装配


class TestRoutesOverHttp:
    """路由确实注册在 ``/system/user`` 下，并且和 Java 一样要求登录。

    这些用例不需要数据库：``SecurityMiddleware`` 的规则表在路由之前就拒绝了无 token 的请求。
    """

    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("get", "/system/user/list"),
            ("get", "/system/user/listAll"),
            ("get", "/system/user/listutil"),
            ("get", "/system/user/listMy"),
            ("get", "/system/user/list/dept"),
            ("get", "/system/user/currentUser"),
            ("get", "/system/user/getroleUser/cgjl_manager"),
            ("get", "/system/user/2"),
            ("post", "/system/user"),
            ("put", "/system/user"),
            ("put", "/system/user/resetPwd"),
            ("put", "/system/user/changeStatus"),
            ("put", "/system/user/bindUky"),
            ("delete", "/system/user/2"),
        ],
    )
    def test_every_endpoint_requires_a_token(
        self, client: Any, method: str, path: str
    ) -> None:
        response = getattr(client, method)(path)

        assert response.status_code == 200
        assert response.json()["code"] == 401

    def test_the_literal_paths_are_registered_before_the_id_template(
        self, client: Any
    ) -> None:
        """``GET /system/user/list`` 不能被当成 ``userId = "list"``。"""
        paths = [getattr(route, "path", "") for route in client.app.routes]
        assert "/system/user/list" in paths
        assert "/system/user/{user_id}" in paths
        assert paths.index("/system/user/list") < paths.index("/system/user/{user_id}")

    def test_both_trailing_slash_forms_exist(self, client: Any) -> None:
        """Java: ``@GetMapping({"/", "/{userId}"})``；FastAPI 需要显式两条路由。"""
        paths = [getattr(route, "path", "") for route in client.app.routes]
        assert "/system/user" in paths
        assert "/system/user/" in paths

    def test_the_three_excel_endpoints_are_registered(self, client: Any) -> None:
        """Phase 3.18 补齐：三个 Excel 端点现在都有路由，且都在 ``/{user_id}`` 之前。

        ``/export`` 与 ``/importTemplate`` 是单段字面量，排在 ``/{user_id}`` 后面
        就会被当成 ``userId = "export"`` 而转 int 失败；``/importData`` 是 POST，
        同理不能被 POST ``""`` 掩住（不是同一个路径，但位置仍然统一）。
        """
        paths = [getattr(route, "path", "") for route in client.app.routes]

        assert "/system/user/export" in paths
        assert "/system/user/importTemplate" in paths
        assert "/system/user/importData" in paths
        for path in ("/system/user/export", "/system/user/importTemplate"):
            assert paths.index(path) < paths.index("/system/user/{user_id}")


# --------------------------------------------------------------------------- Excel 端点


def _xlsx(headers: List[str], rows: List[List[Any]]) -> UploadFile:
    """造一个能被 ``ExcelUtil.importExcel`` 读回去的 xlsx 上传件."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "用户数据"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return UploadFile(file=buffer, filename="users.xlsx")


def _request(query: str = "") -> Request:
    """只要 ``query_params`` 能用的最小 ``Request``."""
    return Request({"type": "http", "method": "POST", "query_string": query.encode(), "headers": []})


class TestExcelEndpoints:
    """``export`` / ``importTemplate`` / ``importData`` —— Phase 3.18 补上的三个端点.

    三个都返回 **``AjaxResult``**，不是文件流；客户端要再走
    ``GET /common/download?fileName=...`` 才能拿到内容。文件名落在 ``msg`` 里，
    因为 Java 的 ``AjaxResult.success(String)`` 命中的是 ``success(String msg)`` 重载。
    """

    def test_export_returns_the_filename_and_calls_the_list_service(
        self, _isolate: _Bundle, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        monkeypatch.setenv("RUOYI__PROFILE", str(tmp_path / "uploadPath"))
        reset_settings_cache()
        try:
            authenticate()
            _isolate.user.list_result = [SysUser(user_id=2, user_name="ry")]

            result = export(SysUser())
        finally:
            reset_settings_cache()

        assert result["code"] == 200
        assert "data" not in result
        assert result["msg"].endswith("_用户数据.xlsx")
        # 不分页 + 没有 ``startPage()``
        assert [call[0] for call in _isolate.user.calls] == ["select_user_list"]

    def test_import_template_has_the_18_import_columns(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        monkeypatch.setenv("RUOYI__PROFILE", str(tmp_path / "uploadPath"))
        reset_settings_cache()
        try:
            authenticate()

            result = import_template()
        finally:
            reset_settings_cache()

        assert "data" not in result
        assert result["msg"].endswith("_用户数据.xlsx")
        path = tmp_path / "uploadPath" / "download" / result["msg"]
        headers = tuple(cell.value for cell in load_workbook(path).worksheets[0][1])
        assert len(headers) == 18
        # ``deptId`` 只导入，所以出现在模板里；三列导出专用字段不出现
        assert "部门编号" in headers
        assert "最后登录IP" not in headers
        assert "部门负责人" not in headers

    def test_import_template_has_no_pre_authorize(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """Java 的 ``importTemplate`` 没有 ``@PreAuthorize`` —— 登录即可下载."""
        monkeypatch.setenv("RUOYI__PROFILE", str(tmp_path / "uploadPath"))
        reset_settings_cache()
        try:
            authenticate(permissions=set())

            result = import_template()
        finally:
            reset_settings_cache()

        assert result["code"] == 200

    def test_import_data_returns_the_detail_string_in_msg(
        self, _isolate: _Bundle
    ) -> None:
        authenticate()
        _isolate.user.import_result = "恭喜您，数据已全部导入成功！共 1 条，数据如下：<br/>1、账号 new1 导入成功"

        result = import_data(
            _request(),
            _xlsx(["登录名称", "用户名称"], [["new1", "新用户"]]),
        )

        assert result["code"] == 200
        assert "data" not in result
        assert result["msg"].startswith("恭喜您，数据已全部导入成功！共 1 条")

    def test_import_data_passes_the_parsed_entities_and_the_operator(
        self, _isolate: _Bundle
    ) -> None:
        authenticate(user_name="alice")

        import_data(_request(), _xlsx(["登录名称", "用户性别"], [["new1", "女"]]))

        assert _isolate.user.imported is not None
        users, update_support, oper_name = _isolate.user.imported
        assert [user.user_name for user in users] == ["new1"]
        # ``readConverterExp`` 在 ExcelUtil 里就反解了，Service 拿到的是 "1"
        assert users[0].sex == "1"
        assert update_support is False
        assert oper_name == "alice"

    @pytest.mark.parametrize("truthy", ["true", "on", "yes", "1", "TRUE", " 1 "])
    def test_update_support_comes_from_the_query_string(
        self, _isolate: _Bundle, truthy: str
    ) -> None:
        """Spring: 普通请求参数绑定 —— multipart 下查询串与表单字段都覆盖."""
        authenticate()

        import_data(
            _request(f"updateSupport={truthy}"),
            _xlsx(["登录名称"], [["new1"]]),
        )

        assert _isolate.user.imported is not None
        assert _isolate.user.imported[1] is True

    @pytest.mark.parametrize("falsy", ["false", "off", "no", "0"])
    def test_update_support_falsy_literals(self, _isolate: _Bundle, falsy: str) -> None:
        authenticate()

        import_data(
            _request(f"updateSupport={falsy}"),
            _xlsx(["登录名称"], [["new1"]]),
        )

        assert _isolate.user.imported is not None
        assert _isolate.user.imported[1] is False

    def test_the_form_field_wins_over_the_query_string(self, _isolate: _Bundle) -> None:
        authenticate()

        import_data(
            _request("updateSupport=false"),
            _xlsx(["登录名称"], [["new1"]]),
            True,
        )

        assert _isolate.user.imported is not None
        assert _isolate.user.imported[1] is True

    def test_an_unknown_literal_is_a_conversion_error(self, _isolate: _Bundle) -> None:
        """``StringToBooleanConverter`` 认不出来就抛异常（Spring 下是 HTTP 400）."""
        authenticate()

        with pytest.raises(ValueError):
            import_data(
                _request("updateSupport=maybe"),
                _xlsx(["登录名称"], [["new1"]]),
            )

        assert _isolate.user.of("import_user") == []

    def test_a_bad_file_raises_util_exception(self, _isolate: _Bundle) -> None:
        """不是 xlsx -> ``UtilException``（HTTP 200 + code 500），不会进 Service."""
        authenticate()

        with pytest.raises(UtilException):
            import_data(_request(), UploadFile(file=BytesIO(b"nope"), filename="u.xlsx"))

        assert _isolate.user.of("import_user") == []

    def test_the_empty_list_message_comes_from_the_service(self, _isolate: _Bundle) -> None:
        """表头在、数据行全空 -> ``[]`` -> Service 抛“导入用户数据不能为空”。"""
        authenticate()
        _isolate.user.import_result = "导入用户数据不能为空！"

        result = import_data(_request(), _xlsx(["登录名称"], []))

        assert result["msg"] == "导入用户数据不能为空！"
