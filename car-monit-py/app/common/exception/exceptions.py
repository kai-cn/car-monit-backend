"""Base exception hierarchy.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/BaseException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/ServiceException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/CustomException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/DemoModeException.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/common/core/exception/BusinessException.java

Java -> Python exception mapping
--------------------------------
Java checked/unchecked distinction has no Python counterpart: every Python exception is
"unchecked". The hierarchy is therefore mirrored by *name and payload*, not by checkedness.

    java.lang.RuntimeException
      +-- BaseException          -> RuoYiBaseException   (renamed, see note below)
      +-- ServiceException       -> ServiceException
      |     +-- BusinessException-> BusinessException   (ry-system monitor package)
      +-- CustomException        -> CustomException
      +-- DemoModeException      -> DemoModeException
      +-- UtilException          -> UtilException (raised by ExcelUtil)
      +-- AccessDeniedException  -> AccessDeniedException (raised by @PreAuthorize equivalents)

``AccessDeniedException`` is Spring Security's, not RuoYi's, so it is not part of the
``BaseException``/``ServiceException`` tree above; it is grouped here because it is raised
and handled by the same layer.

Naming note (deliberate deviation)
----------------------------------
Java's ``com.ruoyi.common.exception.BaseException`` is ported as ``RuoYiBaseException``
instead of ``BaseException``. ``BaseException`` is a Python *builtin* root class
(``except BaseException`` catches ``KeyboardInterrupt`` too); re-exporting it under that
name would silently shadow the builtin in every importing module.
"""

from __future__ import annotations

from typing import Any, Optional


class RuoYiBaseException(RuntimeError):
    """基础异常 / base exception carrying module + message code + i18n args.

    Java: ``com.ruoyi.common.exception.BaseException``.
    Renamed to avoid shadowing Python's builtin ``BaseException``.
    """

    # Java: BaseException(String module, String code, Object[] args, String defaultMessage)
    def __init__(
        self,
        default_message: Optional[str] = None,
        module: Optional[str] = None,
        code: Optional[str] = None,
        args: Optional[Any] = None,
    ) -> None:
        # Java: getMessage() resolves code via MessageUtils, falling back to defaultMessage.
        # The i18n resolver lands in Phase 3 (app/common/utils/message_utils.py); until then
        # the resolved message always equals defaultMessage, which is what MessageUtils does
        # when the bundle has no entry.
        self.module: Optional[str] = module
        self.code: Optional[str] = code
        # Java: private Object[] args. **Not** stored as ``self.args``: ``BaseException.args``
        # is a CPython getset that only accepts a tuple, so ``self.args = None`` raises
        # ``TypeError: 'NoneType' object is not iterable``. ``RuoYiBaseException("msg")``
        # passes ``args=None`` and would therefore explode on construction -- exactly the
        # shape used for "账号已停用". Renamed to ``arguments``; ``get_args()`` keeps the
        # Java accessor.
        self.arguments: Optional[Any] = args
        self.default_message: Optional[str] = default_message
        super().__init__(self.resolve_message())

    # Java: public Object[] getArgs()
    def get_args(self) -> Optional[Any]:
        return self.arguments

    def resolve_message(self) -> Optional[str]:
        """Java: ``getMessage()``."""
        if self.code:
            from app.common.utils.message_utils import message  # local import: avoids cycle

            resolved = message(self.code, self.arguments)
            if resolved is not None:
                return resolved
        return self.default_message


class ServiceException(RuntimeError):
    """业务异常 / business rule violation.

    Mirrors ``com.ruoyi.common.exception.ServiceException``:
      * ``code`` is ``Integer`` and nullable -> ``Optional[int]``
      * ``message`` overrides ``getMessage()`` -> stored and exposed through ``str(exc)``
      * ``detailMessage`` is an internal debugging detail, never returned to clients
    """

    # Java: public ServiceException()
    # Java: public ServiceException(String message)
    def __init__(self, message: Optional[str] = None, code: Optional[int] = None) -> None:
        self.code: Optional[int] = code
        self.message: Optional[str] = message
        self.detail_message: Optional[str] = None
        super().__init__(message)

    # Java: public ServiceException(String message, Integer code)
    @classmethod
    def of(cls, message: str, code: Optional[int] = None) -> "ServiceException":
        return cls(message=message, code=code)

    # Java: public ServiceException setMessage(String message)
    def set_message(self, message: str) -> "ServiceException":
        self.message = message
        self.args = (message,)
        return self

    # Java: public ServiceException setDetailMessage(String detailMessage)
    def set_detail_message(self, detail_message: str) -> "ServiceException":
        self.detail_message = detail_message
        return self

    def __str__(self) -> str:
        return self.message or ""


class BusinessException(ServiceException):
    """业务异常 (ruoyi-system ``common.core.exception`` variant)."""


class DemoModeException(RuntimeError):
    """演示模式异常 / demo mode guard.

    Java: ``public class DemoModeException extends RuntimeException`` (no members).
    The handler always answers ``演示模式，不允许操作``.
    """


class UtilException(RuntimeError):
    """工具类异常 / utility-layer failure.

    # Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/UtilException.java

    Java 声明了三个构造器（``()`` / ``(Throwable)`` / ``(String)``），以及
    ``(String, Throwable)``；没有自己的字段，消息一律走 ``RuntimeException``。

    ``GlobalExceptionHandler`` **没有**为它写 ``@ExceptionHandler``，所以落到
    ``@ExceptionHandler(RuntimeException.class)`` -> ``AjaxResult.error(e.getMessage())``，
    即 HTTP 200 + ``code 500``。
    :class:`~app.common.utils.poi.excel_util.ExcelUtil` 就是靠它把
    ``导出Excel失败，请联系网站管理员！`` 抛给前端的。
    """

    # Java: public UtilException(String message)
    # Java: public UtilException(String message, Throwable e)
    def __init__(self, message: Optional[str] = None, cause: Optional[BaseException] = None) -> None:
        self.message: Optional[str] = message
        self.cause: Optional[BaseException] = cause
        super().__init__(message)


class AccessDeniedException(RuntimeError):
    """访问被拒绝 / access denied.

    Mirror of ``org.springframework.security.access.AccessDeniedException``.

    Raised by the ``@PreAuthorize("@ss.hasPermi(...)")`` equivalent
    (:func:`app.framework.web.service.permission_service.pre_authorize_permi`) when the
    current user lacks the required permission string.

    Why it lives here and not in ``exception_handlers``
        ``GlobalExceptionHandler`` handles it, but the *throwers* are controllers; putting the
        class in the handler module would make every controller import the handler layer.
        ``app.config.exception_handlers`` re-exports it, so either import path works.
    """

    # Java: AccessDeniedException(String msg)
    def __init__(self, message: str = "Access is denied") -> None:
        self.message: str = message
        super().__init__(message)


class CustomException(RuntimeError):
    """自定义异常 / ad-hoc exception with an (almost always ignored) status code.

    Java: ``com.ruoyi.common.exception.CustomException``.

    Mirrored quirk -- the ``code`` field never reaches the client
    -----------------------------------------------------------
    ``GlobalExceptionHandler`` has **no** ``@ExceptionHandler(CustomException.class)``,
    so this type falls through to ``@ExceptionHandler(RuntimeException.class)``, which
    answers ``AjaxResult.error(e.getMessage())``. The consequence is that
    ``new CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED)`` -- thrown all over
    ``SecurityUtils`` -- produces ``{"code": 500, "msg": "获取用户账户异常"}`` with HTTP 200,
    *not* code 401. Reproduced deliberately; the ``code`` attribute is retained only so the
    call sites read the same as Java.

    Java: ``getMessage()`` is overridden to return the stored message, which is what
    ``RuntimeError.__init__(message)`` already does.
    """

    # Java: public CustomException(String message)
    # Java: public CustomException(String message, Integer code)
    # Java: public CustomException(String message, Throwable e)
    def __init__(self, message: str, code: Optional[int] = None, cause: Optional[BaseException] = None) -> None:
        self.message: str = message
        self.code: Optional[int] = code
        self.cause: Optional[BaseException] = cause
        super().__init__(message)

    # Java: public String getMessage()
    def get_message(self) -> str:
        """Java: ``getMessage()``."""
        return self.message
