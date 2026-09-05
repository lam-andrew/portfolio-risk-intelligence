"""Tests for the health endpoint — the Sprint 1 skeleton's end-to-end contract check.

The database connectivity check is stubbed so these tests exercise the API contract without
requiring a running PostgreSQL instance (that path is covered by integration/CI runs).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health_ok_when_db_connected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.routes.check_database", lambda: True)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["service"]
    assert body["version"]


def test_health_reports_db_unavailable_without_failing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Backend stays up (200) even when the database is unreachable.
    monkeypatch.setattr("app.api.routes.check_database", lambda: False)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"


def test_health_reports_market_data_configuration(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The key is optional: /health reports whether market data (US-4) is configured."""
    monkeypatch.setattr("app.api.routes.check_database", lambda: True)

    monkeypatch.setattr("app.api.routes.settings.market_data_api_key", "")
    assert client.get("/api/health").json()["market_data"] == "unconfigured"

    monkeypatch.setattr("app.api.routes.settings.market_data_api_key", "a-test-token")
    assert client.get("/api/health").json()["market_data"] == "configured"


def test_the_api_is_namespaced_under_api(anon_client: TestClient) -> None:
    """The whole contract lives under /api, and the root is left free.

    This is what allows the built frontend and the API to be served from one origin in
    production. Without the prefix a page route and an API route compete for the same path
    — ``/holdings`` was already both — and a browser asking for the page is handed JSON.

    Serving both from one origin is also what keeps the session cookie same-site. Two Fly
    apps would sit on different registrable domains under ``fly.dev``, which is on the
    Public Suffix List, so a ``SameSite=Lax`` cookie would not travel between them and the
    only fix would be weakening it to ``SameSite=None`` (ADR 0017).
    """
    assert anon_client.get("/api/health").status_code == 200
    # The root namespace belongs to the frontend, so nothing of ours answers there.
    assert anon_client.get("/health").status_code == 404
    assert anon_client.get("/holdings").status_code == 404
