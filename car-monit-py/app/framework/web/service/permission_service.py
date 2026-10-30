"""RuoYi首创 自定义权限实现 / the ``@ss`` bean behind ``@PreAuthorize``.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/PermissionService.java

Java 是怎么做的
---------------
``@Service("ss")`` 注册一个名为 ``ss`` 的 bean，控制器用 SpEL 引用它：

    @PreAuthorize("@ss.hasPermi('system:user:list')")

Spring Security 的 ``MethodSecurityInterceptor`` 在**方法调用之前**求值这个表达式，
结果为 ``false`` 时抛 ``AccessDeniedException``，被 ``GlobalExceptionHandler`` 接住，
回 **HTTP 200** + ``{"code":403,"msg":"没有权限，请联系管理员授权"}``。

Python 是怎么做的
-----------------
没有 SpEL，用装饰器显式表达同一件事::

    @router.get("/list")
    @pre_authorize_permi("system:user:list")
    def list_users(...): ...

装饰器必须写在 ``@router.get`` **下面**（即先被应用），这样 FastAPI 注册的是包装后的
函数；顺序写反了权限校验就不会执行。

``hasPermi`` 用的是**精确匹配**，不是通配匹配
--------------------------------------------
这一点极易搞错：:func:`app.common.utils.security_utils.has_permi` 内部走
``simple_match``（把**已授予**的权限当**模式**），而本类的 ``hasPermissions`` 只有两句
``permissions.contains(...)``：

    permissions.contains(ALL_PERMISSION) || permissions.contains(StringUtils.trim(permission))

两者在 ``*:*:*`` 上一致，在 ``system:user:*`` 这种部分通匹配上**不一致**。本类保持
Java 的精确匹配语义，不要复用 ``has_permi_of``。

登录用户从哪里取
----------------
Java 里每次 ``hasPermi`` 都 ``tokenService.getLoginUser(request)``（一次 Redis 读）。
Python 的 ``JwtAuthenticationTokenFilter`` 已经把 ``LoginUser`` 放进
``SecurityContextHolder``，直接读上下文即可——值相同，只是省掉一次重复读取。
未登录时返回 ``false``（与 Java 一致，虽然受保护的路由走不到这里）。

为什么必须修复 ``__signature__``
--------------------------------
控制器文件都带 ``from __future__ import annotations``，于是 ``add.__annotations__``
里存的是**字符串** ``"SysUser"``。FastAPI 解析字符串注解时用的是
``wrapper.__globals__``——而包装函数定义在**本模块**，命名空间里没有 ``SysUser``，
注解就停在 ``ForwardRef`` 上，FastAPI 把它当成**查询参数**而不是请求体。

后果不是报错而是**静默错误**：``POST /system/user`` 会从 query string 里取 ``user``
（所以 ``{"userName": ...}`` 永远绑定不上，所有字段都是 ``None``）。Java 没有这个坑——
AOP 代理保留目标方法的签名，``@RequestBody`` 照常工作。这里用原函数的类型注解重建
``__signature__``，把同一个性质补回来。
"""

from __future__ import annotations

import functools
import inspect
import logging
import typing
from typing import Any, Callable, Iterable, Optional, TypeVar

from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.model.login_user import LoginUser
from app.common.exception.exceptions import AccessDeniedException
from app.common.utils.string_utils import is_empty, java_trim
from app.framework.security.context.security_context import SecurityContextHolder

logger = logging.getLogger("app.framework.web.service.permission_service")

#: 所有权限标识
ALL_PERMISSION = "*:*:*"

#: 管理员角色权限标识
SUPER_ADMIN = "admin"

ROLE_DELIMETER = ","
PERMISSION_DELIMETER = ","

F = TypeVar("F", bound=Callable[..., Any])


def _current_login_user() -> Optional[LoginUser]:
    """Java: ``tokenService.getLoginUser(ServletUtils.getRequest())`` -- 未登录返回 ``None``."""
    try:
        principal = SecurityContextHolder.get_context().get_authentication().get_principal()
    except Exception:  # noqa: BLE001 - 取不到就当作未登录，与 Java 的 null 判断等价
        return None
    return principal if isinstance(principal, LoginUser) else None


class PermissionService:
    """Java: ``@Service("ss") PermissionService``."""

    # Java: public boolean hasPermi(String permission)
    def has_permi(self, permission: Optional[str]) -> bool:
        """验证用户是否具备某权限."""
        if is_empty(permission):
            return False
        login_user = _current_login_user()
        if login_user is None or not login_user.permissions:
            return False
        return self._has_permissions(login_user.permissions, permission)

    # Java: public boolean lacksPermi(String permission)
    def lacks_permi(self, permission: Optional[str]) -> bool:
        """验证用户是否不具备某权限，与 hasPermi 逻辑相反."""
        return self.has_permi(permission) is not True

    # Java: public boolean hasAnyPermi(String permissions)
    def has_any_permi(self, permissions: Optional[str]) -> bool:
        """验证用户是否具有以下任意一个权限（逗号分隔）."""
        if is_empty(permissions):
            return False
        login_user = _current_login_user()
        if login_user is None or not login_user.permissions:
            return False
        authorities = login_user.permissions
        for permission in permissions.split(PERMISSION_DELIMETER):
            if permission is not None and self._has_permissions(authorities, permission):
                return True
        return False

    # Java: public boolean hasRole(String role)
    def has_role(self, role: Optional[str]) -> bool:
        """判断用户是否拥有某个角色."""
        if is_empty(role):
            return False
        login_user = _current_login_user()
        if login_user is None or login_user.user is None or not login_user.user.roles:
            return False
        # Java: for (SysRole sysRole : loginUser.getUser().getRoles())
        # ``roleKey.equals(...)`` 在 roleKey 为 null 时会 NPE，这里同样不做兜底：
        # ``sys_role.role_key`` 是 NOT NULL 列，取不到是数据问题，不该被静默吞掉。
        for sys_role in login_user.user.roles:
            role_key = sys_role.role_key if isinstance(sys_role, SysRole) else None
            if SUPER_ADMIN == role_key or role_key == java_trim(role):
                return True
        return False

    # Java: public boolean lacksRole(String role)
    def lacks_role(self, role: Optional[str]) -> bool:
        """验证用户是否不具备某角色，与 hasRole 逻辑相反."""
        return self.has_role(role) is not True

    # Java: public boolean hasAnyRoles(String roles)
    def has_any_roles(self, roles: Optional[str]) -> bool:
        """验证用户是否具有以下任意一个角色（逗号分隔）."""
        if is_empty(roles):
            return False
        login_user = _current_login_user()
        if login_user is None or login_user.user is None or not login_user.user.roles:
            return False
        for role in roles.split(ROLE_DELIMETER):
            if self.has_role(role):
                return True
        return False

    # Java: private boolean hasPermissions(Set<String> permissions, String permission)
    @staticmethod
    def _has_permissions(permissions: Iterable[str], permission: str) -> bool:
        """精确包含判断 —— 注意**不是** ``simple_match`` 通配匹配，见模块 docstring."""
        return ALL_PERMISSION in permissions or java_trim(permission) in permissions


_SERVICE: Optional[PermissionService] = None


def get_permission_service() -> PermissionService:
    """Java: 从容器里取 ``@ss`` —— 无状态，单例即可."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = PermissionService()
    return _SERVICE


def reset_permission_service() -> None:
    """Test helper: drop the cached ``@ss`` instance."""
    global _SERVICE
    _SERVICE = None


def _keep_target_signature(wrapper: Callable[..., Any], func: Callable[..., Any]) -> None:
    """让 FastAPI 看到**原函数**的类型注解（见模块 docstring 的最后一节）。

    ``functools.wraps`` 只复制 ``__annotations__``（字符串形态）和 ``__wrapped__``；
    FastAPI 的 ``get_typed_signature`` 走 ``inspect.signature(wrapper)``，它会顺着
    ``__wrapped__`` 拿到原签名，却仍然拿**包装函数**的 ``__globals__`` 去求值字符串注解。
    显式设置 ``wrapper.__signature__`` 是唯一能同时避开这两点的做法，而且不修改原函数。
    """
    try:
        hints = typing.get_type_hints(func, include_extras=True)
        signature = inspect.signature(func)
    except Exception:  # noqa: BLE001 - 注解求值失败时保持现状，不能让导入期崩溃
        return
    parameters = [
        parameter.replace(annotation=hints.get(parameter.name, parameter.annotation))
        for parameter in signature.parameters.values()
    ]
    wrapper.__signature__ = signature.replace(  # type: ignore[attr-defined]
        parameters=parameters,
        return_annotation=hints.get("return", signature.return_annotation),
    )


def pre_authorize_permi(permission: str) -> Callable[[F], F]:
    """``@PreAuthorize("@ss.hasPermi('<permission>')")`` 的装饰器版本.

    校验失败抛 :class:`AccessDeniedException`，由 ``register_exception_handlers`` 里的
    处理器翻译成 **HTTP 200 + code 403**（与 Java 的
    ``GlobalExceptionHandler#handleAccessDeniedException`` 一致）。
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not get_permission_service().has_permi(permission):
                logger.warning("[权限校验失败] permission=%s, function=%s", permission, func.__name__)
                raise AccessDeniedException(f"Access is denied: {permission}")
            return func(*args, **kwargs)

        _keep_target_signature(wrapper, func)
        # 把权限点挂到包装函数上，仅供 ``scripts/audit_endpoints.py`` 之类的审计工具
        # 反查「Java @PreAuthorize 与 Python 装饰器是否指向同一个权限串」。
        # 运行时行为不受影响（Java 侧同样只在注解里声明一次权限串）。
        wrapper.__permi__ = permission  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator


def pre_authorize_roles(*roles: str) -> Callable[[F], F]:
    """``@PreAuthorize("@ss.hasAnyRoles('<roles>')")`` 的装饰器版本."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not get_permission_service().has_any_roles(",".join(roles)):
                logger.warning("[角色校验失败] roles=%s, function=%s", roles, func.__name__)
                raise AccessDeniedException(f"Access is denied: {','.join(roles)}")
            return func(*args, **kwargs)

        _keep_target_signature(wrapper, func)
        wrapper.__roles__ = roles  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = [
    "ALL_PERMISSION",
    "SUPER_ADMIN",
    "ROLE_DELIMETER",
    "PERMISSION_DELIMETER",
    "PermissionService",
    "get_permission_service",
    "reset_permission_service",
    "pre_authorize_permi",
    "pre_authorize_roles",
]
