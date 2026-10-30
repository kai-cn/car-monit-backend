"""自定义退出处理类 返回成功 / the logout success handler.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/security/handle/LogoutSuccessHandlerImpl.java

Java original
-------------
``LogoutFilter`` matches ``/logout`` **before** ``JwtAuthenticationTokenFilter`` has run, so
the ``Authentication`` argument Spring passes in is ``null`` under a stateless setup. The
handler ignores it and re-reads the token itself via ``tokenService.getLoginUser(request)`` --
which is also why logging out works with nothing but the ``Authorization`` header.

Three side effects, in this order:

1. ``tokenService.delLoginUser(loginUser.getToken())`` -- delete ``login_tokens:<uuid>`` from
   Redis. This is the *only* thing that invalidates a token; the JWT itself stays valid
   forever and simply stops resolving to a session.
2. ``AsyncManager.me().execute(AsyncFactory.recordLogininfor(userName, LOGOUT, ...))`` -- the
   audit row, written on a background thread.
3. ``ServletUtils.renderString(...)`` -- ``HTTP 200`` with
   ``{"code":200,"msg":"退出成功"}``.

Note the asymmetry: a request without a token still gets ``{"code":200,...}``; there is simply
nothing to delete and no audit row. A request with a **malformed** token gets ``HTTP 200``
with ``code`` 401 and a message naming ``/error`` -- ``getLoginUser`` -> ``parseToken`` throws,
and the container answers a filter-level exception with an ERROR dispatch that this same
security chain then denies. Both behaviours are preserved.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request, Response

from app.common.constant.constants import LOGOUT
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.model.login_user import LoginUser
from app.common.utils.json_utils import to_json_string
from app.common.utils.message_utils import message
from app.common.utils.servlet_utils import render_string
from app.framework.manager.async_manager import AsyncManager
from app.framework.manager.factory.async_factory import record_logininfor
from app.framework.web.service.token_service import TokenService, get_token_service

#: Java: ``MessageUtils.message("user.logout.success")`` -> ``退出成功`` from
#: ``i18n/messages.properties``.
LOGOUT_SUCCESS_CODE = "user.logout.success"
#: ``BaseException``'s fallback when a bundle key is missing: Spring's
#: ``NoSuchMessageException`` is swallowed and the default is used.
LOGOUT_SUCCESS_DEFAULT = "退出成功"


class LogoutSuccessHandlerImpl:
    """Java: ``@Configuration LogoutSuccessHandlerImpl implements LogoutSuccessHandler``."""

    def __init__(self, token_service: Optional[TokenService] = None) -> None:
        self._token_service = token_service

    @property
    def token_service(self) -> TokenService:
        """Java: ``@Autowired private TokenService tokenService`` (resolved lazily)."""
        if self._token_service is None:
            self._token_service = get_token_service()
        return self._token_service

    # Java: public void onLogoutSuccess(HttpServletRequest, HttpServletResponse, Authentication)
    def on_logout_success(self, request: Request, authentication: Optional[object] = None) -> Response:
        """Delete the session, write the audit row, answer success."""
        login_user: Optional[LoginUser] = self.token_service.get_login_user(request)
        if login_user is not None:
            user_name = login_user.get_username()
            # 删除用户缓存记录
            self.token_service.del_login_user(login_user.token)
            # 记录用户退出日志
            AsyncManager.me().execute(
                record_logininfor(user_name, LOGOUT, _success_message())
            )
        return render_string(to_json_string(AjaxResult.success_message(_success_message())))


def _success_message() -> str:
    """Java: ``MessageUtils.message("user.logout.success")`` with the resource fallback."""
    return message(LOGOUT_SUCCESS_CODE) or LOGOUT_SUCCESS_DEFAULT


_LOGOUT_SUCCESS_HANDLER: Optional[LogoutSuccessHandlerImpl] = None


def get_logout_success_handler() -> LogoutSuccessHandlerImpl:
    """Process-wide instance (Java: the ``@Configuration``-annotated bean)."""
    global _LOGOUT_SUCCESS_HANDLER
    if _LOGOUT_SUCCESS_HANDLER is None:
        _LOGOUT_SUCCESS_HANDLER = LogoutSuccessHandlerImpl()
    return _LOGOUT_SUCCESS_HANDLER


def reset_logout_success_handler() -> None:
    """Test helper: drop the singleton so a fake ``TokenService`` can be injected."""
    global _LOGOUT_SUCCESS_HANDLER
    _LOGOUT_SUCCESS_HANDLER = None


__all__ = [
    "LogoutSuccessHandlerImpl",
    "LOGOUT_SUCCESS_CODE",
    "LOGOUT_SUCCESS_DEFAULT",
    "get_logout_success_handler",
    "reset_logout_success_handler",
]
