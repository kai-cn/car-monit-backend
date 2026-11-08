"""非业务异常对外脱敏、对内可追踪（P1-6）."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config.exception_handlers import GENERIC_ERROR_MESSAGE, register_exception_handlers
from app.middleware.trace_id import TraceIdMiddleware
from app.settings import get_settings


def _client() -> TestClient:
    app = FastAPI()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("SQL detail: select * from sys_user where id=1")

    register_exception_handlers(app)
    app.add_middleware(TraceIdMiddleware, settings=get_settings())
    return TestClient(app, raise_server_exceptions=False)


def test_unexpected_error_is_masked_but_keeps_trace_id() -> None:
    response = _client().get("/boom")

    assert response.status_code == 200
    body = response.json()
    assert body == {"code": 500, "msg": GENERIC_ERROR_MESSAGE}
    assert "SQL detail" not in response.text
    assert "select * from" not in response.text
    # 详情只进日志；客户端拿到 TraceId 以便报障定位
    assert response.headers.get("x-trace-id")
