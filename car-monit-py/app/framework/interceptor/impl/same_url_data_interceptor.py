"""``SameUrlDataInterceptor`` —— 判断"URL + 数据"是否与上一次相同.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/impl/SameUrlDataInterceptor.java

Java 原文
---------
"请求地址 + 请求参数相同，且两次间隔小于 ``annotation.interval()`` 毫秒" 即视为重复提交。
判定结果缓存在 Redis::

    key   = CacheConstants.REPEAT_SUBMIT_KEY + requestURI + trimToEmpty(header(token.header))
    value = { requestURI : { "repeatParams": <params>, "repeatTime": <millis> } }
    ttl   = annotation.interval() 毫秒

``repeatParams`` 的取法（顺序不能改）

1. 请求被 :class:`~app.common.filter.repeatable.RepeatedlyRequestWrapper` 包装过
   （``RepeatableFilter`` 只包装 ``Content-Type: application/json``）-> 读**原始 body 字符串**；
2. body 为空 -> ``JSON.toJSONString(request.getParameterMap())``，即 query + 表单字段，
   值是**数组**（``String[]``），例如 ``{"a":["1"]}``。

同样的逻辑在这里用 ``await request.body()`` + ``query_params`` / ``form`` 复现。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from starlette.datastructures import UploadFile
from starlette.requests import Request

from app.common.annotation.repeat_submit import RepeatSubmit
from app.common.constant.cache_constants import REPEAT_SUBMIT_KEY
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.time_unit import TimeUnit
from app.framework.interceptor.repeat_submit_interceptor import (
    RepeatSubmitInterceptor,
    _now_millis,
)
from app.settings import get_settings

logger = logging.getLogger("app.framework.interceptor.impl.same_url_data_interceptor")

#: Java: ``public final String REPEAT_PARAMS = "repeatParams"``
REPEAT_PARAMS = "repeatParams"
#: Java: ``public final String REPEAT_TIME = "repeatTime"``
REPEAT_TIME = "repeatTime"


class SameUrlDataInterceptor(RepeatSubmitInterceptor):
    """Java: ``@Component public class SameUrlDataInterceptor extends RepeatSubmitInterceptor``."""

    def __init__(
        self,
        redis_cache: Optional[RedisCache] = None,
        header: Optional[str] = None,
    ) -> None:
        # Java: @Autowired private RedisCache redisCache; @Value("${token.header}") private String header;
        self._redis_cache = redis_cache
        self._header = header

    @property
    def redis_cache(self) -> RedisCache:
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    @property
    def header(self) -> str:
        """Java: ``@Value("${token.header}")`` —— 默认 ``Authorization``."""
        return self._header or get_settings().token.header

    async def is_repeat_submit(self, request: Request, annotation: RepeatSubmit) -> bool:
        """Java: ``isRepeatSubmit(HttpServletRequest request, RepeatSubmit annotation)``."""
        now_params = await _body_string(request)
        # 请求参数为空，则从参数表里取（覆盖 query string 与 urlencoded / multipart 表单）
        if not now_params:
            now_params = await _param_map_json(request)

        now_data: Dict[str, Any] = {REPEAT_PARAMS: now_params, REPEAT_TIME: _now_millis()}

        # 请求地址（作为存放 cache 的 key 值）
        url = _request_uri(request)
        # 唯一值（没有消息头则使用请求地址）
        submit_key = (request.headers.get(self.header) or "").strip()
        # 唯一标识（指定 key + url + 消息头）
        cache_repeat_key = REPEAT_SUBMIT_KEY + url + submit_key

        session_obj = self.redis_cache.get_cache_object(cache_repeat_key)
        if isinstance(session_obj, dict) and url in session_obj:
            pre_data = session_obj[url]
            if _compare_params(now_data, pre_data) and _compare_time(
                now_data, pre_data, annotation.interval
            ):
                logger.info("重复提交被拦截: url=%s", url)
                return True

        self.redis_cache.set_cache_object_with_timeout(
            cache_repeat_key, {url: now_data}, annotation.interval, TimeUnit.MILLISECONDS
        )
        return False


def _compare_params(now_map: Dict[str, Any], pre_map: Dict[str, Any]) -> bool:
    """Java: ``compareParams`` —— 只比较 ``repeatParams`` 字符串."""
    return str(now_map.get(REPEAT_PARAMS)) == str(pre_map.get(REPEAT_PARAMS))


def _compare_time(now_map: Dict[str, Any], pre_map: Dict[str, Any], interval: int) -> bool:
    """Java: ``compareTime`` —— ``(time1 - time2) < interval``.

    注意 Java 用的是**严格小于**，且拿"当前时间 - 上次时间"直接比，不给时钟回拨留余地：
    ``time1 < time2`` 时差值为负，反而永远算"重复"。照抄。
    """
    time1 = int(now_map.get(REPEAT_TIME) or 0)
    time2 = int(pre_map.get(REPEAT_TIME) or 0)
    return (time1 - time2) < interval


async def _body_string(request: Request) -> str:
    """Java: ``HttpHelper.getBodyString(RepeatedlyRequestWrapper)``.

    ``RepeatableFilter`` 只对 ``Content-Type: application/json`` 的请求包 wrapper，
    其它请求在这里返回空串（于是走参数表分支）。
    """
    content_type = (request.headers.get("content-type") or "").lower()
    if not content_type.startswith("application/json"):
        return ""
    raw = await request.body()
    if not raw:
        return ""
    # Java 用 request 的字符编码读取（项目里是 UTF-8）；非法字节不应让请求 500。
    return raw.decode("utf-8", errors="replace")


async def _param_map_json(request: Request) -> str:
    """Java: ``JSON.toJSONString(request.getParameterMap())`` —— 值是数组，紧凑输出."""
    collected: Dict[str, List[str]] = {}
    for key, value in request.query_params.multi_items():
        collected.setdefault(key, []).append(value)

    content_type = (request.headers.get("content-type") or "").lower()
    if content_type.startswith(("application/x-www-form-urlencoded", "multipart/form-data")):
        form = await request.form()
        for key, value in form.multi_items():
            # Java 的 getParameter 对文件字段返回原始文件名
            text = value.filename if isinstance(value, UploadFile) else value
            collected.setdefault(key, []).append("" if text is None else str(text))

    return json.dumps(collected, ensure_ascii=False, separators=(",", ":"))


def _request_uri(request: Request) -> str:
    """Java: ``HttpServletRequest.getRequestURI()`` —— 不含 query，百分号编码保持原样."""
    raw_path = request.scope.get("raw_path")
    if raw_path:
        return raw_path.decode("latin-1")
    return request.url.path


__all__ = ["REPEAT_PARAMS", "REPEAT_TIME", "SameUrlDataInterceptor"]
