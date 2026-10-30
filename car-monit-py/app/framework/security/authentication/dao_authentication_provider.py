"""Spring Security ``DaoAuthenticationProvider``.

Not a RuoYi file
----------------
``org.springframework.security.authentication.dao.DaoAuthenticationProvider`` plus the
abstract behaviour it inherits from ``AbstractUserDetailsAuthenticationProvider``. It is the
component that turns "username + password" into a ``LoginUser``:

    1. ``retrieveUser``            -> ``UserDetailsService.loadUserByUsername``
    2. ``preAuthenticationChecks`` -> enabled / account-non-locked / non-expired
    3. ``additionalAuthenticationChecks`` -> ``passwordEncoder.matches``
    4. ``createSuccessAuthentication`` -> a new **authenticated** token carrying the principal

Step 1 is where ``UserDetailsServiceImpl`` throws:
``UsernameNotFoundException`` (unknown user) and ``BaseException`` (deleted / disabled
account). The two land in different places, and that asymmetry is what the client sees:

* ``UsernameNotFoundException`` is caught here and rethrown as ``BadCredentialsException``
  (``hideUserNotFoundExceptions`` defaults to ``true``), so ``SysLoginService`` answers
  ``用户不存在/密码错误``.
* a ``BaseException`` is **not** an ``AuthenticationException``, so it is wrapped in
  ``InternalAuthenticationServiceException``; ``SysLoginService``'s ``else`` branch then
  answers ``对不起，您的账号：xxx 已停用``. Wrapping the message (rather than replacing it) is
  what keeps that sentence intact.

Step 2 is a no-op here
----------------------
``preAuthenticationChecks`` throws for a locked / disabled / expired account, but it reads
``UserDetails.isEnabled()`` &c. RuoYi's ``LoginUser`` hard-codes all four flags to ``true``
(``@JsonIgnore public boolean isEnabled() { return true; }``), and ``UserDetailsServiceImpl``
performs the real status checks itself. The checks are therefore unreachable -- implemented
as a documented no-op instead of dead branches, the same choice made for the omitted
``isXxx`` flags in :mod:`app.common.core.domain.model.login_user`.
"""

from __future__ import annotations

from typing import Any, Optional

from app.framework.security.authentication.exceptions import (
    BadCredentialsException,
    InternalAuthenticationServiceException,
    UsernameNotFoundException,
)
from app.framework.security.context.security_context import (
    Authentication,
    UsernamePasswordAuthenticationToken,
)
from app.framework.security.crypto.bcrypt_password_encoder import BCryptPasswordEncoder

#: Spring's message for ``AbstractUserDetailsAuthenticationProvider.badCredentials``. It is
#: never returned to the client (``SysLoginService`` swaps in ``user.password.not.match``),
#: only logged / written to ``sys_logininfor`` by callers that print it.
BAD_CREDENTIALS = "Bad credentials"

#: Java: ``hideUserNotFoundExceptions`` field default of ``AbstractUserDetailsAuthenticationProvider``.
HIDE_USER_NOT_FOUND_EXCEPTIONS = True


class DaoAuthenticationProvider:
    """Java: ``DaoAuthenticationProvider`` (``@Bean`` wired by ``SecurityConfig``)."""

    def __init__(
        self,
        user_details_service: Any = None,
        password_encoder: Optional[BCryptPasswordEncoder] = None,
        hide_user_not_found_exceptions: bool = HIDE_USER_NOT_FOUND_EXCEPTIONS,
    ) -> None:
        self._user_details_service = user_details_service
        # Java: the ``bCryptPasswordEncoder`` @Bean -- ``new BCryptPasswordEncoder()``.
        # Stateless, so one instance is indistinguishable from a per-call instance.
        self._password_encoder = password_encoder or BCryptPasswordEncoder()
        self.hide_user_not_found_exceptions = hide_user_not_found_exceptions

    # Java: private UserDetailsService userDetailsService (resolved lazily, like @Autowired)
    @property
    def user_details_service(self) -> Any:
        if self._user_details_service is None:
            from app.framework.web.service.user_details_service_impl import (
                get_user_details_service,
            )

            self._user_details_service = get_user_details_service()
        return self._user_details_service

    @property
    def password_encoder(self) -> BCryptPasswordEncoder:
        return self._password_encoder

    # Java: public boolean supports(Class<?> authentication)
    def supports(self, authentication_type: type) -> bool:
        """Only ``UsernamePasswordAuthenticationToken`` is handled."""
        return issubclass(authentication_type, UsernamePasswordAuthenticationToken)

    # Java: public Authentication authenticate(Authentication authentication)
    def authenticate(self, authentication: Authentication) -> Authentication:
        username = self._determine_username(authentication)
        try:
            user = self.retrieve_user(username, authentication)
        except UsernameNotFoundException as ex:
            if not self.hide_user_not_found_exceptions:
                raise
            # Java: throw new BadCredentialsException(messages.getMessage(..., "Bad credentials"))
            raise BadCredentialsException(BAD_CREDENTIALS) from ex

        self.pre_authentication_checks(user)
        self.additional_authentication_checks(user, authentication)
        self.post_authentication_checks(user)
        return self.create_success_authentication(user, authentication, user)

    # Java: protected final UserDetails retrieveUser(String, UsernamePasswordAuthenticationToken)
    def retrieve_user(self, username: str, authentication: Authentication) -> Any:
        """Load the principal, translating non-authentication failures.

        Java's ``catch (Exception ex) -> new InternalAuthenticationServiceException(ex.getMessage(), ex)``
        is what carries ``对不起，您的账号：xxx 已停用`` up to ``SysLoginService``.
        """
        try:
            loaded_user = self.user_details_service.load_user_by_username(username)
        except (UsernameNotFoundException, InternalAuthenticationServiceException):
            raise
        except Exception as ex:
            raise InternalAuthenticationServiceException(str(ex), ex) from ex
        if loaded_user is None:
            # Java: throw new InternalAuthenticationServiceException(
            #   "UserDetailsService returned null, which is an interface contract violation")
            raise InternalAuthenticationServiceException(
                "UserDetailsService returned null, which is an interface contract violation"
            )
        return loaded_user

    # Java: protected void preAuthenticationChecks.check(UserDetails user)
    def pre_authentication_checks(self, user: Any) -> None:
        """Documented no-op -- see the module docstring.

        Java would check ``isAccountNonLocked`` / ``isEnabled`` / ``isAccountNonExpired`` /
        ``isCredentialsNonExpired`` here. ``LoginUser`` returns ``true`` for all four, so no
        branch can ever be taken.
        """
        return None

    # Java: protected void additionalAuthenticationChecks(UserDetails, UsernamePasswordAuthenticationToken)
    def additional_authentication_checks(self, user: Any, authentication: Authentication) -> None:
        """Compare the submitted password with the stored hash.

        ``userDetails.getPassword()`` is ``LoginUser.getPassword()``, which delegates to
        ``user.getPassword()`` -- i.e. the *nested* ``SysUser``. ``LoginUser`` itself has no
        ``password`` field (it is ``@JsonIgnore``), so reading ``user.password`` here would
        raise ``AttributeError`` instead of authenticating.
        """
        if authentication.get_credentials() is None:
            # Java: throw new BadCredentialsException(messages.getMessage(
            #   "AbstractUserDetailsAuthenticationProvider.credentialsNotFound", "Credentials cannot be null"))
            raise BadCredentialsException("Credentials cannot be null")
        if not self.password_encoder.matches(authentication.get_credentials(), user.get_password()):
            raise BadCredentialsException(BAD_CREDENTIALS)

    # Java: protected void postAuthenticationChecks.check(UserDetails user)
    def post_authentication_checks(self, user: Any) -> None:
        """Java checks ``isCredentialsNonExpired`` -- again a constant ``true`` in ``LoginUser``."""
        return None

    # Java: protected Authentication createSuccessAuthentication(Object principal, Authentication, UserDetails user)
    def create_success_authentication(
        self, principal: Any, authentication: Authentication, user: Any
    ) -> Authentication:
        """Three-argument constructor -> ``authenticated = true``, even with null authorities."""
        return UsernamePasswordAuthenticationToken(
            principal, authentication.get_credentials(), user.authorities
        )

    # Java: private String determineUsername(Authentication authentication)
    def _determine_username(self, authentication: Authentication) -> str:
        """Java: ``authentication.getPrincipal() == null ? "NONE_PROVIDED" : authentication.getName()``."""
        if authentication.get_principal() is None:
            return "NONE_PROVIDED"
        return authentication.get_name()


__all__ = ["DaoAuthenticationProvider", "BAD_CREDENTIALS", "HIDE_USER_NOT_FOUND_EXCEPTIONS"]
