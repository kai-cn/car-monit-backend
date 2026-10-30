"""``/monitor/cache`` -- 缓存监控（Redis）.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/CacheController.java

端点清单（1 个映射）
--------------------
    ==============  =======  ===================  =============
    Java             Method   Path                 Access
    ==============  =======  ===================  =============
    ``getInfo()``    GET      ``/monitor/cache``   cache:list
    ==============  =======  ===================  =============

返回体（``AjaxResult.success(Map)``，三层嵌套）
----------------------------------------------
.. code-block:: json

    {"code": 200, "msg": "操作成功", "data": {
        "info":         {"redis_version": "6.2.6", "used_memory": "1234567", ...},
        "dbSize":       17,
        "commandStats": [{"name": "get", "value": "12"}, ...]
    }}

三处容易出错的地方
------------------
1. ``info`` 是 **``Properties``**（``key -> String`` 的扁平表），**不是**嵌套结构。
   Lettuce 把 ``INFO`` 文本按首个 ``:`` 切成键值对，``# Server`` 这类段落行直接丢掉。
   所以 ``used_memory_human`` 这种带单位的键也在里面，前端只取它要的几个。
2. ``commandStats[].value`` 是**字符串**（``substringBetween("calls=", ",usec")``），
   不是数字；``name`` 已经去掉了 ``cmdstat_`` 前缀。
3. ``dbSize`` 是 **``Long``**，原样输出为数字。

为什么不用 ``client.execute_command("INFO")``
----------------------------------------------
``redis-py`` 给 ``INFO`` 注册了内置的 response callback，它会把回复**解析成嵌套
dict**（``Server`` / ``Memory`` 等子表，``cmdstat_keys`` 本身又是个 dict）——
和 Java 拿到的 ``Properties``（扁平 ``key -> String``）形状不同，``parse_info``
拿着 dict 直接崩。

Java 的 ``RedisCallback`` 走的是**裸连接**，拿到的是原始文本。这里用
:func:`_execute_raw` 复刻同一路径：借一条连接、``send_command`` + ``read_response``、
归还连接，绕开 response callback，把原始文本交给 :func:`parse_info`。

``info`` / ``commandStats`` 的**键顺序**
---------------------------------------
Java 用的是 ``java.util.Properties``（继承 ``Hashtable``），``stringPropertyNames()``
是**无序**的，所以同样一台 Redis 两次请求的键顺序可能不同。这里按 ``INFO`` 文本的
原始顺序输出 —— 内容是同一批键值，只是顺序稳定。前端按 key 取值，不受影响；
差异记在 ``COMPATIBILITY.md`` §39。

Redis 不可达时
-------------
Java 的 ``getInfo() throws Exception`` 把 ``RedisConnectionFailureException`` 交给
``GlobalExceptionHandler``，回 **HTTP 200 + code 500**。这里不 catch，
``redis.exceptions.ConnectionError`` 走的是同一条兜底路径。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.framework.web.service.permission_service import pre_authorize_permi

router = APIRouter(prefix="/monitor/cache", tags=["monitor-cache"])

#: Java: ``StringUtils.removeStart(key, "cmdstat_")`` 的前缀。
COMMAND_STATS_PREFIX = "cmdstat_"


_REDIS_CACHE: Optional[RedisCache] = None


def _redis_cache() -> RedisCache:
    global _REDIS_CACHE
    if _REDIS_CACHE is None:
        _REDIS_CACHE = get_redis_cache()
    return _REDIS_CACHE


def reset_cache_controller() -> None:
    """Test helper: drop the cached collaborator so a fake can be injected."""
    global _REDIS_CACHE
    _REDIS_CACHE = None


def _execute_raw(client: Any, *args: Any) -> Any:
    """发一条命令并取**原始**回复（不经过 ``redis-py`` 的 response callback）.

    Java: ``redisTemplate.execute((RedisCallback<Object>) connection -> ...)`` ——
    ``RedisCallback`` 拿到的就是连接层的裸回复，``INFO`` 因此是原始文本而不是
    解析后的 dict。``client.execute_command`` 会套 callback，所以这里必须自己借
    连接（见模块 docstring"为什么不用 ``client.execute_command("INFO")``"）。
    """
    pool = client.connection_pool
    # redis-py: get_connection(command_name, *keys, **options)
    connection = pool.get_connection(args[0] if args else None)
    try:
        connection.send_command(*args)
        return connection.read_response()
    finally:
        pool.release(connection)


def parse_info(text: Optional[str]) -> Dict[str, str]:
    """``INFO`` 文本 -> 扁平字典. Java: Lettuce ``Connection#info()`` -> ``Properties``.

    规则与 ``Properties`` 一致：跳过空行与 ``#`` 段落注释，按**首个** ``:``
    切分（值里还带 ``:`` 时原样保留，例如 ``redis_build_id``）。

    空白处理逐字对齐 ``Properties.load``：``LineReader`` 只跳**前导**空白
    （``skipWhiteSpace``）与值的前导空白（``valueStart++`` 循环），行尾空白**不裁**
    —— 所以 ``used_memory:1 `` 的值是 ``"1 "``。真实 ``INFO`` 输出两侧都没有
    空白，这条纯粹是为了不把 Java 的解析规则“顺手收紧”。
    """
    properties: Dict[str, str] = {}
    if not text:
        return properties
    for raw_line in text.splitlines():
        # Java: LineReader 只跳前导空白；行尾空白会留在值里
        line = raw_line.lstrip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        # Java: Properties.load0 跳过值的前导空白
        properties[key] = value.lstrip()
    return properties


def substring_between(text: Optional[str], open_token: str, close_token: str) -> Optional[str]:
    """Java: ``StringUtils.substringBetween(str, open, close)`` —— 找不到返回 ``None``."""
    if text is None:
        return None
    start = text.find(open_token)
    if start < 0:
        return None
    start += len(open_token)
    end = text.find(close_token, start)
    if end < 0:
        return None
    return text[start:end]


def build_command_stats(command_stats: Dict[str, str]) -> List[Dict[str, Optional[str]]]:
    """``cmdstat_*`` 属性表 -> 饼图数据 ``[{"name": ..., "value": ...}]``."""
    pie_list: List[Dict[str, Optional[str]]] = []
    for key, value in command_stats.items():
        # Java: StringUtils.removeStart(key, "cmdstat_") —— 没有前缀时原样返回
        name = key[len(COMMAND_STATS_PREFIX):] if key.startswith(COMMAND_STATS_PREFIX) else key
        pie_list.append({"name": name, "value": substring_between(value, "calls=", ",usec")})
    return pie_list


@router.get("", response_model=None)
@pre_authorize_permi("monitor:cache:list")
def get_info() -> AjaxResult:
    """获取缓存监控信息. Java: ``@GetMapping() public AjaxResult getInfo() throws Exception``.

    Java 用三条 ``RedisCallback`` 分别取 ``INFO`` / ``INFO commandstats`` / ``DBSIZE``；
    前两条经 :func:`_execute_raw` 走裸连接（照抄 ``RedisCallback`` 的语义，拿到原始
    文本而非 ``redis-py`` 解析后的嵌套 dict），第三条 ``DBSIZE`` 回复本来就是整数，
    用普通封装即可。
    """
    client = _redis_cache().client
    info = parse_info(_execute_raw(client, "INFO"))
    command_stats_info = parse_info(_execute_raw(client, "INFO", "commandstats"))
    db_size = client.dbsize()

    result: Dict[str, Any] = {
        "info": info,
        "dbSize": db_size,
        "commandStats": build_command_stats(command_stats_info),
    }
    return AjaxResult.success_data(result)


__all__ = [
    "router",
    "COMMAND_STATS_PREFIX",
    "get_info",
    "_execute_raw",
    "parse_info",
    "substring_between",
    "build_command_stats",
    "reset_cache_controller",
]
