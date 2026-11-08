"""数据权限切面（P2-8 修正后的行为）."""

from __future__ import annotations


import pytest

from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.framework.aspectj import data_scope_aspect as aspect


def _login_user(user: SysUser) -> LoginUser:
    return LoginUser(user=user)


def test_stale_data_scope_is_cleared_for_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    """管理员不过滤，但客户端/上一次残留的 ``dataScope`` 必须被删掉."""
    admin = SysUser(user_id=1, admin=True, dept_id=10)
    entity = SysUser(params={"dataScope": " AND (1=1)"})
    monkeypatch.setattr(aspect, "_current_login_user", lambda: _login_user(admin))

    aspect.apply_data_scope(entity, "d", "u")

    assert "dataScope" not in entity.params


def test_dept_scope_is_rendered_from_numeric_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    user = SysUser(user_id=2, admin=False, dept_id=100, roles=[SysRole(role_id=5, data_scope="3")])
    entity = SysUser()
    monkeypatch.setattr(aspect, "_current_login_user", lambda: _login_user(user))

    aspect.apply_data_scope(entity, "d", "u")

    assert entity.params["dataScope"] == " AND (d.dept_id = 100 )"


def test_non_numeric_ids_never_reach_sql(monkeypatch: pytest.MonkeyPatch) -> None:
    """即使模型被绕过塞入字符串，``_id`` 也只输出整数或 ``null``."""
    user = SysUser(user_id=2, admin=False, dept_id=100)
    role = SysRole(role_id=1, data_scope="2")
    role.role_id = "1 OR 1=1"  # type: ignore[assignment] - 模拟被绕过的模型
    user.roles = [role]

    rendered = aspect.data_scope_filter(_login_user(user), "d", "u")

    assert "OR 1=1" not in rendered
    assert "role_id = null" in rendered
