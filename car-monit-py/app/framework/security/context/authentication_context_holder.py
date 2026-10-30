"""Authentication context used by ``SysPasswordService``.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/security/context/AuthenticationContextHolder.java

Java stores a ``ThreadLocal<Authentication>`` that Spring Security populates so that
``SysPasswordService.validate`` can see the *presented* username/password without extra
parameters. Python uses a ``ContextVar`` for the same reason as
:mod:`app.framework.security.context.security_context`.

Mirrored defect -- this holder is never populated in this project
---------------------------------------------------------------
A project-wide search finds exactly two references to ``AuthenticationContextHolder``:
the class itself and ``SysPasswordService.validate``. Nothing ever calls
``setContext(...)``, and ``SysPasswordService`` is never injected anywhere either, so the
password-retry lockout is dead code in the Java application. The holder is nevertheless
ported verbatim so that ``SysPasswordService`` still type-checks the same way.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

from app.framework.security.context.security_context import Authentication

_CONTEXT: ContextVar[Optional[Authentication]] = ContextVar("authentication_context", default=None)


class AuthenticationContextHolder:
    """Java: ``AuthenticationContextHolder``."""

    # Java: public static Authentication getContext()
    @staticmethod
    def get_context() -> Optional[Authentication]:
        return _CONTEXT.get()

    # Java: public static void setContext(Authentication context)
    @staticmethod
    def set_context(context: Optional[Authentication]) -> None:
        _CONTEXT.set(context)

    # Java: public static void clearContext()
    @staticmethod
    def clear_context() -> None:
        _CONTEXT.set(None)


__all__ = ["AuthenticationContextHolder"]
