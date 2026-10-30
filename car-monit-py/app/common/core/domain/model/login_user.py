# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/model/LoginUser.java
"""登录用户身份权限 / the authenticated principal.

Java models this as a ``UserDetails`` implementation -- the Spring Security contract for
"the currently authenticated principal". Python has no such interface, so the class keeps
only the parts that carry meaning here:

=====================  ==========================================================
Java                   Python
=====================  ==========================================================
``getUsername()``      :attr:`LoginUser.username` (computed from ``user.userName``)
``getPassword()``      ``@JsonIgnore``, so it is a method rather than a field -- see
                       :meth:`LoginUser.get_password`. It *is* needed: the bcrypt
                       comparison in ``DaoAuthenticationProvider`` reads it, and
                       ``@JsonIgnore`` keeps the hash out of the cached JSON.
``getAuthorities()``   always ``null`` in Java; kept as a computed field so the
                       cached JSON shape matches Jackson's output.
``isAccountNonExpired`` Java hard-codes ``true`` for all four ``isXxx`` flags and marks
``isAccountNonLocked``  them ``@JsonIgnore``. They are constants, so they are simply
``isCredentialsNonExpired`` absent here rather than modelled as dead code.
``isEnabled``
=====================  ==========================================================

``loginTime`` / ``expireTime`` are Java ``Long`` (epoch **milliseconds**), not ``Date``.
They stay integers so the 20-minute refresh comparison in ``TokenService`` is exact.
"""

from __future__ import annotations

from typing import Any, Optional, Set

from pydantic import Field, computed_field, field_serializer

from app.common.core.domain.domain_model import DomainModel
from app.common.core.domain.entity.sys_user import SysUser


class LoginUser(DomainModel):
    """Java: ``LoginUser implements UserDetails``."""

    #: 用户唯一标识 -- the UUID embedded in the JWT ``login_user_key`` claim **and** used
    #: as the Redis key suffix. Not the JWT itself.
    token: Optional[str] = None
    #: Redis 中不区分大小写,存储的 sessionId
    session_id: Optional[str] = None
    #: 登录时间（epoch 毫秒）
    login_time: Optional[int] = None
    #: 过期时间（epoch 毫秒）
    expire_time: Optional[int] = None
    #: 登录IP地址
    ipaddr: Optional[str] = None
    #: 登录地点
    login_location: Optional[str] = None
    #: 浏览器类型
    browser: Optional[str] = None
    #: 操作系统
    os: Optional[str] = None
    #: 权限列表 -- Java ``Set<String>``. A Python ``set`` is not JSON-serializable, so it
    #: is emitted as a sorted list: Java's ``HashSet`` iteration order is unspecified, so
    #: no client can depend on a particular order anyway.
    permissions: Optional[Set[str]] = None
    #: 用户信息
    user: Optional[SysUser] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def username(self) -> Optional[str]:
        """Java: ``getUsername()`` -> ``user.getUserName()``."""
        return self.user.user_name if self.user is not None else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def authorities(self) -> None:
        """Java: ``getAuthorities()`` -- hard-coded ``null`` (authorisation is permission-based)."""
        return None

    @field_serializer("permissions")
    def _serialize_permissions(self, value: Optional[Set[str]], _info: Any) -> Optional[list]:
        if value is None:
            return None
        return sorted(value)

    # ---- Java helper accessors -------------------------------------------------
    def get_username(self) -> Optional[str]:
        """Java: ``getUsername()``."""
        return self.username

    def get_password(self) -> Optional[str]:
        """Java: ``@JsonIgnore getPassword()`` -> ``user.getPassword()``.

        This is the *bcrypt hash*, not the submitted password. It is exposed through a plain
        method (never a field) for exactly two reasons:

        * ``DaoAuthenticationProvider.additionalAuthenticationChecks`` calls
          ``passwordEncoder.matches(presented, userDetails.getPassword())`` -- without this
          accessor the provider has nothing to compare against;
        * ``@JsonIgnore`` means Jackson never serialises it, so it must not become a field
          here either, or it would be written into ``login_tokens:<uuid>`` in Redis.
        """
        return self.user.password if self.user is not None else None

    def get_user_id(self) -> Optional[int]:
        """Convenience mirror of ``getUser().getUserId()``, used all over the Java code."""
        return self.user.user_id if self.user is not None else None

    def get_dept_id(self) -> Optional[int]:
        """Convenience mirror of ``getUser().getDeptId()``."""
        return self.user.dept_id if self.user is not None else None

    def is_admin(self) -> bool:
        """Java: ``getUser().isAdmin()``."""
        return self.user is not None and self.user.admin


__all__ = ["LoginUser"]
