"""Redis client factory.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/RedisConfig.java
# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/FastJson2JsonRedisSerializer.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/redis/RedisCache.java

Java original
-------------
* ``RedisTemplate<String, Object>`` with ``StringRedisSerializer`` for keys and
  ``FastJson2JsonRedisSerializer`` for values -> values are stored as **JSON text**.
* Lettuce pool: ``max-active=8``, ``max-idle=8``, ``min-idle=0``, ``max-wait=-1ms``.
* ``spring.redis.timeout: 10s`` is the command timeout.

Python equivalent
-----------------
* ``redis-py`` with ``decode_responses=True`` so values round-trip as the same JSON
  strings FastJson2 produced. ``pickle`` is deliberately NOT used -- it would make the
  Redis keyspace unreadable to the still-running Java instance.
* ``max_connections`` maps ``max-active``; there is no direct ``min-idle`` analogue.
"""

from __future__ import annotations

import logging
from typing import Optional

import redis
from redis.connection import ConnectionPool

from app.settings import AppSettings, get_settings

logger = logging.getLogger("app.config.redis")

_pool: Optional[ConnectionPool] = None
_client: Optional[redis.Redis] = None


def _create_pool(settings: AppSettings) -> ConnectionPool:
    section = settings.spring.redis
    return ConnectionPool(
        host=section.host,
        port=section.port,
        db=section.database,
        password=section.password or None,
        # Java: spring.redis.timeout: 10s
        socket_timeout=section.timeout_seconds,
        socket_connect_timeout=section.timeout_seconds,
        # Java: lettuce.pool.max-active: 8
        max_connections=max(1, section.pool.max_active),
        # FastJson2JsonRedisSerializer produced JSON text -> keep it human readable.
        decode_responses=True,
        health_check_interval=30,
    )


def get_redis_client() -> redis.Redis:
    """Return the process-wide Redis client (lazy; never connects on import)."""
    global _pool, _client
    if _client is None:
        settings = get_settings()
        _pool = _create_pool(settings)
        _client = redis.Redis(connection_pool=_pool)
        logger.debug(
            "Redis client created (host=%s, port=%s, db=%s)",
            settings.spring.redis.host,
            settings.spring.redis.port,
            settings.spring.redis.database,
        )
    return _client


def check_connection() -> bool:
    """Liveness probe used by ``GET /health``; never raises."""
    try:
        get_redis_client().ping()
        return True
    except Exception as exc:  # noqa: BLE001 - probe must not raise
        logger.warning("[健康检查] Redis 连接失败: %s", exc)
        return False


def close_redis() -> None:
    """Release the connection pool (FastAPI shutdown hook)."""
    global _pool, _client
    if _client is not None:
        try:
            _client.close()
        except Exception as exc:  # noqa: BLE001 - shutdown must not fail
            logger.debug("Redis close ignored: %s", exc)
    if _pool is not None:
        _pool.disconnect()
    _client = None
    _pool = None
