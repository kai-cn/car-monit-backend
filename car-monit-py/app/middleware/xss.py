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
* ``xss.max_body_bytes``（Python-only，默认 1MB）：清洗前最多缓冲这么多字节；
  超过上限时直接返回 413，避免恶意大包把中间件内存放大。``0`` 表示不限制。
  超限后只做**有界 drain**（最多再读 ``limit + 64KB``），不会被永不结束的慢速
  chunked body 挂住。中间件注册在 TraceId/CORS 内侧，413 由外层补齐响应头。
* body / query 不是合法 UTF-8 时**不清洗、按原样放行**（并记 WARNING）。
  Java 的 ``getInputStream`` 用容器已解码的字符流，Python 若用 ``errors="replace"``
  重编码会静默改写内容，反而破坏下游的 JSON 解析。
* Java 的 ``getParameterMap`` 不走 ``getParameterValues``，审计日志可能看到未清洗值；
  Python 在进入路由前统一清洗 query/form，所有下游（包括审计）看到的是清洗后的值。
  这是比 Java 更严格的行为，不影响安全语义。
"""

from __future__ import annotations

import json
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


class _BodyTooLarge(Exception):
    """body 超过 ``xss.max_body_bytes``；由中间件转成 413."""


def _header(headers: List[Tuple[bytes, bytes]], name: bytes) -> str:
    for key, value in headers:
        if key.lower() == name:
            return value.decode("latin-1")
    return ""


def _content_length(headers: List[Tuple[bytes, bytes]]) -> Optional[int]:
    raw = _header(headers, b"content-length").strip()
    if not raw.isdigit():
        return None
    return int(raw)


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


_DRAIN_UNIT = 64 * 1024


async def _drain_body(receive: Receive, limit: int) -> None:
    """超限后最多再读 ``limit + _DRAIN_UNIT`` 字节，避免被慢速大包挂住.

    旧实现会一直读到达 ``more_body=False``；攻击者用一个永不结束的慢速 chunked
    body 就能让中间件在鉴权前一直占着连接。这里给一个固定预算：读满即停，剩下
    的数据由服务器在响应后丢弃 / 关闭连接。
    """
    budget = limit + _DRAIN_UNIT
    drained = 0
    while drained < budget:
        message = await receive()
        if message["type"] != "http.request":
            return
        drained += len(message.get("body", b""))
        if not message.get("more_body", False):
            return


async def _read_body(receive: Receive, limit: int) -> bytes:
    """读完整个请求体；``limit > 0`` 时超过上限抛 :class:`_BodyTooLarge`.

    超限时只做有界 drain（见 :func:`_drain_body`），不保存剩余内容。
    """
    chunks: List[bytes] = []
    total = 0
    while True:
        message = await receive()
        if message["type"] != "http.request":
            break
        chunk = message.get("body", b"")
        total += len(chunk)
        if limit > 0 and total > limit:
            if message.get("more_body", False):
                await _drain_body(receive, limit)
            raise _BodyTooLarge
        chunks.append(chunk)
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


async def _send_body_too_large(send: Send, limit: int) -> None:
    """Java 没有等价行为：超过 Python-only 的 XSS 缓冲上限时直接 413."""
    body = json.dumps(
        {"code": 500, "msg": f"请求体超过 XSS 清洗上限（{limit} 字节）"}
    ).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json;charset=utf-8"),
                (b"content-length", str(len(body)).encode("latin-1")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


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
                cleaned_query = _clean_values(query.decode("utf-8"))
                scope["query_string"] = cleaned_query.encode("utf-8")
            except UnicodeDecodeError:
                logger.warning("[XSS] query 不是合法 UTF-8，按原样放行")
            except Exception:  # noqa: BLE001 - 清洗失败时按原样放行，不能打断请求
                logger.warning("[XSS] query 清洗失败，按原样放行", exc_info=True)

        content_type = _header(headers, b"content-type").lower()
        new_body: Optional[bytes] = None
        is_json = content_type.startswith(_JSON_CONTENT_TYPE)
        is_form = content_type.startswith(_FORM_CONTENT_TYPE)
        if is_json or is_form:
            limit = int(getattr(self._settings.xss, "max_body_bytes", 0) or 0)
            declared = _content_length(headers)
            if limit > 0 and declared is not None and declared > limit:
                await _send_body_too_large(send, limit)
                return
            try:
                body = await _read_body(receive, limit)
            except _BodyTooLarge:
                await _send_body_too_large(send, limit)
                return
            try:
                if body:
                    text = body.decode("utf-8")  # 严格解码：非法字节不静默改写
                    if is_json:
                        new_body = java_trim(escape_util.clean(text)).encode("utf-8")
                    else:
                        new_body = _clean_values(text).encode("utf-8")
                else:
                    new_body = body
            except UnicodeDecodeError:
                logger.warning("[XSS] body 不是合法 UTF-8，跳过清洗并按原样放行")
                new_body = body
            except Exception:  # noqa: BLE001 - 同上
                logger.warning("[XSS] body 清洗失败，按原样放行", exc_info=True)
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
