"""spring redis 工具类 / Redis helper bean.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/redis/RedisCache.java

Java original
-------------
``@Component`` wrapping ``@Autowired RedisTemplate redisTemplate`` (raw type, so every
value goes through ``FastJson2JsonRedisSerializer``). All methods are ``<T>`` generic and
return whatever the serializer restored.

Python equivalent
-----------------
A class holding a ``redis.Redis`` client plus one
:class:`~app.framework.config.fast_json2_json_redis_serializer.FastJson2JsonRedisSerializer`
instance, exposed through :func:`get_redis_cache` (process-wide singleton, mirroring
Spring's default singleton scope).

Two Java behaviours that are easy to get wrong:

* ``redisTemplate.delete(key)`` returns ``boolean`` while ``expire`` also returns
  ``boolean``; Python's ``redis-py`` returns ``int`` counts. Both are coerced to ``bool``
  so that call sites such as ``if (redisCache.hasKey(key))`` keep working.
* ``setCacheObject(key, value)`` (2-arg) stores with **no TTL**, while the 4-arg overload
  requires a TTL. ``TokenService.refreshToken`` uses the 4-arg form with
  ``expireTime`` minutes -- losing the TTL would make sessions immortal.

``keys(pattern)`` deviates from Java deliberately: Spring Data Redis uses ``KEYS``, an
O(N) command that blocks the whole server; this implementation uses ``SCAN`` incremental
iteration instead, de-duplicates keys and sorts the result (see the method docstring).
"""

from __future__ import annotations

from typing import Any, Collection, Dict, List, Optional, Set

import redis

from app.common.utils.time_unit import TimeUnit
from app.config.redis_config import get_redis_client
from app.framework.config.fast_json2_json_redis_serializer import FastJson2JsonRedisSerializer


class RedisCache:
    """Java: ``RedisCache``."""

    def __init__(self, client: Optional[redis.Redis] = None) -> None:
        self._client = client
        self._serializer = FastJson2JsonRedisSerializer()

    @property
    def client(self) -> redis.Redis:
        """Java: ``public RedisTemplate redisTemplate`` (lazily resolved)."""
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    # ------------------------------------------------------------------ value ops

    # Java: public <T> void setCacheObject(String key, T value)
    def set_cache_object(self, key: str, value: Any) -> None:
        self.client.set(key, self._serializer.serialize(value))

    # Java: public <T> void setCacheObject(String key, T value, Integer timeout, TimeUnit unit)
    def set_cache_object_with_timeout(self, key: str, value: Any, timeout: int, unit: TimeUnit) -> None:
        self.client.set(key, self._serializer.serialize(value), px=unit.to_millis(timeout))

    # Java: public <T> Boolean setCacheObjectIfAbsent(String key, T value, long timeout, TimeUnit unit)
    def set_cache_object_if_absent(self, key: str, value: Any, timeout: int, unit: TimeUnit) -> bool:
        return bool(self.client.set(key, self._serializer.serialize(value), px=unit.to_millis(timeout), nx=True))

    # Java: public <T> T getCacheObject(String key)
    def get_cache_object(self, key: str) -> Any:
        return self._serializer.deserialize(self.client.get(key))

    # Java: public boolean deleteObject(String key)
    def delete_object(self, key: Any) -> bool:
        """Delete one key or a collection of keys.

        Java overloads ``deleteObject(String)`` and ``deleteObject(Collection)``; Python
        dispatches on the runtime type (same convention as ``StringUtils.isEmpty`` in
        :mod:`app.common.utils.string_utils`).
        """
        if isinstance(key, (list, tuple, set, frozenset)):
            return self._delete_many(key)
        return bool(self.client.delete(key))

    def _delete_many(self, keys: Collection[Any]) -> bool:
        """Java: ``return redisTemplate.delete(collection) > 0;``"""
        return self.client.delete(*keys) > 0

    # ------------------------------------------------------------------ key ops

    # Java: public boolean expire(String key, long timeout)  -> SECONDS
    def expire(self, key: str, timeout: int, unit: TimeUnit = TimeUnit.SECONDS) -> bool:
        return bool(self.client.pexpire(key, unit.to_millis(timeout)))

    # Java: public long getExpire(String key)
    def get_expire(self, key: str) -> int:
        """Remaining TTL **in seconds** (Spring's default ``getExpire`` unit).

        ``redis-py`` returns ``-2`` for a missing key and ``-1`` for a key without TTL --
        the same sentinels Spring uses.
        """
        return self.client.ttl(key)

    # Java: public Boolean hasKey(String key)
    def has_key(self, key: str) -> bool:
        return bool(self.client.exists(key))

    # Java: public Collection<String> keys(String pattern)
    def keys(self, pattern: str) -> List[str]:
        """用 ``SCAN`` 取代 ``KEYS``：语义等价，但不会阻塞整个 Redis。

        ``KEYS`` 在百万级 keyspace 上会持有单线程事件循环数百毫秒到数秒，
        ``/monitor/online``、字典缓存刷新等调用会直接拖垮所有并发请求。
        ``SCAN`` 是游标增量遍历，代价是极端情况下可能返回重复键，
        这里用 ``set`` 去重（顺序本来就和 Java 的 ``Set`` 一样不保证）。
        """
        return sorted({str(key) for key in self.client.scan_iter(match=pattern, count=1000)})

    # ------------------------------------------------------------------ list ops

    # Java: public <T> long setCacheList(String key, List<T> dataList)
    def set_cache_list(self, key: str, data_list: List[Any]) -> int:
        if not data_list:
            return 0
        count = self.client.rpush(key, *[self._serializer.serialize(item) for item in data_list])
        return int(count or 0)

    # Java: public <T> List<T> getCacheList(String key)
    def get_cache_list(self, key: str) -> List[Any]:
        return [self._serializer.deserialize(item) for item in self.client.lrange(key, 0, -1)]

    # ------------------------------------------------------------------ set ops

    # Java: public <T> BoundSetOperations<String, T> setCacheSet(String key, Set<T> dataSet)
    def set_cache_set(self, key: str, data_set: Set[Any]) -> int:
        """Add every member; returns the number added.

        Java returns the ``BoundSetOperations`` handle (used only for further command
        chaining, which this project never does), so the member count is returned instead.
        """
        if not data_set:
            return 0
        return int(self.client.sadd(key, *[self._serializer.serialize(item) for item in data_set]) or 0)

    # Java: public <T> Set<T> getCacheSet(String key)
    def get_cache_set(self, key: str) -> Set[Any]:
        return {self._serializer.deserialize(item) for item in self.client.smembers(key)}

    # ------------------------------------------------------------------ hash ops

    # Java: public <T> void setCacheMap(String key, Map<String, T> dataMap)
    def set_cache_map(self, key: str, data_map: Optional[Dict[str, Any]]) -> None:
        # Java: if (dataMap != null) { ... }
        if data_map is not None:
            self.client.hset(key, mapping=self._serialize_map(data_map))

    # Java: public <T> Map<String, T> getCacheMap(String key)
    def get_cache_map(self, key: str) -> Dict[str, Any]:
        return {h_key: self._serializer.deserialize(value) for h_key, value in self.client.hgetall(key).items()}

    # Java: public <T> void setCacheMapValue(String key, String hKey, T value)
    def set_cache_map_value(self, key: str, h_key: str, value: Any) -> None:
        self.client.hset(key, h_key, self._serializer.serialize(value))

    # Java: public <T> T getCacheMapValue(String key, String hKey)
    def get_cache_map_value(self, key: str, h_key: str) -> Any:
        return self._serializer.deserialize(self.client.hget(key, h_key))

    # Java: public <T> List<T> getMultiCacheMapValue(String key, Collection<Object> hKeys)
    def get_multi_cache_map_value(self, key: str, h_keys: Collection[Any]) -> List[Any]:
        if not h_keys:
            return []
        return [self._serializer.deserialize(item) for item in self.client.hmget(key, list(h_keys))]

    # Java: public boolean deleteCacheMapValue(String key, String hKey)
    def delete_cache_map_value(self, key: str, h_key: str) -> bool:
        return int(self.client.hdel(key, h_key) or 0) > 0

    # ------------------------------------------------------------------ helpers

    def _serialize_map(self, data_map: Dict[str, Any]) -> Dict[str, str]:
        return {key: self._serializer.serialize(value) for key, value in data_map.items()}


_CACHE: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Process-wide ``RedisCache`` (Spring's default singleton scope)."""
    global _CACHE
    if _CACHE is None:
        _CACHE = RedisCache()
    return _CACHE


def reset_redis_cache() -> None:
    """Test helper: drop the cached bean so a fake client can be injected."""
    global _CACHE
    _CACHE = None


__all__ = ["RedisCache", "get_redis_cache", "reset_redis_cache"]
