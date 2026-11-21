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


class _ScanOnlyClient:
    """只实现 SCAN；若走到 ``KEYS`` 会直接 AssertionError."""

    def __init__(self) -> None:
        self.scan_calls: List[Tuple[Any, ...]] = []

    def scan_iter(self, match: str, count: int = 1000):
        self.scan_calls.append((match, count))
        return ["login_tokens:b", "login_tokens:a", "login_tokens:a"]

    def keys(self, *_args: Any, **_kwargs: Any) -> List[bytes]:
        raise AssertionError("RedisCache.keys must not use KEYS")


def test_keys_uses_scan_and_deduplicates() -> None:
    """keys(pattern) 必须走 SCAN 游标，不得调用阻塞的 KEYS."""
    client = _ScanOnlyClient()
    cache = RedisCache(client=client)

    assert cache.keys("login_tokens:*") == ["login_tokens:a", "login_tokens:b"]
    assert client.scan_calls == [("login_tokens:*", 1000)]
