"""``RedisCache`` 的批量删除边界（Redis ``DEL`` 不接受空参数）."""

from __future__ import annotations

from typing import Any, List, Tuple

from app.common.core.redis.redis_cache import RedisCache


class _FakeClient:
    def __init__(self) -> None:
        self.delete_calls: List[Tuple[Any, ...]] = []

    def delete(self, *keys: Any) -> int:
        self.delete_calls.append(keys)
        return len(keys)


def test_delete_object_with_an_empty_collection_skips_del() -> None:
    """``DEL`` 不带键会报 "wrong number of arguments"；空集合应直接返回 False."""
    client = _FakeClient()
    cache = RedisCache(client=client)

    assert cache.delete_object([]) is False
    assert cache.delete_object(()) is False
    assert cache.delete_object(set()) is False
    assert client.delete_calls == []


def test_delete_object_with_keys_issues_one_del() -> None:
    client = _FakeClient()
    cache = RedisCache(client=client)

    assert cache.delete_object(["a", "b"]) is True
    assert client.delete_calls == [("a", "b")]
