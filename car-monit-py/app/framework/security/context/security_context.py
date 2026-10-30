"""Authentication context (Spring Security stand-in).

Not a RuoYi file
----------------
``SecurityContextHolder``, ``SecurityContext``, ``UsernamePasswordAuthenticationToken`` and
``AnonymousAuthenticationToken`` belong to **Spring Security**
(``org.springframework.security.*``), not to ``com.ruoyi``. They are ported here because
roughly 200 RuoYi call sites depend on them:

    SecurityContextHolder.getContext().getAuthentication()
    SecurityContextHolder.getContext().setAuthentication(token)

ThreadLocal -> ContextVar
-------------------------
Spring stores the context in a ``ThreadLocal``. A Python ASGI server multiplexes requests
over one thread with ``asyncio``, so a ``ThreadLocal`` would leak the previous request's
identity into the next one. ``contextvars.ContextVar`` is the asyncio-safe equivalent:
Starlette copies the current context into the worker thread it uses for ``def`` endpoints
(``anyio.to_thread.run_sync``), so a value set by middleware is visible inside a sync
endpoint -- but never to a different request.

The stored object is *mutated* (``set_authentication``) rather than re-bound, so the copy
in the worker thread sees the same instance the filter populated.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, List, Optional


class Authentication:
    """Spring: ``interface Authentication``.

    Only the members RuoYi's code touches are modelled: ``principal``, ``credentials``,
    ``authorities``, ``details`` and :meth:`get_name`.
    """

    def __init__(
        self,
        principal: Any = None,
        credentials: Any = None,
        authorities: Optional[List[Any]] = None,
        details: Any = None,
        authenticated: bool = True,
    ) -> None:
        self.principal = principal
        self.credentials = credentials
        self.authorities = authorities
        self.details = details
        self.authenticated = authenticated

    # Java: Authentication#getName()
    def get_name(self) -> str:
        """Identity name.

        Java resolves, in order: ``UserDetails`` -> ``getUsername()``,
        ``AuthenticatedPrincipal`` -> ``getName()``, ``Principal`` -> ``getName()``,
        anything else -> ``toString()``. ``LoginUser`` is the only principal type this
        project installs, so the first branch is the one that matters; the fallbacks are
        kept so anonymous tokens (a ``str`` principal) behave as in Java.
        """
        principal = self.principal
        if principal is None:
            return ""
        # Java: principal instanceof UserDetails
        get_username = getattr(principal, "get_username", None)
        if callable(get_username):
            return get_username()
        return str(principal)

    # Java: Authentication#getPrincipal()
    def get_principal(self) -> Any:
        return self.principal

    # Java: Authentication#getCredentials()
    def get_credentials(self) -> Any:
        return self.credentials

    # Java: Authentication#getAuthorities()
    def get_authorities(self) -> Optional[List[Any]]:
        return self.authorities

    # Java: Authentication#getDetails()
    def get_details(self) -> Any:
        return self.details

    # Java: Authentication#setDetails(Object)
    def set_details(self, details: Any) -> None:
        self.details = details

    # Java: Authentication#isAuthenticated()
    def is_authenticated(self) -> bool:
        return self.authenticated

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"{type(self).__name__}(principal={self.principal!r})"


class _Unset:
    """Sentinel distinguishing "no third argument" from "third argument is null".

    Java resolves the overload at compile time: two arguments means the pre-authentication
    constructor (``authenticated = false``), three arguments means the authenticated one
    (``authenticated = true``) **even when the collection is null**. ``None`` cannot encode
    that difference because ``new UsernamePasswordAuthenticationToken(loginUser, null,
    loginUser.getAuthorities())`` legitimately passes null for the authorities.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<unset>"


#: Default value of the ``authorities`` parameter; never escapes this module.
_UNSET = _Unset()


class UsernamePasswordAuthenticationToken(Authentication):
    """Spring: ``UsernamePasswordAuthenticationToken``.

    Two constructors in Java with different meanings:

    * ``(principal, credentials)``   -> ``authenticated = false`` (pre-authentication)
    * ``(principal, credentials, authorities)`` -> ``authenticated = true``

    ``JwtAuthenticationTokenFilter`` uses the three-argument form, so a request that
    passed through it carries ``authenticated = true``.

    The arity is what decides ``authenticated`` -- not the value of ``authorities``. Passing
    ``None`` explicitly therefore still authenticates, exactly as in Java.
    """

    def __init__(
        self,
        principal: Any = None,
        credentials: Any = None,
        authorities: Any = _UNSET,
    ) -> None:
        three_argument_form = authorities is not _UNSET
        # Java: the 2-arg constructor calls super(principal, credentials) and never sets
        # authenticated = true; the 3-arg one calls super.setAuthenticated(true).
        super().__init__(
            principal=principal,
            credentials=credentials,
            authorities=None if three_argument_form is False else authorities,
            authenticated=three_argument_form,
        )

    def erase_credentials(self) -> None:
        """Java: ``eraseCredentials()`` -- the base class nulls the credentials."""
        self.credentials = None


class AnonymousAuthenticationToken(Authentication):
    """Spring: ``AnonymousAuthenticationToken`` set by ``AnonymousAuthenticationFilter``.

    ``ExceptionTranslationFilter`` inspects the principal type to decide whether a denied
    request should be answered by the ``AuthenticationEntryPoint`` (401 body) or by the
    ``AccessDeniedHandler`` (403). Keeping a distinct class makes that test explicit:

        isinstance(authentication, AnonymousAuthenticationToken)

    Java's key is the literal ``"anonymousUser"``.
    """

    KEY = "anonymousUser"
    #: Spring's ``SimpleGrantedAuthority("ROLE_ANONYMOUS")``
    ROLE_ANONYMOUS = "ROLE_ANONYMOUS"

    def __init__(self, authorities: Optional[List[Any]] = None, details: Any = None) -> None:
        super().__init__(
            principal=self.KEY,
            credentials="",
            authorities=authorities if authorities is not None else [self.ROLE_ANONYMOUS],
            details=details,
            authenticated=True,
        )


class SecurityContext:
    """Spring: ``interface SecurityContext`` -- a single mutable holder for the token."""

    def __init__(self, authentication: Optional[Authentication] = None) -> None:
        self.authentication = authentication

    # Java: SecurityContext#getAuthentication()
    def get_authentication(self) -> Optional[Authentication]:
        return self.authentication

    # Java: SecurityContext#setAuthentication(Authentication)
    def set_authentication(self, authentication: Optional[Authentication]) -> None:
        self.authentication = authentication


#: Per-request storage. ``default=None`` plus lazy creation in :meth:`get_context` keeps
#: each request from sharing a mutable object with any other.
_CONTEXT: ContextVar[Optional[SecurityContext]] = ContextVar("security_context", default=None)


class SecurityContextHolder:
    """Spring: ``SecurityContextHolder`` -- static facade over the per-request context.

    Java mutates the caller's ``SecurityContext`` instance, so the Python port mutates the
    stored instance as well and never re-binds the ``ContextVar`` during a request.
    """

    # Java: SecurityContextHolder.getContext()
    @staticmethod
    def get_context() -> SecurityContext:
        context = _CONTEXT.get()
        if context is None:
            context = SecurityContext()
            _CONTEXT.set(context)
        return context

    # Java: SecurityContextHolder.setContext(SecurityContext)
    @staticmethod
    def set_context(context: SecurityContext) -> None:
        _CONTEXT.set(context)

    # Java: SecurityContextHolder.clearContext()
    @staticmethod
    def clear_context() -> None:
        _CONTEXT.set(None)


__all__ = [
    "Authentication",
    "UsernamePasswordAuthenticationToken",
    "AnonymousAuthenticationToken",
    "SecurityContext",
    "SecurityContextHolder",
]
