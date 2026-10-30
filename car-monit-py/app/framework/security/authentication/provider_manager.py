"""Spring Security ``ProviderManager``.

Not a RuoYi file
----------------
``org.springframework.security.authentication.ProviderManager`` is the default
``AuthenticationManager`` implementation. RuoYi never names the class explicitly; it appears
only as this ``@Bean`` in ``SecurityConfig``::

    @Bean
    @Override
    public AuthenticationManager authenticationManagerBean() throws Exception {
        return super.authenticationManagerBean();
    }

``WebSecurityConfigurerAdapter.authenticationManagerBean()`` returns the
``AuthenticationManager`` that the adapter built in ``configure(AuthenticationManagerBuilder)``,
which -- given RuoYi passes exactly one ``UserDetailsService`` and one ``PasswordEncoder`` --
is a ``ProviderManager`` holding a single ``DaoAuthenticationProvider``.

Sequence of a call
------------------
1. skip every provider whose ``supports(authentication.getClass())`` is false;
2. call ``provider.authenticate(authentication)`` on the first match;
3. return its result after ``eraseCredentials`` (``eraseCredentialsAfterAuthentication``
   defaults to ``true``, so the plaintext password does not survive in the token);
4. no match -> ``ProviderNotFoundException``.

Step 4 is unreachable in this project (the only caller builds a
``UsernamePasswordAuthenticationToken``, which the single provider supports), but the branch
is kept because a missing branch is indistinguishable from an infinite loop when someone
later adds a provider.

Cost of the no-op
-----------------
``ProviderManager`` looks like ceremony around one ``if``. It is kept because
``SysLoginService`` injects the **interface**, and the exception it may throw
(``ProviderNotFoundException``) is part of that contract; collapsing the two classes would
make the Python call graph diverge from the Java one for no gain.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.framework.security.authentication.authentication_manager import AuthenticationManager
from app.framework.security.authentication.dao_authentication_provider import (
    DaoAuthenticationProvider,
)
from app.framework.security.authentication.exceptions import ProviderNotFoundException


class ProviderManager(AuthenticationManager):
    """Java: ``class ProviderManager implements AuthenticationManager``."""

    def __init__(
        self,
        providers: Optional[Sequence[Any]] = None,
        erase_credentials_after_authentication: bool = True,
    ) -> None:
        self._providers: List[Any] = list(providers or [])
        self.erase_credentials_after_authentication = erase_credentials_after_authentication

    @property
    def providers(self) -> List[Any]:
        return self._providers

    # Java: public Authentication authenticate(Authentication authentication)
    def authenticate(self, authentication: Any) -> Any:
        for provider in self._providers:
            if not provider.supports(type(authentication)):
                continue
            result = provider.authenticate(authentication)
            if self.erase_credentials_after_authentication:
                # Java: if (result.getCredentials() != null && result instanceof
                #              AbstractAuthenticationToken) result.eraseCredentials()
                erase = getattr(result, "erase_credentials", None)
                if result.get_credentials() is not None and callable(erase):
                    erase()
            return result
        # Java: throw new ProviderNotFoundException(messages.getMessage(
        #   "ProviderManager.providerNotFound", "No AuthenticationProvider found for {0}"))
        raise ProviderNotFoundException(
            f"No AuthenticationProvider found for {type(authentication).__name__}"
        )


_PROVIDER_MANAGER: Optional[ProviderManager] = None


def get_authentication_manager() -> AuthenticationManager:
    """Java: the ``authenticationManagerBean`` ``@Bean`` -- Spring's default singleton scope.

    The returned manager holds one :class:`DaoAuthenticationProvider` wired to the
    ``userDetailsService`` bean (resolved lazily by the provider itself) and a stateless
    ``BCryptPasswordEncoder``.
    """
    global _PROVIDER_MANAGER
    if _PROVIDER_MANAGER is None:
        _PROVIDER_MANAGER = ProviderManager(providers=[DaoAuthenticationProvider()])
    return _PROVIDER_MANAGER


def reset_authentication_manager() -> None:
    """Test helper: drop the singleton so fakes can be swapped in."""
    global _PROVIDER_MANAGER
    _PROVIDER_MANAGER = None


__all__ = [
    "ProviderManager",
    "get_authentication_manager",
    "reset_authentication_manager",
]
