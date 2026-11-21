"""Forest 进程级 ``httpx.Client`` 复用用例（P2-3）."""

from __future__ import annotations

from app.base.service.forest import forest_client


def test_client_is_reused_across_calls() -> None:
    forest_client.close_http_client()
    try:
        first = forest_client.get_http_client()
        second = forest_client.get_http_client()
        assert first is second
        assert not first.is_closed
    finally:
        forest_client.close_http_client()


def test_close_releases_the_singleton() -> None:
    forest_client.close_http_client()
    client = forest_client.get_http_client()
    forest_client.close_http_client()

    assert client.is_closed
    assert forest_client.get_http_client() is not client
