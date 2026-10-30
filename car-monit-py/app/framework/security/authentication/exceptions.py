"""Spring Security authentication exceptions.

Not a RuoYi file
----------------
``org.springframework.security.core.AuthenticationException`` and its subclasses. They are
ported because ``SysLoginService`` branches on ``BadCredentialsException``::

    catch (Exception e) {
        if (e instanceof BadCredentialsException) { ... UserPasswordNotMatchException ... }
        else { ... CustomException(e.getMessage()) ... }
    }

Only the five types reachable from this project's login path are modelled. Spring declares
about twenty (``AccountExpiredException``, ``LockedException``, ``DisabledException``,
``CredentialsExpiredException``, ...); they are thrown by
``AbstractUserDetailsAuthenticationProvider.preAuthenticationChecks``, which cannot fire here
because ``LoginUser.isEnabled()`` / ``isAccountNonLocked()`` hard-code ``true``. Modelling
them would be dead code -- see the note in
:mod:`app.framework.security.authentication.dao_authentication_provider`.

All of them are ``RuntimeException`` in Java, i.e. unchecked; Python exceptions are
unchecked by nature, so the hierarchy is mirrored by name only.
"""

from __future__ import annotations

from typing import Optional


class AuthenticationException(RuntimeError):
    """Java: ``abstract class AuthenticationException extends RuntimeException``."""

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message
        super().__init__(message)

    def get_message(self) -> Optional[str]:
        return self.message


class BadCredentialsException(AuthenticationException):
    """Java: ``BadCredentialsException`` -- wrong password *or* unknown user.

    ``hideUserNotFoundExceptions`` (default ``true``) collapses
    ``UsernameNotFoundException`` into this type on purpose: otherwise the response would
    disclose whether an account exists.
    """


class UsernameNotFoundException(AuthenticationException):
    """Java: ``UsernameNotFoundException``.

    Thrown by ``UserDetailsServiceImpl.loadUserByUsername``. It never escapes the
    ``AuthenticationManager`` -- ``DaoAuthenticationProvider`` converts it.
    """


class InternalAuthenticationServiceException(AuthenticationException):
    """Java: ``InternalAuthenticationServiceException`` -- wraps a non-auth failure.

    ``getMessage()`` keeps the wrapped exception's message, which is what surfaces on the
    login response for a disabled or deleted account (``BaseException.getMessage()``).
    """

    def __init__(self, message: Optional[str] = None, cause: Optional[BaseException] = None) -> None:
        self.cause = cause
        super().__init__(message)


class ProviderNotFoundException(AuthenticationException):
    """Java: ``ProviderNotFoundException`` -- no provider accepts the token type."""


__all__ = [
    "AuthenticationException",
    "BadCredentialsException",
    "UsernameNotFoundException",
    "InternalAuthenticationServiceException",
    "ProviderNotFoundException",
]
