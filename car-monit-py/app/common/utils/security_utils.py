"""安全服务工具类 / security helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/SecurityUtils.java

Static utility class in Java; a module of functions here (same convention as
:mod:`app.common.utils.string_utils`).

The one behaviour to internalise
--------------------------------
Nearly every getter is wrapped in ``try { ... } catch (Exception e) { throw new
CustomException(..., HttpStatus.UNAUTHORIZED); }``. Because
``GlobalExceptionHandler`` has no handler for ``CustomException``, the client sees

    HTTP 200  {"code": 500, "msg": "获取用户账户异常"}

and **not** 401 -- the ``HttpStatus.UNAUTHORIZED`` argument is discarded. The ``-1L`` /
``""`` / ``"用户"`` / ``"-1"`` fall-backs inside the ``try`` blocks are therefore
*unreachable*: they are returned only when the authentication exists and its principal is
``null``, which no code path produces. Both layers are reproduced verbatim anyway, since a
future change to the exception handler would make them live.

``get_authentication`` deliberately does not annotate a nullable return: Java returns
whatever ``SecurityContextHolder`` holds, and ``null`` is a valid answer that callers
(``JwtAuthenticationTokenFilter``) test explicitly.

``getUser().getUserId()`` -> ``login_user.user.user_id``
---------------------------------------------------------
The pydantic entities expose fields, not Java-style getters (``SysUser`` has no
``get_user_id()``). Reading an attribute is the direct equivalent of calling the getter,
and a missing/``None`` ``user`` raises ``AttributeError`` where Java would NPE -- both are
swallowed by the surrounding ``except Exception`` and become ``CustomException``.
``LoginUser`` keeps the two conveniences that ``SecurityUtils`` itself needs on the
principal (``get_username()`` / ``get_user_id()``).
"""

from __future__ import annotations

from typing import Collection, Optional, Set

from app.common.constant.constants import ALL_PERMISSION, SUPER_ADMIN
from app.common.constant.http_status import HttpStatus
from app.common.core.domain.model.login_user import LoginUser
from app.common.exception.exceptions import CustomException
from app.common.utils.pattern_match_utils import simple_match
from app.common.utils.string_utils import has_text
from app.framework.security.context.security_context import Authentication, SecurityContextHolder
from app.framework.security.crypto.bcrypt_password_encoder import BCryptPasswordEncoder


def _cast_login_user(principal: object) -> LoginUser:
    """Java: ``(LoginUser) principal``.

    A Spring class-cast failure is a ``ClassCastException``, i.e. a ``RuntimeException``
    that the surrounding ``catch (Exception e)`` turns into ``CustomException``. Raising
    ``TypeError`` gives the same outcome through the same handler.
    """
    if not isinstance(principal, LoginUser):
        raise TypeError(
            f"class org.springframework.security.core.Authentication principal cannot be cast to "
            f"class com.ruoyi.common.core.domain.model.LoginUser ({type(principal).__name__})"
        )
    return principal


# --------------------------------------------------------------------------- 用户标识


def get_username() -> str:
    """获取用户账户.

    Java: ``SecurityUtils.getUsername()`` -> ``getLoginUser().getUsername()``.
    """
    try:
        return get_login_user().get_username()
    except Exception:
        raise CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED) from None


def get_user_id() -> Optional[int]:
    """获取用户 id.

    Java: ``SecurityUtils.getUserId()`` -> ``Long``. ``-1L`` when the principal is null.
    """
    try:
        user_obj = get_authentication().get_principal()
        if user_obj is None:
            return -1
        login_user = _cast_login_user(user_obj)
        return login_user.user.user_id
    except Exception:
        raise CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED) from None


def get_user_real_name() -> str:
    """获取用户真实姓名. Java: ``SecurityUtils.getUserRealName()`` -> ``nickName``."""
    try:
        user_obj = get_authentication().get_principal()
        if user_obj is None:
            return "用户"
        login_user = _cast_login_user(user_obj)
        return login_user.user.nick_name
    except Exception:
        raise CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED) from None


def get_eps_id() -> int:
    """获取用户当前所在部门. Java: ``SecurityUtils.getEpsId()`` -> ``sysUser.deptId``."""
    try:
        user_obj = get_authentication().get_principal()
        if user_obj is None:
            return -1
        login_user = _cast_login_user(user_obj)
        return login_user.user.dept_id
    except Exception:
        raise CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED) from None


def get_eps() -> str:
    """获取用户当前所在部门名称. Java: ``SecurityUtils.getEps()`` -> ``sysUser.epsName``."""
    try:
        user_obj = get_authentication().get_principal()
        if user_obj is None:
            return ""
        login_user = _cast_login_user(user_obj)
        return login_user.user.eps_name
    except Exception:
        raise CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED) from None


def get_tenant_id() -> int:
    """获取用户当前所在租户. Java: ``SecurityUtils.getTenantId()`` -> ``sysUser.tenantId``."""
    try:
        user_obj = get_authentication().get_principal()
        if user_obj is None:
            return -1
        login_user = _cast_login_user(user_obj)
        return login_user.user.tenant_id
    except Exception:
        raise CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED) from None


def get_dept_sub_code() -> str:
    """获取用户当前所在部门编码. Java: ``SecurityUtils.getDeptSubCode()`` -> ``sysUser.subCode``."""
    try:
        user_obj = get_authentication().get_principal()
        if user_obj is None:
            return "-1"
        login_user = _cast_login_user(user_obj)
        return login_user.user.sub_code
    except Exception:
        raise CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED) from None


# --------------------------------------------------------------------------- 上下文


def get_login_user() -> LoginUser:
    """获取用户.

    Java: ``SecurityUtils.getLoginUser()``. Throws ``CustomException("获取用户信息异常")`` --
    note the different message from the other getters.
    """
    try:
        return _cast_login_user(get_authentication().get_principal())
    except Exception:
        raise CustomException("获取用户信息异常", HttpStatus.UNAUTHORIZED) from None


def get_authentication() -> Optional[Authentication]:
    """获取 Authentication (may be ``None``). Java: ``SecurityUtils.getAuthentication()``."""
    return SecurityContextHolder.get_context().get_authentication()


# --------------------------------------------------------------------------- 密码


def encrypt_password(password: Optional[str]) -> str:
    """生成 BCryptPasswordEncoder 密码.

    Java constructs a **new** encoder per call; the object is stateless, so a module-level
    instance is behaviourally identical and avoids re-deriving the BCrypt tables.
    """
    return _PASSWORD_ENCODER.encode(password)


def matches_password(raw_password: Optional[str], encoded_password: Optional[str]) -> bool:
    """判断密码是否相同. Java: ``SecurityUtils.matchesPassword(String, String)``."""
    return _PASSWORD_ENCODER.matches(raw_password, encoded_password)


#: Java: ``new BCryptPasswordEncoder()`` -- strength 10, ``$2a$`` prefix.
_PASSWORD_ENCODER = BCryptPasswordEncoder()


# --------------------------------------------------------------------------- 权限


def is_admin(user_id: Optional[int]) -> bool:
    """是否为管理员. Java: ``SecurityUtils.isAdmin(Long)`` -> ``userId != null && 1L == userId``."""
    return user_id is not None and user_id == 1


def has_permi(permission: str) -> bool:
    """验证用户是否具备某权限. Java: ``SecurityUtils.hasPermi(String)``."""
    return has_permi_of(get_login_user().permissions, permission)


def has_permi_of(authorities: Optional[Collection[str]], permission: str) -> bool:
    """判断权限集合中是否包含某权限.

    Java: ``SecurityUtils.hasPermi(Collection<String>, String)``.

    ``simpleMatch(authority, permission)`` -- the **granted** string is the pattern. So a
    grant of ``system:user:*`` satisfies a check for ``system:user:list``, and the special
    grant ``*:*:*`` satisfies everything.
    """
    # Java streams over the collection directly and would NPE on a null set. So do we
    # (TypeError); the login path always installs a non-null Set, so this is unreachable.
    return any(
        has_text(authority) and (ALL_PERMISSION == authority or simple_match(authority, permission))
        for authority in authorities
    )


def has_role(role: str) -> bool:
    """验证用户是否拥有某个角色. Java: ``SecurityUtils.hasRole(String)``."""
    role_list = get_login_user().user.roles
    # Java: roleList.stream().map(SysRole::getRoleKey).collect(Collectors.toSet())
    roles: Set[str] = {sys_role.role_key for sys_role in role_list}
    return has_role_of(roles, role)


def has_role_of(roles: Optional[Collection[str]], role: str) -> bool:
    """判断角色集合中是否包含某角色. Java: ``SecurityUtils.hasRole(Collection<String>, String)``."""
    return any(
        has_text(candidate) and (SUPER_ADMIN == candidate or simple_match(candidate, role))
        for candidate in roles
    )


__all__ = [
    "get_username",
    "get_user_id",
    "get_user_real_name",
    "get_eps_id",
    "get_eps",
    "get_tenant_id",
    "get_dept_sub_code",
    "get_login_user",
    "get_authentication",
    "encrypt_password",
    "matches_password",
    "is_admin",
    "has_permi",
    "has_permi_of",
    "has_role",
    "has_role_of",
]
