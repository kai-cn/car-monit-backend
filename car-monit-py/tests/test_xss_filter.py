"""XSS 过滤器回归用例.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/filter/XssFilter.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/html/HTMLFilter.java

分两层验证：

1. ``EscapeUtil.clean`` 的白名单/协议/注释/未闭合标签语义；
2. ``XssMiddleware`` 的 URL pattern、GET/DELETE 放行、excludes、query/form/JSON body
   清洗与 ``Content-Length`` 更新。
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.common.utils.escape_util import clean
from app.middleware.xss import XssMiddleware


def _xss_settings(enabled: bool = True, max_body_bytes: int = 1024 * 1024) -> Any:
    return SimpleNamespace(
        xss=SimpleNamespace(
            enabled=enabled,
            url_patterns="/system/*,/monitor/*,/tool/*",
            excludes="/system/notice",
            max_body_bytes=max_body_bytes,
        )
    )


def _build_app(enabled: bool = True, max_body_bytes: int = 1024 * 1024) -> TestClient:
    app = FastAPI()

    @app.get("/system/echo")
    @app.delete("/system/echo")
    @app.post("/system/echo")
    async def echo(request: Request) -> Any:
        return {
            "q": request.query_params.get("q"),
            "body": (await request.body()).decode("utf-8"),
            "content_length": request.headers.get("content-length"),
        }

    @app.post("/system/raw")
    async def raw(request: Request) -> Any:
        return {"hex": (await request.body()).hex()}

    @app.post("/system/upload")
    async def upload(request: Request) -> Any:
        parsed = await request.form()
        upload_file = parsed.get("file")
        content = await upload_file.read() if hasattr(upload_file, "read") else b""
        return {"note": parsed.get("note"), "file": content.decode("utf-8")}

    @app.post("/system/form")
    async def form(request: Request) -> Any:
        parsed = await request.form()
        return {"q": parsed.get("q"), "keep": parsed.get("keep")}

    @app.post("/system/text")
    async def text(request: Request) -> Any:
        return {"body": (await request.body()).decode("utf-8")}

    @app.post("/system/notice")
    async def notice(request: Request) -> Any:
        return {
            "q": request.query_params.get("q"),
            "body": (await request.body()).decode("utf-8"),
        }

    @app.post("/manager/echo")
    async def manager_echo(request: Request) -> Any:
        return {"q": request.query_params.get("q")}

    @app.post("/monitor/echo")
    async def monitor_echo(request: Request) -> Any:
        return {"q": request.query_params.get("q")}

    @app.post("/tool/echo")
    async def tool_echo(request: Request) -> Any:
        return {"q": request.query_params.get("q")}

    @app.post("/other/echo")
    async def other_echo(request: Request) -> Any:
        return {
            "q": request.query_params.get("q"),
            "body": (await request.body()).decode("utf-8"),
        }

    app.add_middleware(XssMiddleware, settings=_xss_settings(enabled, max_body_bytes))
    return TestClient(app)


class TestEscapeUtilClean:
    def test_disallowed_tags_are_removed_but_text_is_kept(self) -> None:
        assert clean("<script>alert(1)</script>") == "alert(1)"

    def test_allowed_tags_and_attributes_are_kept(self) -> None:
        assert clean("<b>hi</b>") == "<b>hi</b>"
        # Java 源码的属性引号是转义的（append("=\\\"")），输出保留反斜杠。
        assert clean('<a href="http://x">x</a>') == '<a href=\\"http://x\\">x</a>'

    def test_bad_protocol_becomes_anchor(self) -> None:
        assert clean('<a href="javascript:alert(1)">x</a>') == '<a href=\\"#alert(1)\\">x</a>'

    def test_comments_are_removed(self) -> None:
        assert clean("<!-- hi -->") == ""

    def test_unclosed_tag_is_closed(self) -> None:
        assert clean("<b>unclosed") == "<b>unclosed</b>"

    def test_plain_text_and_ampersand_are_untouched(self) -> None:
        assert clean("a & b") == "a & b"


class TestXssMiddleware:
    def test_get_and_delete_are_not_filtered(self) -> None:
        client = _build_app()
        token = "<script>x</script>"

        assert client.get(f"/system/echo?q={token}").json()["q"] == token
        assert client.delete(f"/system/echo?q={token}").json()["q"] == token

    def test_json_body_and_query_are_cleaned(self) -> None:
        client = _build_app()
        response = client.post(
            "/system/echo?q=<script>x</script>",
            json={"name": "<script>alert(1)</script>", "ok": "<b>hi</b>"},
        )
        payload = response.json()
        assert payload["q"] == "x"
        body = json.loads(payload["body"])
        assert body == {"name": "alert(1)", "ok": "<b>hi</b>"}

    def test_content_length_is_recomputed(self) -> None:
        client = _build_app()
        payload = client.post(
            "/system/echo", json={"name": "<script>alert(1)</script>"}
        ).json()
        assert int(payload["content_length"]) == len(payload["body"].encode("utf-8"))

    def test_urlencoded_form_values_are_cleaned(self) -> None:
        client = _build_app()
        response = client.post(
            "/system/form",
            content="q=%3Cscript%3Ex%3C%2Fscript%3E&keep=%3Cb%3Ehi%3C%2Fb%3E",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert response.json() == {"q": "x", "keep": "<b>hi</b>"}

    def test_excluded_path_is_untouched(self) -> None:
        client = _build_app()
        token = "<script>x</script>"
        payload = client.post(f"/system/notice?q={token}", json={"name": token}).json()
        assert payload["q"] == token
        assert json.loads(payload["body"]) == {"name": token}

    def test_other_paths_are_untouched(self) -> None:
        client = _build_app()
        token = "<script>x</script>"
        payload = client.post(f"/other/echo?q={token}", json={"name": token}).json()
        assert payload["q"] == token
        assert json.loads(payload["body"]) == {"name": token}

    def test_only_the_configured_patterns_are_cleaned(self) -> None:
        client = _build_app()
        token = "<script>x</script>"
        # Java 的 xss.urlPatterns 只有 /system/*,/monitor/*,/tool/*，/manager 不在其中。
        assert client.post(f"/manager/echo?q={token}").json()["q"] == token
        assert client.post("/monitor/echo?q=<script>x</script>").json()["q"] == "x"
        assert client.post("/tool/echo?q=<script>x</script>").json()["q"] == "x"

    def test_non_json_body_is_untouched(self) -> None:
        client = _build_app()
        token = "<script>x</script>"
        response = client.post(
            "/system/text",
            content=token,
            headers={"content-type": "text/plain"},
        )
        assert response.json()["body"] == token

    def test_values_are_trimmed(self) -> None:
        client = _build_app()
        assert client.post("/system/echo?q=%20%20x%20%20").json()["q"] == "x"

    def test_disabled_filter_passes_everything_through(self) -> None:
        client = _build_app(enabled=False)
        token = "<script>x</script>"
        payload = client.post(f"/system/echo?q={token}", json={"name": token}).json()
        assert payload["q"] == token
        assert json.loads(payload["body"]) == {"name": token}

    def test_oversized_json_body_returns_413(self) -> None:
        """body 超过 ``xss.max_body_bytes`` 时不进入清洗，直接 413."""
        client = _build_app(max_body_bytes=16)
        response = client.post("/system/echo", json={"name": "x" * 100})
        assert response.status_code == 413
        assert response.json()["msg"].startswith("请求体超过 XSS 清洗上限")

    def test_oversized_form_body_returns_413(self) -> None:
        client = _build_app(max_body_bytes=16)
        response = client.post(
            "/system/form",
            content="q=" + "a" * 100,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 413

    def test_non_utf8_json_body_is_passed_through(self) -> None:
        """非法 UTF-8 不能静默替换字节：原样交给下游，由下游按自己的规则报错."""
        client = _build_app()
        payload = b'{"name":"\xd5\xe3<script>x</script>"}'
        response = client.post(
            "/system/raw", content=payload, headers={"content-type": "application/json"}
        )
        assert response.status_code == 200
        assert bytes.fromhex(response.json()["hex"]) == payload

    def test_multipart_body_is_not_rewritten(self) -> None:
        """multipart 只处理文件原样透传；文本字段不清洗（与 Java 的差异已登记）."""
        client = _build_app()
        token = "<script>x</script>"
        response = client.post(
            "/system/upload",
            files={"file": ("a.txt", b"<script>file</script>", "text/plain")},
            data={"note": token},
        )
        assert response.status_code == 200
        assert response.json() == {"note": token, "file": "<script>file</script>"}

    def test_create_app_orders_trace_cors_xss_and_security(self) -> None:
        """XSS 必须在 TraceId/CORS 内侧、Security 外侧（413 才有响应头）."""
        from app.config.exception_handlers import FallbackExceptionMiddleware
        from app.main import create_app
        from app.middleware.request_context import RequestContextMiddleware
        from app.middleware.security import SecurityMiddleware
        from app.middleware.trace_id import TraceIdMiddleware
        from starlette.middleware.cors import CORSMiddleware

        application = create_app()
        classes = [middleware.cls for middleware in application.user_middleware]

        assert classes.index(TraceIdMiddleware) < classes.index(CORSMiddleware)
        assert classes.index(CORSMiddleware) < classes.index(XssMiddleware)
        assert classes.index(XssMiddleware) < classes.index(FallbackExceptionMiddleware)
        assert classes.index(XssMiddleware) < classes.index(RequestContextMiddleware)
        assert classes.index(XssMiddleware) < classes.index(SecurityMiddleware)

    def test_oversized_body_413_keeps_trace_and_cors_headers(self) -> None:
        """XSS 的 Python-only 413 也必须带 X-Trace-Id 与 ACAO."""
        from app.main import create_app
        from app.settings import AppSettings

        application = create_app(
            AppSettings(
                xss={"max_body_bytes": 16},
                app={"cors": {"allowed_origins": ["http://localhost:3000"]}},
            )
        )
        client = TestClient(application, raise_server_exceptions=False)

        response = client.post(
            "/system/user/list",
            headers={
                "Origin": "http://localhost:3000",
                "X-Trace-Id": "CLIENT-XSS-413",
            },
            json={"q": "x" * 100},
        )

        assert response.status_code == 413
        assert response.headers["x-trace-id"] == "CLIENT-XSS-413"
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_oversized_body_drain_is_bounded(self, monkeypatch) -> None:
        """超限后的 drain 必须有上限，不能被永不结束的慢速 body 挂住."""
        from app.middleware import xss as xss_module

        monkeypatch.setattr(xss_module, "_DRAIN_UNIT", 1024)
        calls = {"n": 0}

        async def receive() -> dict:
            calls["n"] += 1
            if calls["n"] > 20:
                raise AssertionError("drain 没有上限")
            return {"type": "http.request", "body": b"x" * 1024, "more_body": True}

        with pytest.raises(xss_module._BodyTooLarge):
            asyncio.run(xss_module._read_body(receive, 8))

        # 首个 chunk 超限（1 次）+ budget=8+1024 的 drain（2 次）
        assert calls["n"] == 3
