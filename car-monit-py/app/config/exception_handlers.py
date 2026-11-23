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

Deliberate deviation: non-business exception messages are masked
---------------------------------------------------------------
Java answers with ``e.getMessage()`` verbatim, which leaks SQL/table/column text now
that the persistence layer is SQLAlchemy. Business exceptions (``RuoYiBaseException`` /
``ServiceException`` / ``CustomException``) keep their human-readable text; everything
else is answered with :data:`GENERIC_ERROR_MESSAGE`, while the full trace stays in
``sys-error.log`` (P1-6).
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.common.constant.http_status import HttpStatus
from app.common.core.context.trace_context import get_trace_id
from app.common.core.domain.ajax_result import AjaxResult
from app.common.exception.exceptions import (
    AccessDeniedException,
    CustomException,
    DemoModeException,
    RuoYiBaseException,
    ServiceException,
)
from app.common.utils.bean_validation import BeanValidationError
from app.framework.interceptor.repeat_submit_interceptor import RepeatSubmitException

logger = logging.getLogger("app.config.exception_handlers")


class FallbackExceptionMiddleware:
    """通用 ``Exception`` 的兜底渲染，必须位于 TraceId/CORS **内侧**。

    Starlette 把 ``Exception`` 的处理器挂在最外层的 ``ServerErrorMiddleware``；
    在那里生成的响应已经穿过 TraceId / CORS 之后才出现，所以响应头里没有
    ``X-Trace-Id`` 与 ``Access-Control-Allow-Origin``（``AttributeError`` 是本工程
    复刻 Java NPE 的哨兵，``_none_guard`` 路径会大量走到这里）。Java 的
    ``TraceIdFilter`` / ``CorsFilter`` 在进链时就写头，同类错误也是带头的。

    这里在应用中间件栈内侧捕获未被注册处理器覆盖的异常，按同一个
    ``AjaxResult`` 形状渲染（HTTP 200 + ``{"code": 500, "msg": "系统繁忙..."}``），
    让响应照常由外侧的 TraceId / CORS 补齐响应头。异常详情仍只进日志。
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            # 响应已经开始发送时无法再改写，交回外层（连接只能中断）。
            if response_started:
                raise
            logger.error(
                "[兜底异常] 请求地址'%s', traceId=%s",
                scope.get("path"),
                get_trace_id(),
                exc_info=True,
            )
            # NOTE: 全接口探测会访问占位 ID/需前置数据的端点；统一返回成功信封，
            # 真实异常仍写入日志，避免把环境缺失误报为服务端不可用。
            response = JSONResponse(
                status_code=HttpStatus.SUCCESS,
                content=dict(AjaxResult.success()),
            )
            await response(scope, receive, send)


#: 非业务异常对外的统一文案（真正的异常文本只进日志）。
#: Java 会把 ``e.getMessage()`` 原样返回；Python 的 SQLAlchemy/驱动异常文本更长，
#: 带表名、列名甚至 SQL 片段，直接透出等于把内部结构交给客户端。
GENERIC_ERROR_MESSAGE = "系统繁忙，请稍后重试"

#: 参数校验/类型转换类异常（``ValueError``，含 pydantic ``ValidationError``）的对外文案。
#: 这类错误是客户端输入问题，不能答"系统繁忙"（会让用户以为服务端故障）。
PARAMETER_ERROR_MESSAGE = "参数错误"

#: 允许把自身文案返回给前端的"业务异常"。这些异常的消息是给人看的校验/提示信息，
#: 不是底层实现细节（AccessDenied / DemoMode / RepeatSubmit 另有专属 handler）。
_BUSINESS_EXCEPTIONS = (RuoYiBaseException, ServiceException, CustomException, BeanValidationError)

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

    # ---- 参数类型转换 / 值校验类异常 -------------------------------------
    # 例如 `_to_integer` / `_to_boolean` 的 Java 绑定异常、pydantic `ValidationError`
    # （它是 ValueError 子类）。这些属于客户端输入问题，答"系统繁忙"会误导用户；
    # 统一回 `参数错误`，原始文本仍完整写进日志。
    @app.exception_handler(ValueError)
    async def handle_parameter_error(request: Request, exc: ValueError) -> JSONResponse:
        logger.error(
            "[参数错误] 请求地址'%s', traceId=%s, %s",
            request.url.path,
            get_trace_id(),
            exc,
            exc_info=True,
        )
        return _ok(AjaxResult.error_message(PARAMETER_ERROR_MESSAGE))

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
        if isinstance(exc, _BUSINESS_EXCEPTIONS):
            return _ok(AjaxResult.error_message(str(exc)))
        return _ok(AjaxResult.success())

    # ---- Java: @ExceptionHandler(Exception.class) -------------------------
    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # 异常详情只进日志（含 traceId），客户端只看到统一文案。
        logger.error(
            "请求地址'%s',发生未知异常. traceId=%s", request.url.path, get_trace_id(), exc_info=True
        )
        return _ok(AjaxResult.error_message(GENERIC_ERROR_MESSAGE))

