"""User-related exceptions.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/user/UserException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/user/CaptchaException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/user/CaptchaExpireException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/user/UserPasswordNotMatchException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/user/UserPasswordRetryLimitExceedException.java

Java keeps these in a ``user`` sub-package; the Python layout mirrors it as
``app.common.exception.user``.

Every subclass only supplies an i18n code, so the visible message comes from
``config/i18n/messages.properties`` via :meth:`RuoYiBaseException.resolve_message`:

    CaptchaException                        -> user.jcaptcha.error           验证码错误
    CaptchaExpireException                  -> user.jcaptcha.expire          验证码已失效
    UserPasswordNotMatchException           -> user.password.not.match       用户不存在/密码错误
    UserPasswordRetryLimitExceedException   -> user.password.retry.limit.exceed
                                               密码输入错误{0}次，帐户锁定{1}分钟

Where they surface
------------------
``SysLoginService.login`` lets them escape, so ``GlobalExceptionHandler`` catches them as a
``RuntimeException`` and answers ``{"code": 500, "msg": <resolved message>}`` with HTTP 200.
The 401/403-ish status codes embedded in upstream RuoYi are *not* used here.
"""

from __future__ import annotations

from typing import Any, List, Optional

from app.common.exception.exceptions import RuoYiBaseException


class UserException(RuoYiBaseException):
    """用户信息异常类.

    Java: ``super("user", code, args, null)`` -- module ``"user"``, no default message,
    so the resolved text always comes from the bundle.
    """

    def __init__(self, code: str, args: Optional[List[Any]] = None) -> None:
        super().__init__(default_message=None, module="user", code=code, args=args)


class CaptchaException(UserException):
    """验证码错误异常类."""

    def __init__(self) -> None:
        super().__init__("user.jcaptcha.error", None)


class CaptchaExpireException(UserException):
    """验证码失效异常类."""

    def __init__(self) -> None:
        super().__init__("user.jcaptcha.expire", None)


class UserPasswordNotMatchException(UserException):
    """用户密码不正确或不符合规范异常类."""

    def __init__(self) -> None:
        super().__init__("user.password.not.match", None)


class UserPasswordRetryLimitExceedException(UserException):
    """用户错误最大次数异常类."""

    def __init__(self, retry_limit_count: int, lock_time: int) -> None:
        # Java: new Object[] { retryLimitCount, lockTime }
        super().__init__("user.password.retry.limit.exceed", [retry_limit_count, lock_time])


class UserNotExistsException(UserException):
    """用户不存在异常类 (declared in Java, never thrown by this project's code paths)."""

    def __init__(self) -> None:
        super().__init__("user.not.exists", None)


class BlackListException(UserException):
    """IP 黑名单异常类 (declared in Java, never thrown by this project's code paths)."""

    def __init__(self) -> None:
        super().__init__("login.blocked", None)


__all__ = [
    "UserException",
    "CaptchaException",
    "CaptchaExpireException",
    "UserPasswordNotMatchException",
    "UserPasswordRetryLimitExceedException",
    "UserNotExistsException",
    "BlackListException",
]
