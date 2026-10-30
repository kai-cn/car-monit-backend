"""用户验证处理 / the only ``UserDetailsService`` in the project.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/UserDetailsServiceImpl.java

What ``loadUserByUsername`` really decides
-----------------------------------------
It is not merely a lookup: it is the project's **account-state policy**. Three mutually
exclusive branches, and the exception type is what separates them downstream:

===================================  ==========================  ==============================
condition                            Java exception              what the client sees
===================================  ==========================  ==============================
no row for ``user_name``             ``UsernameNotFoundException``  ``用户不存在/密码错误`` (401)
``del_flag == "2"``                  ``BaseException``           ``对不起，您的账号：xxx 已被删除``
``status  == "1"``                   ``BaseException``           ``对不起，您的账号：xxx 已停用``
otherwise                            ``LoginUser``               ``{"code":200,"token":"..."}``
===================================  ==========================  ==============================

The first row is deliberately indistinguishable from a wrong password:
``DaoAuthenticationProvider.hideUserNotFoundExceptions`` rewrites it as
``BadCredentialsException``, and ``SysLoginService`` maps that to ``user.password.not.match``.
Telling "no such user" apart from "wrong password" would let anyone enumerate accounts.

The other two rows *are* distinguishable, on purpose: an administrator who disabled an account
wants the user to read why they cannot log in. ``BaseException`` is not an
``AuthenticationException``, so the provider wraps it -- message and all -- in
``InternalAuthenticationServiceException``; ``SysLoginService``'s ``else`` branch forwards
``getMessage()`` verbatim.

(Java's ``BaseException`` is :class:`~app.common.exception.exceptions.RuoYiBaseException`
here, renamed only to avoid shadowing Python's builtin ``BaseException``.)

Order matters
-------------
``DELETED`` is tested **before** ``DISABLE``. A soft-deleted row usually also carries
``status = "1"``, so reversing the two would make every deleted account report ``已停用``
instead of ``已被删除``. The ``if / else if`` chain is reproduced as written.

What ``createLoginUser`` does *not* pass
----------------------------------------
``new LoginUser(user, permissionService.getMenuPermission(user))`` -- two arguments only.
``SysPermissionService.getRolePermission`` is **not** called here; role keys are resolved
separately by ``GET /getInfo``. ``LoginUser`` has no ``roles`` field at all, so there is
nothing to fill in.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.enums.user_status import UserStatus
from app.common.exception.exceptions import RuoYiBaseException
from app.framework.security.authentication.exceptions import UsernameNotFoundException
from app.framework.web.service.sys_permission_service import (
    SysPermissionService,
    get_permission_service,
)
from app.system.service.sys_user_service import SysUserService, get_user_service

logger = logging.getLogger("app.framework.web.service.user_details")


class UserDetailsServiceImpl:
    """Java: ``@Service UserDetailsServiceImpl implements UserDetailsService``."""

    def __init__(
        self,
        user_service: Optional[SysUserService] = None,
        permission_service: Optional[SysPermissionService] = None,
    ) -> None:
        self._user_service = user_service
        self._permission_service = permission_service

    # Java: @Autowired private ISysUserService userService
    @property
    def user_service(self) -> SysUserService:
        if self._user_service is None:
            self._user_service = get_user_service()
        return self._user_service

    # Java: @Autowired private SysPermissionService permissionService
    @property
    def permission_service(self) -> SysPermissionService:
        if self._permission_service is None:
            self._permission_service = get_permission_service()
        return self._permission_service

    # Java: public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException
    def load_user_by_username(self, username: str) -> Any:
        user = self.user_service.select_user_by_user_name(username)
        # Java: StringUtils.isNull(user) -- field-based null check, not isBlank
        if user is None:
            logger.info("登录用户：%s 不存在.", username)
            # Message is asserted by tests and (indirectly) by every "user not found" login.
            raise UsernameNotFoundException(f"登录用户：{username} 不存在")
        elif UserStatus.DELETED.get_code() == user.del_flag:
            logger.info("登录用户：%s 已被删除.", username)
            raise RuoYiBaseException(f"对不起，您的账号：{username} 已被删除")
        elif UserStatus.DISABLE.get_code() == user.status:
            logger.info("登录用户：%s 已被停用.", username)
            raise RuoYiBaseException(f"对不起，您的账号：{username} 已停用")

        return self.create_login_user(user)

    # Java: public UserDetails createLoginUser(SysUser user)
    def create_login_user(self, user: SysUser) -> LoginUser:
        """Two fields only -- see the module docstring."""
        return LoginUser(user=user, permissions=self.permission_service.get_menu_permission(user))


_SERVICE: Optional[UserDetailsServiceImpl] = None


def get_user_details_service() -> UserDetailsServiceImpl:
    """Java: the ``userDetailsService`` ``@Bean`` -- Spring's default singleton scope."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = UserDetailsServiceImpl()
    return _SERVICE


def reset_user_details_service() -> None:
    """Test helper: drop the singleton so fake services can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "UserDetailsServiceImpl",
    "get_user_details_service",
    "reset_user_details_service",
]
