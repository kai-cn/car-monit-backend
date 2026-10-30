"""Global exception handling.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/web/exception/GlobalExceptionHandler.java

Critical behavioural invariant
------------------------------
RuoYi answers **HTTP 200** for every exception it handles; the real status lives in the
``code`` field of ``AjaxResult``. Authentication failures behave the same way because
``ServletUtils.renderString`` hard-codes ``response.setStatus(200)``.

Why a ``RuntimeError`` handler is mandatory
-------------------------------------------
Java's ``@ExceptionHandler(RuntimeException.class)`` is the catch-all for **every** RuoYi
exception that has no more specific handler: ``BaseException`` (-> ``USER``/``Captcha``
exceptions), ``CustomException`` (thrown all over ``SecurityUtils``) and anything else
unchecked. Python's closest counterpart is ``RuntimeError``, which the whole business
exception tree derives from (:mod:`app.common.exception.exceptions`).

Without it those exceptions miss ``ExceptionMiddleware`` and reach
``ServerErrorMiddleware``, whose handler **always re-raises** after sending the body: under
Uvicorn the client still receives the right ``{"code": 500, "msg": ...}``, but every such
failure is logged as an unhandled error and ``TestClient`` raises instead of returning --
which is exactly how this gap was found (``POST /login`` with a wrong password).

Only *unmapped* requests (no controller matched) escape the handler chain and produce a
real 404 from Spring's ``BasicErrorController``. That body shape is reproduced below so
clients that switch on HTTP status keep working.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.constant.http_status import HttpStatus
from app.common.core.context.trace_context import get_trace_id
from app.common.core.domain.ajax_result import AjaxResult
from app.common.exception.exceptions import AccessDeniedException, DemoModeException, ServiceException
from app.framework.interceptor.repeat_submit_interceptor import RepeatSubmitException

logger = logging.getLogger("app.config.exception_handlers")

# ``AccessDeniedException`` 的类定义在 ``app.common.exception.exceptions``
# （抛它的是控制器层，不该反向依赖处理器层）；这里只是转出，保持既有 import 路径可用。
__all__ = ["AccessDeniedException", "register_exception_handlers", "spring_error_response"]


def _ok(payload: AjaxResult) -> JSONResponse:
    """Emit HTTP 200 with an ``AjaxResult`` body (RuoYi's universal behaviour)."""
    return JSONResponse(status_code=HttpStatus.SUCCESS, content=dict(payload))


def _spring_error_body(request: Request, status: int, error: str) -> Dict[str, Any]:
    """Reproduce Spring Boot ``BasicErrorController``'s JSON body.

    Java: ``{"timestamp":"2024-01-01T00:00:00.000+00:00","status":404,"error":"Not Found","path":"/x"}``
    """
    return {
        "timestamp": _now_iso8601(),
        "status": status,
        "error": error,
        "path": request.url.path,
    }


def _now_iso8601() -> str:
    from datetime import datetime, timedelta, timezone

    # Spring serializes the timestamp with the JVM default zone; the JVM runs at GMT+8.
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="milliseconds")


def spring_error_response(request: Request, status: int, error: str) -> JSONResponse:
    """Render a Spring Boot ``BasicErrorController`` body with a **real** HTTP status.

    Needed by the code that runs *outside* the MVC dispatch, i.e. the security filter chain
    (:mod:`app.middleware.security`): a servlet filter sits upstream of
    ``DispatcherServlet``, so a 500 thrown there, or a 403 raised by
    ``AccessDeniedHandlerImpl`` (which calls ``response.sendError(403)``), is answered by the
    container's error page -- ``BasicErrorController`` -- and **not** by
    ``GlobalExceptionHandler``. Those responses therefore carry the true status code and this
    body, unlike everything else RuoYi returns.

    Java body: ``{"timestamp":"...","status":403,"error":"Forbidden","path":"/x"}``
    (``message`` and ``trace`` are omitted because ``server.error.include-*`` default to
    ``never``).
    """
    return JSONResponse(status_code=status, content=_spring_error_body(request, status, error))


def register_exception_handlers(app: FastAPI) -> None:
    """Register every handler on the FastAPI application."""

    # ---- Java: @ExceptionHandler(ServiceException.class) -------------------
    @app.exception_handler(ServiceException)
    async def handle_service_exception(request: Request, exc: ServiceException) -> JSONResponse:
        logger.error("[业务异常] 请求地址'%s', 异常: %s", request.url.path, exc, exc_info=True)
        if exc.code is not None:
            return _ok(AjaxResult.error_code(exc.code, str(exc)))
        return _ok(AjaxResult.error_message(str(exc)))

    # ---- Java: @ExceptionHandler(AccessDeniedException.class) -------------
    @app.exception_handler(AccessDeniedException)
    async def handle_access_denied(request: Request, exc: AccessDeniedException) -> JSONResponse:
        logger.error("请求地址'%s',权限校验失败'%s'", request.url.path, exc.message)
        return _ok(AjaxResult.error_code(HttpStatus.FORBIDDEN, "没有权限，请联系管理员授权"))

    # ---- Java: @ExceptionHandler(DemoModeException.class) -----------------
    @app.exception_handler(DemoModeException)
    async def handle_demo_mode(request: Request, exc: DemoModeException) -> JSONResponse:
        return _ok(AjaxResult.error_message("演示模式，不允许操作"))

    # ---- Java: RepeatSubmitInterceptor#preHandle（直接 renderString，无异常） --
    # Java 的拦截器把 ``AjaxResult.error(annotation.message())`` 写进响应体就返回 false，
    # 不经过 ``GlobalExceptionHandler``。本工程用依赖 + 异常短路，这里把它渲染成同一份
    # 响应：HTTP 200 + ``{"code":500,"msg":"<annotation.message>"}``。
    @app.exception_handler(RepeatSubmitException)
    async def handle_repeat_submit(request: Request, exc: RepeatSubmitException) -> JSONResponse:
        logger.warning("请求地址'%s',重复提交被拦截", request.url.path)
        return _ok(AjaxResult.error_message(exc.message))

    # ---- Java: @ExceptionHandler(MethodArgumentNotValidException.class) ---
    # Java: MethodArgumentNotValidException / BindException -> first field error message.
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        if errors:
            first = errors[0]
            # Pydantic ``msg`` is the closest analogue of ``FieldError.getDefaultMessage()``.
            message = str(first.get("msg", "参数校验失败"))
            field = ".".join(str(part) for part in first.get("loc", ()) if part not in ("body", "query", "path"))
            if field:
                message = f"{field} {message}"
        else:
            message = "参数校验失败"
        logger.error("[参数校验失败] 请求地址'%s', %s", request.url.path, message)
        return _ok(AjaxResult.error_message(message))

    # ---- Java: @ExceptionHandler(HttpRequestMethodNotSupportedException) --
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == HttpStatus.BAD_METHOD:
            # Java: AjaxResult.error(e.getMessage())
            # Spring's HttpRequestMethodNotSupportedException message is exactly
            # "Request method 'POST' not supported" -- no "Allowed: ..." suffix.
            method = request.method
            message = f"Request method '{method}' not supported"
            logger.error("请求地址'%s',不支持'%s'请求", request.url.path, method)
            return _ok(AjaxResult.error_message(message))
        if exc.status_code == HttpStatus.NOT_FOUND:
            # Unmapped path -> Spring BasicErrorController body with a real 404 status.
            return JSONResponse(
                status_code=HttpStatus.NOT_FOUND,
                content=_spring_error_body(request, HttpStatus.NOT_FOUND, "Not Found"),
            )
        # Any other framework-level status keeps its own code, wrapped in AjaxResult.
        return _ok(AjaxResult.error_code(exc.status_code, str(exc.detail)))

    # ---- Java: @ExceptionHandler(RuntimeException.class) ------------------
    # Catches RuoYiBaseException (UserException / CaptchaException ...), CustomException
    # and any other unchecked error that has no dedicated handler above. Registered on
    # ExceptionMiddleware, so the response is sent **without** re-raising -- unlike the
    # Exception handler below, which Starlette routes to ServerErrorMiddleware.
    @app.exception_handler(RuntimeError)
    async def handle_runtime_exception(request: Request, exc: RuntimeError) -> JSONResponse:
        logger.error("请求地址'%s',发生未知异常.", request.url.path, exc_info=True)
        return _ok(AjaxResult.error_message(str(exc)))

    # ---- Java: @ExceptionHandler(Exception.class) -------------------------
    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Java logs the URI and the message but returns ``e.getMessage()`` verbatim.
        logger.error(
            "请求地址'%s',发生未知异常. traceId=%s", request.url.path, get_trace_id(), exc_info=True
        )
        return _ok(AjaxResult.error_message(_java_message(exc)))


def _java_message(exc: Exception) -> Optional[str]:
    """Java: ``e.getMessage()`` —— 注意**它可以是 ``null``**.

    ``NullPointerException`` 在这套 JDK（未开 ``-XX:+ShowCodeDetailsInExceptionMessages``）
    上的 ``getMessage()`` 就是 ``null``，于是 ``GlobalExceptionHandler#handleException``
    返回 ``{"msg":null,"code":500}``。本工程用 ``AttributeError`` 承担 NPE 的角色
    （见 ``sys_config_service._none_guard`` 等），所以这两种文案必须还原成 ``null``：

    * Python 自己的 ``'NoneType' object has no attribute 'x'``；
    * 各处显式抛的 ``java.lang.NullPointerException: xxx is null`` 哨兵。

    其它 ``AttributeError``（例如 :mod:`app.system.mapper.sys_dict_data_mapper` 用它伪装
    ``TooManyResultsException``）自带 Java 异常文案，必须原样透出 —— 所以判据是**文案**，
    不是异常类型。
    """
    text = str(exc)
    if isinstance(exc, AttributeError) and (
        text.startswith("'NoneType' object has no attribute")
        or text.startswith("java.lang.NullPointerException")
    ):
        return None
    return text
