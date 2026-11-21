# -*- coding: utf-8 -*-
"""大屏 GET 响应缓存头与 ETag/304（Java V3 新增 Filter）。

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/filter/BigScreenResponseFilter.java

【Java→Python 差异】
* Java ``ContentCachingResponseWrapper`` 在 Filter 里缓存响应字节；Python/FastAPI 的
  ``BaseHTTPMiddleware`` 通过消费 ``response.body_iterator`` 实现，代价是响应体被整体读入内存
  （大屏 GET 响应 < 1MB，与 Java wrapper 的内存行为一致）。
* Java ``DigestUtils.md5DigestAsHex(body)`` → Python ``hashlib.md5(body).hexdigest()``。
* Java ``If-None-Match`` 精确字符串比较 → Python 同样精确比较（不处理多值/弱标签，
  与 Java 实现一致；差异记录在 COMPATIBILITY）。
* 下载流（``/download/``）被 Java Filter 的 ``shouldNotFilter`` 排除，这里同样跳过。
"""
from __future__ import annotations

import hashlib
import logging
from typing import Awaitable, Callable

from fastapi import Request
from starlette.responses import Response

log = logging.getLogger(__name__)

PREFIX = "/manager/bigScreen"
EXPOSED_HEADERS = "ETag, X-Data-Age, X-Cache, X-Degrade, X-Data-As-Of, X-Data-Source"


def _max_age(uri: str) -> int:
    """Java: ``maxAge(String uri)`` —— 按路径分档，默认 30 秒。"""
    if "/export/status/" in uri:
        return 5
    if any(part in uri for part in ("/sectionList", "/tollGantryFwqList", "/orgList")):
        return 300
    if "/carLocation" in uri or "/carWarning" in uri:
        return 10
    return 30


async def bigscreen_response_filter(request: Request,
                                    call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """非大屏 GET / 下载流直接透传；其它响应附加缓存头并支持 304。"""
    path = request.url.path
    if request.method != "GET" or not path.startswith(PREFIX) or "/download/" in path:
        return await call_next(request)

    response = await call_next(request)
    if response.status_code != 200:
        return response

    chunks = [chunk async for chunk in response.body_iterator]
    body = b"".join(chunk if isinstance(chunk, bytes) else chunk.encode("utf-8") for chunk in chunks)
    etag = '"' + hashlib.md5(body).hexdigest() + '"'

    headers = dict(response.headers)
    headers["ETag"] = etag
    headers["Cache-Control"] = f"private, max-age={_max_age(path)}, must-revalidate"
    headers["Access-Control-Expose-Headers"] = EXPOSED_HEADERS
    # CacheContext 是 Java 的 ThreadLocal；Python 侧由服务层写进 request.state.cache_meta。
    meta = getattr(request.state, "cache_meta", None) or {}
    if meta.get("level"):
        headers["X-Cache"] = str(meta["level"])
    headers["X-Data-Age"] = str(meta.get("data_age_seconds", 0))
    if meta.get("source"):
        headers["X-Data-Source"] = str(meta["source"])
    if meta.get("degrade_reason"):
        headers["X-Degrade"] = str(meta["degrade_reason"])
    if meta.get("data_as_of"):
        headers["X-Data-As-Of"] = str(meta["data_as_of"])

    if request.headers.get("If-None-Match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(content=body, status_code=200, headers=headers,
                    media_type=response.media_type)
