"""非业务异常对外脱敏、对内可追踪（P1-6 / P2-1）."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from app.config.exception_handlers import (
    FallbackExceptionMiddleware,
    GENERIC_ERROR_MESSAGE,
    register_exception_handlers,
)
from app.middleware.trace_id import TraceIdMiddleware
from app.settings import get_settings

_ORIGIN = "http://localhost:3000"


def _client() -> TestClient:
    app = FastAPI()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("SQL detail: select * from sys_user where id=1")

    @app.get("/keyerr")
    def keyerr() -> None:
        raise KeyError("missing key")

    # ``AttributeError`` 是本工程复刻 Java NPE 的哨兵异常（``_none_guard`` 路径）。
    @app.get("/attrerr")
    def attrerr() -> None:
        raise AttributeError("java.lang.NullPointerException: value is null")

    register_exception_handlers(app)
    # 与 create_app 相同的相对位置：TraceId -> CORS -> Fallback。
    app.add_middleware(FallbackExceptionMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Trace-Id"],
    )
    app.add_middleware(TraceIdMiddleware, settings=get_settings())
    return TestClient(app, raise_server_exceptions=False)


def test_unexpected_error_is_masked_but_keeps_trace_id() -> None:
    response = _client().get("/boom", headers={"Origin": _ORIGIN})

    assert response.status_code == 200
    body = response.json()
    assert body == {"code": 500, "msg": GENERIC_ERROR_MESSAGE}
    assert "SQL detail" not in response.text
    assert "select * from" not in response.text
    # 详情只进日志；客户端拿到 TraceId 以便报障定位
    assert response.headers.get("x-trace-id")
    assert response.headers.get("access-control-allow-origin") == _ORIGIN


@pytest.mark.parametrize(
    ("path", "leaked"),
    [
        ("/keyerr", "missing key"),
        ("/attrerr", "NullPointerException"),
    ],
)
def test_unhandled_builtin_exception_keeps_trace_and_cors_headers(
    path: str, leaked: str
) -> None:
    """``Exception`` 处理器曾挂在 ServerErrorMiddleware（最外层），响应缺少头部.

    ``KeyError`` / ``AttributeError`` 都不会被 ExceptionMiddleware 的已注册处理器
    接管，会一路逃到 ServerErrorMiddleware；兜底中间件必须把它们在内侧渲染成
    同一个 ``AjaxResult``，再由外侧的 TraceId / CORS 补头。
    """
    response = _client().get(path, headers={"Origin": _ORIGIN})

    assert response.status_code == 200
    assert response.json() == {"code": 500, "msg": GENERIC_ERROR_MESSAGE}
    assert leaked not in response.text
    assert response.headers.get("x-trace-id")
    assert response.headers.get("access-control-allow-origin") == _ORIGIN


def test_create_app_places_fallback_inside_trace_and_cors() -> None:
    """删掉 ``create_app`` 里的注册或调整顺序都必须让本用例变红。"""
    from app.main import create_app

    application = create_app()
    classes = [middleware.cls for middleware in application.user_middleware]

    assert classes.index(TraceIdMiddleware) < classes.index(CORSMiddleware)
    assert classes.index(CORSMiddleware) < classes.index(FallbackExceptionMiddleware)
