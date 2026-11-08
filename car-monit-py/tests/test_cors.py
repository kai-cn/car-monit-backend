"""CORS 默认拒绝未知来源的回归用例."""

from __future__ import annotations

from typing import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.settings import reset_settings_cache


@pytest.fixture(autouse=True)
def _reset_settings() -> Iterator[None]:
    reset_settings_cache()
    yield
    reset_settings_cache()


def _client() -> TestClient:
    from app.main import create_app

    return TestClient(create_app(), raise_server_exceptions=False)


def _preflight(client: TestClient, origin: str) -> httpx.Response:
    return client.options(
        "/system/user/list",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


def test_local_empty_whitelist_rejects_unknown_origin() -> None:
    response = _preflight(_client(), "http://evil.example")

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_local_empty_whitelist_allows_loopback() -> None:
    response = _preflight(_client(), "http://localhost:5173")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_configured_whitelist_replaces_the_loopback_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP__CORS__ALLOWED_ORIGINS", '["https://admin.example.com"]')
    client = _client()

    assert _preflight(client, "http://localhost:5173").status_code == 400
    allowed = _preflight(client, "https://admin.example.com")
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://admin.example.com"


def test_non_local_empty_whitelist_rejects_every_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IS_LOCALHOST", "prod")
    monkeypatch.setenv(
        "TOKEN__SECRET",
        "cHl0ZXN0LW9ubHktand0LXNpZ25pbmcta2V5LTAxMjM0NTY3ODlhYmNkZWZnaGlqa2xtbg==",
    )
    monkeypatch.setenv("SPRING__DATASOURCE__DRUID__MASTER__PASSWORD", "prod-db-password")
    monkeypatch.setenv("HENGDA__SECRET", "prod-hengda-signing-key-4d8e1a6b2f9c0357")
    client = _client()

    assert _preflight(client, "http://localhost:5173").status_code == 400
    assert _preflight(client, "https://admin.example.com").status_code == 400
