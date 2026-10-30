"""Spring Security ``AuthenticationManager``.

Not a RuoYi file
----------------
``org.springframework.security.authentication.AuthenticationManager`` is a one-method
interface; ``SysLoginService`` injects it with ``@Resource``::

    @Resource
    private AuthenticationManager authenticationManager;
    ...
    authentication = authenticationManager.authenticate(
            new UsernamePasswordAuthenticationToken(username, password));

Python has no interfaces, so this is a plain base class that raises
``NotImplementedError``; :class:`~app.framework.security.authentication.provider_manager.ProviderManager`
is the only implementation, exactly as in Spring.
"""

from __future__ import annotations

from typing import Any


class AuthenticationManager:
    """Java: ``interface AuthenticationManager``."""

    # Java: Authentication authenticate(Authentication authentication) throws AuthenticationException
    def authenticate(self, authentication: Any) -> Any:
        raise NotImplementedError("AuthenticationManager is an interface")


__all__ = ["AuthenticationManager"]
