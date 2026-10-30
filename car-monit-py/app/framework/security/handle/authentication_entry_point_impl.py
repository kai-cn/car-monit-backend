"""认证失败处理类 返回未授权 / the 401 answer.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/security/handle/AuthenticationEntryPointImpl.java

Java original
-------------
``ExceptionTranslationFilter`` calls this whenever an ``AuthenticationException`` reaches it,
and also whenever an ``AccessDeniedException`` arrives **while the caller is anonymous**
(``AuthenticationTrustResolver.isAnonymous``): being refused while not logged in means
"please authenticate", not "you are forbidden".

The response is built with ``ServletUtils.renderString``, which forces ``HTTP 200``. So the
wire format is::

    HTTP/1.1 200
    Content-Type: application/json;charset=UTF-8

    {"code":401,"msg":"请求访问：/system/user/list，认证失败，无法访问系统资源"}

Clients must therefore read ``code``, never the HTTP status -- this is the single most
important RuoYi invariant in the whole authentication path.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Request, Response

from app.common.constant.http_status import HttpStatus
from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils import string_utils
from app.common.utils.json_utils import to_json_string
from app.common.utils.servlet_utils import render_string

#: Java: ``StringUtils.format("请求访问：{}，认证失败，无法访问系统资源", request.getRequestURI())``.
UNAUTHORIZED_MESSAGE_TEMPLATE = "请求访问：{}，认证失败，无法访问系统资源"


class AuthenticationEntryPointImpl:
    """Java: ``@Component AuthenticationEntryPointImpl implements AuthenticationEntryPoint``."""

    # Java: public void commence(HttpServletRequest, HttpServletResponse, AuthenticationException)
    def commence(self, request: Request, exception: Any = None) -> Response:
        """Render the 401 envelope.

        ``exception`` exists only to mirror the Java signature -- the implementation never
        looks at it, and neither does this one. The path reported is ``getRequestURI()``,
        i.e. the path **with** the context path and without the query string; ``context-path``
        is ``/`` in this project, so ``request.url.path`` is the same value.
        """
        return self.commence_for_uri(request.url.path)

    def commence_for_uri(self, uri: str) -> Response:
        """Render the 401 envelope for an explicit URI.

        Not a Java method -- it is the seam for the one case where ``commence`` reports a
        path that is *not* the request's own: an exception thrown by a filter. ``Servlet``
        containers answer that with an ERROR dispatch to ``/error``, ``/error`` is not in
        ``SecurityConfig``'s permit-all list, and this entry point is what denies the second
        pass -- so the body names ``/error``, not the original path. ``SecurityMiddleware``
        has no such re-dispatch and calls this with ``"/error"`` to land on the same body.
        """
        code = HttpStatus.UNAUTHORIZED
        msg = string_utils.format(UNAUTHORIZED_MESSAGE_TEMPLATE, uri)
        return render_string(to_json_string(AjaxResult.error_code(code, msg)))


_ENTRY_POINT: Optional["AuthenticationEntryPointImpl"] = None


def get_authentication_entry_point() -> AuthenticationEntryPointImpl:
    """Process-wide instance (Java: the ``@Component`` singleton)."""
    global _ENTRY_POINT
    if _ENTRY_POINT is None:
        _ENTRY_POINT = AuthenticationEntryPointImpl()
    return _ENTRY_POINT


def reset_authentication_entry_point() -> None:
    """Test helper: drop the singleton."""
    global _ENTRY_POINT
    _ENTRY_POINT = None


__all__ = [
    "AuthenticationEntryPointImpl",
    "UNAUTHORIZED_MESSAGE_TEMPLATE",
    "get_authentication_entry_point",
    "reset_authentication_entry_point",
]
