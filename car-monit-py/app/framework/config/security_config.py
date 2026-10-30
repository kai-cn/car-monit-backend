"""spring security配置 / the authorization rule table.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/SecurityConfig.java

Java original
-------------
``SecurityConfig extends WebSecurityConfigurerAdapter`` builds a filter chain:

    CorsFilter -> LogoutFilter -> JwtAuthenticationTokenFilter -> ... -> AnonymousAuthenticationFilter
               -> ExceptionTranslationFilter -> FilterSecurityInterceptor

and a **rule table** consumed by the last of them::

    .antMatchers("/login", "/captchaImage").permitAll()
    .antMatchers(HttpMethod.GET, "/", "/*.html", ...).permitAll()
    .antMatchers("/swagger-ui.html", ...).denyAll()
    .antMatchers("/common/download**").anonymous()
    ...
    .anyRequest().authenticated()

Because a Spring ``WebSecurityConfigurerAdapter`` is a builder with no Python analogue, the
chain is split across four modules and this one owns only the table:

===========================================  =============================================
Java                                          Python
===========================================  =============================================
``SecurityConfig#configure(HttpSecurity)``     this module (``AUTHORIZATION_RULES``)
``JwtAuthenticationTokenFilter``               ``app.framework.security.filter...``
``AuthenticationEntryPointImpl``                ``...handle.authentication_entry_point_impl``
``LogoutSuccessHandlerImpl``                   ``...handle.logout_success_handler_impl``
the whole chain, wired in order                ``app.middleware.security.SecurityMiddleware``
===========================================  =============================================

Matching semantics -- copied from ``ExpressionBasedFilterInvocationSecurityMetadataSource``
-------------------------------------------------------------------------------------------
* Rules are evaluated **in declaration order** and the **first match wins**; ``anyRequest()``
  is the catch-all at the end.
* A path is matched with Spring's ``AntPathMatcher`` (:func:`app.common.utils.string_utils.is_match`),
  against the path *inside* the servlet context (``context-path: /`` here, so identical).
* ``antMatchers(HttpMethod.GET, ...)`` matches the method by exact string equality -- a
  ``HEAD`` request does **not** match a ``GET`` rule (``HttpMethod.matches`` compares names),
  and a trailing slash is significant: ``/login`` does not match ``/login/``.
* ``anyRequest()`` covers every verb, so ``POST /`` is *not* permitAll -- only ``GET /`` is.

What the four access modes mean -- the subtle part
--------------------------------------------------
The modes are evaluated **after** ``AnonymousAuthenticationFilter``, which installs an
``AnonymousAuthenticationToken`` when no authentication exists. So "anonymous" is a real
authentication, not the absence of one:

===========  =========================  ============================
mode          anonymous caller            authenticated caller
===========  =========================  ============================
permitAll     allowed                     allowed
authenticated **401** (entry point)        allowed
anonymous     allowed                     **403** (AccessDeniedHandler)
denyAll       **401** (entry point)        **403** (AccessDeniedHandler)
===========  =========================  ============================

Two consequences worth stating explicitly, because both look like bugs and both are
RuoYi behaviour:

* ``/system/file/view/**`` and ``/system/notice/view/**`` are declared ``anonymous()``. A
  browser fetching an ``<img src>`` sends no ``Authorization`` header and therefore passes;
  the same URL fetched with a valid token returns **403**. That is what the Java build does.
* ``denyAll`` answers 401 to anonymous callers rather than 403, because
  ``ExceptionTranslationFilter`` treats "anonymous" as "not logged in yet" and starts
  authentication instead of reporting a denial.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from app.common.utils.string_utils import is_match


class AccessMode(str, Enum):
    """The subset of Spring's ``access(...)`` expressions this project uses.

    ``str`` mixin so a mode can be logged or compared against its Java spelling directly.
    """

    #: ``permitAll()`` -- ``PermitAllExpression``: always true, even for anonymous callers.
    PERMIT_ALL = "permitAll"
    #: ``anonymous()`` -- ``AnonymousExpression``: true **only** for ``AnonymousAuthenticationToken``.
    ANONYMOUS = "anonymous"
    #: ``authenticated()`` -- ``AuthenticatedExpression``: authenticated and not anonymous.
    AUTHENTICATED = "authenticated"
    #: ``denyAll()`` -- ``DenyAllExpression``: never true.
    DENY_ALL = "denyAll"


@dataclass(frozen=True)
class UrlRule:
    """One ``antMatchers(...)`` entry.

    Java: ``registry.antMatchers(pattern).access(mode)``. ``http_method`` is ``None`` for the
    ``antMatchers(String...)`` overload (any verb) and ``"GET"`` for
    ``antMatchers(HttpMethod.GET, ...)``.
    """

    pattern: str
    access: AccessMode
    http_method: Optional[str] = None


#: Java: ``httpSecurity.logout().logoutUrl("/logout")``.
#:
#: Which verbs match is decided by ``LogoutConfigurer#createLogoutRequestMatcher``, which
#: only pins ``POST`` when CSRF protection is active. ``SecurityConfig`` calls
#: ``csrf().disable()`` first, so the matcher is created without a method and **any verb**
#: reaches the logout handler. The RuoYi front-end sends ``POST /logout`` regardless, so the
#: two readings are indistinguishable in practice -- pinned here as "any verb", with a note in
#: ``COMPATIBILITY.md`` that it must be re-checked against a running instance before cut-over.
LOGOUT_URL = "/logout"

#: Java: ``HttpMethod.POST`` / ``HttpMethod.GET`` in the ``SecurityConfig`` rule table.
_GET = "GET"


#: Java: the ``authorizeRequests()`` chain, **in declaration order**. Order is behaviour:
#: ``first match wins``, so moving a line changes who gets 401/403. Do not sort it.
AUTHORIZATION_RULES: Tuple[UrlRule, ...] = (
    # -- 对于登录login 注册register 验证码captchaImage 允许匿名访问 -----------
    UrlRule("/login", AccessMode.PERMIT_ALL),
    UrlRule("/captchaImage", AccessMode.PERMIT_ALL),
    # -- 静态资源，可匿名访问 (GET only) ------------------------------------
    UrlRule("/", AccessMode.PERMIT_ALL, _GET),
    UrlRule("/*.html", AccessMode.PERMIT_ALL, _GET),
    UrlRule("/**/*.html", AccessMode.PERMIT_ALL, _GET),
    UrlRule("/**/*.css", AccessMode.PERMIT_ALL, _GET),
    UrlRule("/**/*.js", AccessMode.PERMIT_ALL, _GET),
    #: ``ResourcesConfig`` serves uploads under ``/profile/**``; it is a static handler with
    #: no authentication of its own.
    UrlRule("/profile/**", AccessMode.PERMIT_ALL, _GET),
    # -- 监控/文档类接口禁止访问 -------------------------------------------
    UrlRule("/swagger-ui.html", AccessMode.DENY_ALL),
    UrlRule("/swagger-resources/**", AccessMode.DENY_ALL),
    UrlRule("/webjars/**", AccessMode.DENY_ALL),
    UrlRule("/*/api-docs", AccessMode.DENY_ALL),
    UrlRule("/druid/**", AccessMode.DENY_ALL),
    # -- 下载：匿名只能下"模板类"的，带 resource 参数的必须登录 -----------------
    UrlRule("/common/download**", AccessMode.ANONYMOUS),
    UrlRule("/common/download/resource**", AccessMode.AUTHENTICATED),
    # -- 图片预览：匿名可看，登录后反而 403 (RuoYi 现状，勿改) ----------------
    UrlRule("/system/file/view/**", AccessMode.ANONYMOUS),
    UrlRule("/system/notice/view/**", AccessMode.ANONYMOUS),
    # -- 定时同步接口：外部调度器调用，放行 ----------------------------------
    UrlRule("/manager/suspicious/syncSuspiciousCarTask", AccessMode.PERMIT_ALL),
    # -- 除上面外的所有请求全部需要鉴权认证 (anyRequest().authenticated()) ----
    #: **Python-only addition.** ``/health`` is the liveness probe required by the migration
    #: brief ("must be startable, with health-check verification") and has no Java
    #: counterpart, so it cannot inherit a rule from ``SecurityConfig``. Declared *after*
    #: every Java rule and *before* the catch-all, so it can never shadow Java behaviour --
    #: no Java pattern matches ``/health``. Recorded in ``COMPATIBILITY.md``.
    UrlRule("/health", AccessMode.PERMIT_ALL),
)

#: The fall-through ``anyRequest().authenticated()``.
DEFAULT_ACCESS = AccessMode.AUTHENTICATED


def resolve_access(method: str, path: str) -> AccessMode:
    """Return the access mode that governs ``method path``.

    Java: ``FilterSecurityInterceptor`` asking
    ``AbstractSecurityInterceptor#getAttributes(object)`` -> first matching
    ``ConfigAttribute`` from the metadata source.

    ``method`` is compared verbatim (upper-case it yourself, as ``request.method`` already
    is); ``path`` is the context-relative request path without the query string, i.e.
    ``HttpServletRequest#getServletPath() + getPathInfo()``.
    """
    for rule in AUTHORIZATION_RULES:
        if rule.http_method is not None and rule.http_method != method:
            continue
        if is_match(rule.pattern, path):
            return rule.access
    return DEFAULT_ACCESS


def is_logout_request(method: str, path: str) -> bool:
    """Java: ``LogoutFilter#requiresLogout`` -> ``logoutRequestMatcher.matches(request)``.

    ``LogoutFilter`` sits **sixth** in the chain, i.e. before ``JwtAuthenticationTokenFilter``
    and long before ``FilterSecurityInterceptor``. A matching request is handled and the
    chain stops, so ``/logout`` never reaches the rule table and answers 200 even without a
    token.
    """
    return is_match(LOGOUT_URL, path)


__all__ = [
    "AccessMode",
    "UrlRule",
    "AUTHORIZATION_RULES",
    "DEFAULT_ACCESS",
    "LOGOUT_URL",
    "resolve_access",
    "is_logout_request",
]
