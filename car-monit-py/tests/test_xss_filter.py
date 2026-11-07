"""XSS 过滤器回归用例.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/filter/XssFilter.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/html/HTMLFilter.java

分两层验证：

1. ``EscapeUtil.clean`` 的白名单/协议/注释/未闭合标签语义；
2. ``XssMiddleware`` 的 URL pattern、GET/DELETE 放行、excludes、query/form/JSON body
   清洗与 ``Content-Length`` 更新。
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.common.utils.escape_util import clean
from app.middleware.xss import XssMiddleware


def _xss_settings(enabled: bool = True) -> Any:
    return SimpleNamespace(
        xss=SimpleNamespace(
            enabled=enabled,
            url_patterns="/system/*,/monitor/*,/tool/*",
            excludes="/system/notice",
        )
    )


def _build_app(enabled: bool = True) -> TestClient:
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

    app.add_middleware(XssMiddleware, settings=_xss_settings(enabled))
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

    def test_create_app_registers_xss_as_the_outermost_middleware(self) -> None:
        from app.main import create_app

        application = create_app()
        assert application.user_middleware[0].cls is XssMiddleware
