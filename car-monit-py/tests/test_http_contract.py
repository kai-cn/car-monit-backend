"""HTTP contract tests: the invariants a Java client depends on.

# Migrated from: (no Java test) -- behaviour copied from
#   SysIndexController, TraceIdFilter, GlobalExceptionHandler, SecurityConfig

每个断言都对应 Java 侧的一个具体实现，不是「照着 Python 输出抄的」。
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestIndexEndpoint:
    """Java: ``SysIndexController#index`` -> ``@RequestMapping("/")`` returning String."""

    def test_get_root_returns_plain_text(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        # text/plain;charset=UTF-8 -- 与 Spring 的 StringHttpMessageConverter 一致
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text == "欢迎使用系统后台管理框架，请通过前端地址访问。"

    def test_root_only_get_is_permitted(self, client: TestClient) -> None:
        """Java: ``.antMatchers(HttpMethod.GET, "/").permitAll()`` -- 其余动词落到 anyRequest。

        ``HttpMethod.matches(String)`` 是**名字精确比较**，所以 ``HEAD`` 也不匹配 ``GET``；
        POST/PUT/DELETE/PATCH 因此走 ``anyRequest().authenticated()``，匿名调用者拿到
        **HTTP 200 + code 401**（RuoYi 的全套约定：真实状态在响应体里）。
        """
        for verb in ("post", "put", "delete", "patch"):
            response = getattr(client, verb)("/")
            assert response.status_code == 200, verb
            assert response.json() == {
                "code": 401,
                "msg": "请求访问：/，认证失败，无法访问系统资源",
            }


class TestTraceIdFilter:
    """Java: ``com.ruoyi.common.core.filter.TraceIdFilter``."""

    def test_response_carries_trace_id_header(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.headers.get("X-Trace-Id")
        assert len(response.headers["X-Trace-Id"]) >= 16

    def test_incoming_trace_id_is_echoed(self, client: TestClient) -> None:
        """Java 原语义：请求头已有 X-Trace-Id 时直接复用，不重新生成。"""
        response = client.get("/", headers={"X-Trace-Id": "trace-from-upstream"})
        assert response.headers["X-Trace-Id"] == "trace-from-upstream"


class TestGlobalExceptionHandler:
    """Java: ``com.ruoyi.framework.web.exception.GlobalExceptionHandler``."""

    def test_unmapped_path_returns_spring_404_body(self, client: TestClient) -> None:
        """未匹配路由走 Spring ``BasicErrorController``，返回真实 404（这是唯一的例外）。

        路径必须在**白名单内**，否则永远看不到 404：安全过滤器在路由之前执行（见
        ``test_unmapped_path_without_token_is_unauthorized``）。``/profile/**`` 对 GET 是
        ``permitAll``，正好用来穿过过滤器链。
        """
        response = client.get("/profile/definitely-not-a-route")
        assert response.status_code == 404
        body = response.json()
        assert set(body.keys()) == {"timestamp", "status", "error", "path"}
        assert body["status"] == 404
        assert body["error"] == "Not Found"
        assert body["path"] == "/profile/definitely-not-a-route"

    def test_unmapped_path_without_token_is_unauthorized(self, client: TestClient) -> None:
        """鉴权发生在路由之前：未映射路径 + 无令牌 = 401，而不是 404。

        Java: ``FilterSecurityInterceptor`` 排在 ``DispatcherServlet`` 之前，
        ``anyRequest().authenticated()`` 先把请求否决掉，容器根本走不到
        ``NoHandlerFoundException``。新增安全层后这个顺序才是「意料之外但真实」的。
        """
        response = client.get("/definitely-not-a-route")
        assert response.status_code == 200
        assert response.json() == {
            "code": 401,
            "msg": "请求访问：/definitely-not-a-route，认证失败，无法访问系统资源",
        }

    def test_method_not_allowed_is_http_200(self, client: TestClient) -> None:
        """Java: ``@ExceptionHandler(HttpRequestMethodNotSupportedException)`` 返回 AjaxResult。

        注意：HTTP 状态码是 200，业务码在响应体里 —— RuoYi 的统一约定。
        """
        # /health 只注册了 GET；POST 会触发 405
        response = client.post("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 500
        assert body["msg"] == "Request method 'POST' not supported"


class TestHealthEndpoint:
    """ADDED endpoint -- see COMPATIBILITY.md. Not present in the Java project."""

    def test_health_returns_ajax_result(self, client: TestClient) -> None:
        response = client.get("/health")
        # RuoYi 约定：健康检查永远 HTTP 200，真实状态在 data.status
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        assert body["data"]["status"] in ("UP", "DOWN")
        assert body["data"]["application"] == "系统"
        assert set(body["data"]["components"].keys()) == {"db", "redis"}


class TestCorsConfig:
    """Java: ``ResourcesConfig#corsFilter``.

    ``setAllowCredentials(true)`` + ``maxAge(1800)``。Python 侧默认不再全开：
    local 空白名单只回显回环地址，生产走 ``app.cors.allowed_origins`` 白名单。
    """

    def test_preflight_echoes_loopback_origin_with_credentials(self, client: TestClient) -> None:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert response.headers["access-control-allow-credentials"] == "true"
        # Java: config.setMaxAge(1800L)
        assert response.headers["access-control-max-age"] == "1800"

    def test_simple_request_exposes_trace_header(self, client: TestClient) -> None:
        """TraceIdFilter 写的响应头必须能被浏览器 JS 读到。"""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert "x-trace-id" in response.headers.get("access-control-expose-headers", "").lower()

    def test_configured_whitelist_only_echoes_listed_origins(self) -> None:
        """``app.cors.allowed_origins`` 非空时只回显白名单内的 Origin（P1-8）。"""
        from app.main import create_app
        from app.settings import AppSettings

        application = create_app(
            AppSettings(app={"cors": {"allowed_origins": ["https://ok.example"]}})
        )
        http = TestClient(application)

        allowed = http.options(
            "/",
            headers={
                "Origin": "https://ok.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert allowed.headers["access-control-allow-origin"] == "https://ok.example"

        denied = http.options(
            "/",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in denied.headers
