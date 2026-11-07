"""XSS 过滤器 —— Java ``XssFilter`` + ``XssHttpServletRequestWrapper`` 的等价实现.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/filter/XssFilter.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/filter/XssHttpServletRequestWrapper.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/FilterConfig.java

Java 原语义
-----------
``FilterConfig`` 把 ``XssFilter`` 注册在 ``HIGHEST_PRECEDENCE``，URL pattern 取
``xss.urlPatterns``（本项目是 ``/system/*,/monitor/*,/tool/*``）。``XssFilter``：

* **GET / DELETE 直接放行**（``handleExcludeURL`` 的第一条分支）；
* 命中 ``xss.excludes``（逗号分隔，AntPathMatcher）直接放行；本项目是 ``/system/notice``；
* 其余请求包一层 ``XssHttpServletRequestWrapper``：
  * ``getParameterValues(name)`` 对每个值执行 ``EscapeUtil.clean(value).trim()``；
  * ``getInputStream()`` 仅对 ``Content-Type: application/json`` 的 body 做
    ``EscapeUtil.clean(body).trim()``（**整段文本**，不是逐字段解析 JSON）。

Python 等价实现
---------------
纯 ASGI 中间件（不是 ``BaseHTTPMiddleware``，因为要改写请求体）：

1. 只处理 ``http`` scope；
2. 方法为 GET / DELETE、命中 excludes、或不在 urlPatterns 内时直接透传；
3. 改写 ``scope["query_string"]`` 中的**值**（键不动）；
4. 对 ``application/json`` 的 body 做整段文本清洗；对
   ``application/x-www-form-urlencoded`` 按参数值清洗；
5. 改写 body 时同步更新 ``Content-Length``（并移除 ``Transfer-Encoding``），
   用一次性 ``receive`` 把新 body 交给下游。

已知差异（记录在 COMPATIBILITY.md）
-----------------------------------
* ``multipart/form-data`` 的**文本字段**没有清洗：Java 的 Servlet 容器会解析 multipart
  并让 wrapper 清洗字段值；Python 侧重建 multipart 会破坏文件流，故只保留文件原样。
  本项目命中 XSS 过滤的 multipart 端点只有 ``/system/file`` 的上传，没有文本字段。
* Java 的 ``getParameterMap`` 不走 ``getParameterValues``，审计日志可能看到未清洗值；
  Python 在进入路由前统一清洗 query/form，所有下游（包括审计）看到的是清洗后的值。
  这是比 Java 更严格的行为，不影响安全语义。
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode

from app.common.utils import escape_util
from app.common.utils.string_utils import is_match, java_trim
from app.settings import AppSettings, get_settings

logger = logging.getLogger("app.middleware.xss")

Scope = Dict[str, Any]
Receive = Callable[[], Awaitable[Dict[str, Any]]]
Send = Callable[[Dict[str, Any]], Awaitable[None]]

_JSON_CONTENT_TYPE = "application/json"
_FORM_CONTENT_TYPE = "application/x-www-form-urlencoded"


def _header(headers: List[Tuple[bytes, bytes]], name: bytes) -> str:
    for key, value in headers:
        if key.lower() == name:
            return value.decode("latin-1")
    return ""


def _servlet_pattern_match(pattern: str, path: str) -> bool:
    """Servlet ``urlPatterns`` 语义（``/system/*`` 是前缀匹配，不是 Ant ``*``）。

    Java 的 ``FilterRegistrationBean.addUrlPatterns`` 走 Servlet 规范：
    ``/system/*`` 匹配 ``/system`` 与 ``/system/...``（可跨多段），而 AntPathMatcher
    的 ``*`` 不跨 ``/``。两者不能混用。
    """
    pattern = pattern.strip()
    if not pattern:
        return False
    if pattern == "/*":
        return True
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        return path == prefix or path.startswith(prefix + "/")
    if pattern.startswith("*."):
        return path.endswith(pattern[1:])
    return path == pattern


def _excluded(path: str, excludes: str) -> bool:
    """Java: ``StringUtils.matches(url, excludes)`` 的 List 重载（逗号分隔 + Ant）。"""
    return any(
        is_match(pattern.strip(), path)
        for pattern in excludes.split(",")
        if pattern.strip()
    )


def _clean_values(query: str) -> str:
    """对 query / form 的**值**执行 ``EscapeUtil.clean(...).trim()``。"""
    pairs = parse_qsl(query, keep_blank_values=True)
    cleaned = [(key, java_trim(escape_util.clean(value))) for key, value in pairs]
    return urlencode(cleaned, doseq=True, encoding="utf-8", errors="replace")


async def _read_body(receive: Receive) -> bytes:
    chunks: List[bytes] = []
    while True:
        message = await receive()
        if message["type"] != "http.request":
            break
        chunks.append(message.get("body", b""))
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def _replay(body: bytes) -> Receive:
    sent = False

    async def receive() -> Dict[str, Any]:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    return receive


def _replace_body_headers(
    headers: List[Tuple[bytes, bytes]], body: bytes
) -> List[Tuple[bytes, bytes]]:
    headers = [
        (key, value)
        for key, value in headers
        if key.lower() not in (b"content-length", b"transfer-encoding")
    ]
    headers.append((b"content-length", str(len(body)).encode("latin-1")))
    return headers


class XssMiddleware:
    """Java: ``FilterConfig.xssFilterRegistration`` 注册的那条过滤器链。"""

    def __init__(self, app: Any, settings: Optional[AppSettings] = None) -> None:
        self.app = app
        self._settings = settings or get_settings()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self._settings.xss.enabled:
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method", "")).upper()
        path = str(scope.get("path", ""))
        if (
            method in ("GET", "DELETE")
            or _excluded(path, self._settings.xss.excludes)
            or not self._matches_url(path)
        ):
            await self.app(scope, receive, send)
            return

        scope = dict(scope)
        headers = list(scope.get("headers", []))

        query = scope.get("query_string", b"")
        if query:
            try:
                cleaned_query = _clean_values(
                    query.decode("utf-8", errors="replace")
                )
                scope["query_string"] = cleaned_query.encode("utf-8")
            except Exception:  # noqa: BLE001 - 清洗失败时按原样放行，不能打断请求
                logger.warning("[XSS] query 清洗失败，按原样放行", exc_info=True)

        content_type = _header(headers, b"content-type").lower()
        new_body: Optional[bytes] = None
        body: Optional[bytes] = None
        if content_type.startswith(_JSON_CONTENT_TYPE):
            body = await _read_body(receive)
            try:
                if body:
                    text = body.decode("utf-8", errors="replace")
                    new_body = java_trim(escape_util.clean(text)).encode("utf-8")
                else:
                    new_body = body
            except Exception:  # noqa: BLE001 - 同上
                logger.warning("[XSS] JSON body 清洗失败，按原样放行", exc_info=True)
                new_body = body
        elif content_type.startswith(_FORM_CONTENT_TYPE):
            body = await _read_body(receive)
            try:
                if body:
                    text = body.decode("utf-8", errors="replace")
                    new_body = _clean_values(text).encode("utf-8")
                else:
                    new_body = body
            except Exception:  # noqa: BLE001 - 同上
                logger.warning("[XSS] form body 清洗失败，按原样放行", exc_info=True)
                new_body = body

        if new_body is not None:
            headers = _replace_body_headers(headers, new_body)
            scope["headers"] = headers
            receive = _replay(new_body)

        await self.app(scope, receive, send)

    def _matches_url(self, path: str) -> bool:
        return any(
            _servlet_pattern_match(pattern, path)
            for pattern in self._settings.xss.url_patterns.split(",")
            if pattern.strip()
        )


__all__ = ["XssMiddleware"]
