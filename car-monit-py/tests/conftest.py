"""pytest fixtures.

# Migrated from: (no Java equivalent -- JUnit + @SpringBootTest lives per-module)

Java 对照
---------
* ``@SpringBootTest(webEnvironment = RANDOM_PORT)`` + ``TestRestTemplate``
  <-> ``TestClient(create_app())``（见 :mod:`fastapi.testclient`）
* ``@BeforeEach`` 里重置 mocks <-> ``reset_settings_cache()`` / ``reset_logging()``

NOTE: ``TestClient`` 的 ``with`` 语句会触发 FastAPI 的 lifespan（等价于
Spring 容器的 refresh + shutdown），所以数据库/Redis 在用例结束后会被释放。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator

import pytest
from fastapi.testclient import TestClient

from app.logging_config import reset_logging
from app.settings import reset_settings_cache


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Boot one application instance for the whole test session."""
    # 清掉 lru_cache，保证 .env / config/application.yml 被重新读取。
    reset_settings_cache()
    reset_logging()

    from app.main import create_app

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client


class FakeRedisCache:
    """内存版 ``RedisCache``（只实现拦截器用到的两个方法）.

    ``RedisCache`` 走 JSON 序列化，取回来的对象与存进去的**不是同一个引用**；
    这里同样做一次 JSON 往返，避免测试里的"改缓存对象等于改上次判定结果"。
    """

    def __init__(self) -> None:
        #: ``key -> (value, ttl_millis)``
        self.data: Dict[str, Any] = {}
        self.writes: list = []

    def get_cache_object(self, key: str) -> Any:
        stored = self.data.get(key)
        return None if stored is None else json.loads(json.dumps(stored[0]))

    def set_cache_object_with_timeout(self, key: str, value: Any, timeout: int, unit: Any) -> None:
        ttl = unit.to_millis(timeout)
        self.writes.append((key, value, ttl))
        self.data[key] = (value, ttl)

    def set_cache_object(self, key: str, value: Any) -> None:
        self.data[key] = (value, None)


@pytest.fixture(autouse=True)
def repeat_submit_redis(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeRedisCache]:
    """给 ``SameUrlDataInterceptor`` 装一份内存 Redis（每个用例一份）.

    不装的话 ``POST /system/config`` 会真的连 Redis，而且 5 秒 TTL 会让**不同用例**
    互相污染（同一份 body 连发两次就变成"重复提交"）。同时清掉进程内单例，
    保证用例之间不共享缓存内容。
    """
    from app.framework.interceptor import repeat_submit_interceptor
    from app.framework.interceptor.impl import same_url_data_interceptor as implementation

    fake = FakeRedisCache()
    repeat_submit_interceptor.reset_interceptor()
    monkeypatch.setattr(implementation, "get_redis_cache", lambda: fake)
    yield fake
    repeat_submit_interceptor.reset_interceptor()
