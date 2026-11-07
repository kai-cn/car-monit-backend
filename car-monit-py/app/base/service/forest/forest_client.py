"""Forest 声明式 HTTP 客户端的公共实现.

# Migrated from: com.dtflys.forest（第三方库，非本工程源码）

Java 侧全部是 ``@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")`` + ``@Get`` +
``@Query`` / ``@Var`` 的**接口声明**，方法体由 Forest 在运行时生成。Python 里没有
注解处理器，所以这里提供一个显式的小运行时：

* :func:`to_query_params` —— ``@Query`` 传对象时，把实体的**非 null** 字段按
  camelCase（Jackson 属性名）摊平成 query 参数（Forest 内部同样用 JSON 转换并
  丢弃 null）；
* :func:`forest_get` —— 发 GET、解析 JSON、按 ``forest.retry-count`` /
  ``forest.max-retry-interval`` 重试连接类错误；
* :func:`build_url` —— ``baseURL + path``，处理重复斜杠。

三处与 Forest 对齐的细节
------------------------
1. **超时**：``forest.connect-timeout`` 与 ``forest.timeout`` 都是 60000 ms；
   单个接口可以覆盖（``IHenDaApi`` 的 ``connectTimeout = 30000``）。
2. **重试**：``forest.retryer`` 是 ``BackOffRetryer``，``retry-count: 2`` ——
   只重试**传输层**异常，业务 4xx/5xx 不重试（Forest 同样不重试，它把非 2xx
   交给 ``onError``/默认抛 ``ForestNetworkException``）。
3. **非 2xx 抛错**：Forest 对非 2xx 响应抛 ``HttpProtocolException``，文案是
   ``HTTP <status> ErrorContent=<响应体>``；RuoYi 的 ``GlobalExceptionHandler`` 再把它
   原样塞进 ``AjaxResult.error(e.getMessage())``，所以 backend 的响应是
   ``{"code":500,"msg":"HTTP 500 ErrorContent={...}"}``（实测 ``/base/feerecords/{bigId}``）。
   另外**空响应体**（``/base/snapshotflow/earliest-time`` 的 Java 形态）在 Java 侧反序列化成
   ``null`` 而不是解析失败，所以这里返回 ``None``。
"""

from __future__ import annotations

import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Mapping, Optional

import httpx

from app.common.core.page.table_data_info import TableDataInfo
from app.settings import get_settings

#: Java: ``@Headers({"Connection: close"})``
_CONNECTION_CLOSE_HEADER = {"Connection": "close"}

#: Forest 的默认日期格式（``ForestDateConverter`` 未配置时使用）。
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ForestException(RuntimeError):
    """Java: ``com.dtflys.forest.exceptions.ForestRuntimeException``."""


def build_url(base_url: str, path: str) -> str:
    """``baseURL + path``，去掉拼接处的重复斜杠。"""
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _stringify(value: Any) -> str:
    """把字段值转成 query 字符串 —— 与 Forest 的 Jackson 转换一致。"""
    if isinstance(value, bool):
        # Java 的 Boolean.toString()
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.strftime(_DEFAULT_DATE_FORMAT)
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def to_query_params(entity: Any) -> Dict[str, str]:
    """``@Query OdsXxxEntity`` -> ``{camelCase 字段名: 字符串值}``（丢弃 ``None``）。"""
    if entity is None:
        return {}
    if isinstance(entity, Mapping):
        dumped: Dict[str, Any] = dict(entity)
    else:
        # ``by_alias=True`` 才是 Jackson 线上的 camelCase 名字；
        # ``mode="json"`` 让嵌套对象也变成 JSON 安全值。
        dumped = entity.model_dump(by_alias=True, mode="json")

    params: Dict[str, str] = {}
    for key, value in dumped.items():
        if value is None:
            continue
        params[key] = _stringify(value)
    return params


def _parse_response(response: httpx.Response, url: str) -> Any:
    """Java: Forest 的 ``HttpProtocolHandler`` 响应处理。

    * 非 2xx —— 抛 ``HttpProtocolException``，文案 ``HTTP <status> ErrorContent=<body>``；
    * 空响应体 —— 反序列化成 ``null``（Java 侧 ``String``/对象返回值都是这个形态）；
    * 其余 —— 正常 JSON 解析。
    """
    if not response.is_success:
        raise ForestException(f"HTTP {response.status_code} ErrorContent={response.text}")
    if not response.content or not response.text.strip():
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise ForestException(
            f"响应不是合法 JSON: {url} -> {response.text[:200]!r}"
        ) from exc


def forest_get(
    base_url: str,
    path: str,
    params: Optional[Dict[str, str]] = None,
    connect_timeout_ms: Optional[int] = None,
    timeout_ms: Optional[int] = None,
) -> Any:
    """发 GET 并返回 ``json.loads`` 之后的对象。"""
    settings = get_settings()
    forest = settings.forest

    connect_timeout = (connect_timeout_ms or forest.connect_timeout) / 1000.0
    read_timeout = (timeout_ms or forest.timeout) / 1000.0
    attempts = max(0, forest.retry_count) + 1

    url = build_url(base_url, path)
    last_error: Optional[Exception] = None

    for attempt in range(attempts):
        try:
            with httpx.Client(
                timeout=httpx.Timeout(read_timeout, connect=connect_timeout),
                headers=_CONNECTION_CLOSE_HEADER,
            ) as client:
                response = client.get(url, params=params)
            return _parse_response(response, url)
        except httpx.TransportError as exc:
            # Forest 的 BackOffRetryer 只对连接 / 读超时这类异常重试。
            last_error = exc
            if attempt + 1 >= attempts:
                break
            delay_ms = min(100 * (2**attempt), forest.max_retry_interval)
            time.sleep(delay_ms / 1000.0)

    raise ForestException(f"请求失败: {url} -> {last_error}") from last_error


def forest_post(
    base_url: str,
    path: str,
    body: Any = None,
    connect_timeout_ms: Optional[int] = None,
    timeout_ms: Optional[int] = None,
) -> Any:
    """发 POST（``@JSONBody``）并返回 ``json.loads`` 之后的对象。

    ``body`` 传实体时按 ``by_alias=True``（Jackson 的 camelCase）序列化；
    重试语义与 :func:`forest_get` 完全一致。
    """
    settings = get_settings()
    forest = settings.forest

    connect_timeout = (connect_timeout_ms or forest.connect_timeout) / 1000.0
    read_timeout = (timeout_ms or forest.timeout) / 1000.0
    attempts = max(0, forest.retry_count) + 1

    url = build_url(base_url, path)
    if body is not None and hasattr(body, "model_dump"):
        payload: Any = body.model_dump(by_alias=True, mode="json")
    else:
        payload = body

    last_error: Optional[Exception] = None

    for attempt in range(attempts):
        try:
            with httpx.Client(
                timeout=httpx.Timeout(read_timeout, connect=connect_timeout),
                headers=_CONNECTION_CLOSE_HEADER,
            ) as client:
                response = client.post(url, json=payload)
            return _parse_response(response, url)
        except httpx.TransportError as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            delay_ms = min(100 * (2**attempt), forest.max_retry_interval)
            time.sleep(delay_ms / 1000.0)

    raise ForestException(f"请求失败: {url} -> {last_error}") from last_error


def to_table_data_info(payload: Any) -> TableDataInfo:
    """Jackson 反序列化成 ``TableDataInfo``。

    上游返回非 JSON 对象（``null``）时 Java 得到 ``null``、随后在控制器里 NPE；
    这里退化成"空表"以免 500 —— 已登记到 ``COMPATIBILITY.md``。
    """
    info = TableDataInfo()
    if not isinstance(payload, Mapping):
        return info
    info.set_total(int(payload.get("total") or 0))
    rows = payload.get("rows")
    info.set_rows(rows if isinstance(rows, list) else None)
    code = payload.get("code")
    info.set_code(int(code) if code is not None else 0)
    info.set_msg(payload.get("msg"))
    return info


__all__ = [
    "ForestException",
    "build_url",
    "forest_get",
    "forest_post",
    "to_query_params",
    "to_table_data_info",
]
