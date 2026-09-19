"""US-21 automatic-following acceptance and scheduling boundaries (network-free)."""

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import get_session
from app.data.filing_ingestion import ingest
from app.data.filing_schedule import next_job, schedule_due
from app.main import app
from app.models import Filing, FilingSync, WatchlistEntry
from tests.test_filings import FakeSec


@contextmanager
def db():
    generator = app.dependency_overrides[get_session]()
    try:
        yield next(generator)
    finally:
        generator.close()


@pytest.fixture(autouse=True)
def sec_configured(monkeypatch):
    monkeypatch.setattr(settings, "sec_contact_email", "test@example.com")


def test_backfills_existing_manual_and_imported_holdings_without_filing_requests(client):
    client.post("/api/holdings", json={"ticker": "AAPL", "quantity": 2})
    with db() as session:
        assert schedule_due(session) == 1
        job = next_job(session)
        assert job and job.ticker == "AAPL"
        ingest(session, job, FakeSec())
        assert job.status == "ready"
    response = client.post(
        "/api/holdings/import",
        files={"file": ("positions.csv", "ticker,quantity\nMSFT,3\nAAPL,4\n", "text/csv")},
    )
    assert response.status_code == 200
    with db() as session:
        assert schedule_due(session) == 1
        assert schedule_due(session) == 0
        job = next_job(session)
        assert job and job.ticker == "MSFT"
        assert session.get(FilingSync, "AAPL").status == "ready"


def test_watch_without_holdings_ingests_and_grants_access_without_changing_risk_inputs(client):
    assert client.post("/api/watchlist", json={"ticker": " aapl "}).status_code == 201
    assert client.post("/api/watchlist", json={"ticker": "AAPL"}).status_code == 201
    assert client.get("/api/watchlist").json() == ["AAPL"]
    assert client.get("/api/holdings").json() == []
    tracked = client.get("/api/filings").json()["companies"]
    assert len(tracked) == 1 and tracked[0]["watched"] and not tracked[0]["held"]
    with db() as session:
        schedule_due(session)
        ingest(session, next_job(session), FakeSec())
    assert client.get("/api/filings/AAPL").json()["indexed_count"] == 3
    assert client.get("/api/filings/AAPL/search?q=supplier").json()
    assert client.post("/api/filings/AAPL/ingest").status_code == 429
    assert client.get("/api/holdings").json() == []
    assert client.get("/api/portfolio/summary").json()["positions"] == []


def test_overlap_removal_revokes_access_only_when_both_memberships_removed(client):
    holding = client.post("/api/holdings", json={"ticker": "AAPL", "quantity": 2}).json()
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    rows = client.get("/api/filings").json()["companies"]
    assert len(rows) == 1 and rows[0]["held"] and rows[0]["watched"]
    assert client.delete("/api/watchlist/AAPL").status_code == 204
    assert client.get("/api/filings/AAPL").status_code == 200
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    client.delete(f"/api/holdings/{holding['id']}")
    assert client.get("/api/filings/AAPL").status_code == 200
    client.delete("/api/watchlist/AAPL")
    for path in ["/api/filings/AAPL", "/api/filings/AAPL/search?q=risk"]:
        assert client.get(path).status_code == 404
    assert client.post("/api/filings/AAPL/ingest").status_code == 404


def test_accounts_have_private_lists_but_share_public_work(client):
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    with db() as session:
        assert schedule_due(session) == 1
        ingest(session, next_job(session), FakeSec())
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/register", json={"email": "second@example.com", "password": "a-second-password"}
    )
    assert client.get("/api/watchlist").json() == []
    assert client.get("/api/filings").json()["companies"] == []
    assert client.delete("/api/watchlist/AAPL").status_code == 404
    assert client.get("/api/filings/AAPL").status_code == 404
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    with db() as session:
        assert schedule_due(session) == 0
        assert session.scalar(select(func.count()).select_from(FilingSync)) == 1
    assert client.get("/api/filings/AAPL").json()["indexed_count"] == 3
    client.delete("/api/watchlist/AAPL")
    with db() as session:
        assert schedule_due(session, now=datetime.now(UTC) + timedelta(days=2)) == 1
        assert next_job(session).ticker == "AAPL"  # First account still watches it.


@pytest.mark.parametrize(
    "status,delay",
    [
        ("ready", timedelta(days=1)),
        ("failed", timedelta(hours=1)),
        ("partial", timedelta(hours=1)),
        ("unsupported", timedelta(days=7)),
    ],
)
def test_scheduling_intervals_and_cache_reuse(client, status, delay):
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    with db() as session:
        now = datetime.now(UTC)
        job = FilingSync(ticker="AAPL", status=status, updated_at=now, cik="0000000001")
        session.add(job)
        session.commit()
        assert schedule_due(session, now=now + delay - timedelta(seconds=1)) == 0
        assert schedule_due(session, now=now + delay) == 1
        session.refresh(job)
        assert job.status == "queued" and job.cik == "0000000001"
        assert schedule_due(session, now=now + timedelta(days=30)) == 0
        job.status = "running"
        session.commit()
        assert schedule_due(session, now=now + timedelta(days=30)) == 0


def test_last_removal_stops_queued_work_and_future_refresh_but_keeps_corpus(client):
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    with db() as session:
        schedule_due(session)
    client.delete("/api/watchlist/AAPL")
    with db() as session:
        assert next_job(session) is None
        assert schedule_due(session) == 0
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    with db() as session:
        provider = FakeSec()
        ingest(session, next_job(session), provider)
        assert provider.downloads == 3
        assert schedule_due(session, now=datetime.now(UTC) + timedelta(days=2)) == 1
        ingest(session, next_job(session), provider)
        assert provider.downloads == 3
    client.delete("/api/watchlist/AAPL")
    with db() as session:
        assert schedule_due(session, now=datetime.now(UTC) + timedelta(days=30)) == 0
        assert session.scalar(select(func.count()).select_from(Filing)) == 3


def test_disabled_ingestion_still_saves_watches_and_resumes_on_configuration(client, monkeypatch):
    monkeypatch.setattr(settings, "sec_contact_email", "")
    assert client.post("/api/watchlist", json={"ticker": "AAPL"}).status_code == 201
    assert not client.get("/api/filings").json()["configured"]
    with db() as session:
        assert schedule_due(session) == 0 and next_job(session) is None
        monkeypatch.setattr(settings, "sec_contact_email", "test@example.com")
        assert schedule_due(session) == 1


def test_input_validation_and_watchlist_limit(client, monkeypatch):
    for ticker in ["", "../../evil", "TOOLONGTICKER", "ZZZZZZ"]:
        assert client.post("/api/watchlist", json={"ticker": ticker}).status_code == 422
    monkeypatch.setattr("app.api.watchlist.MAX_WATCHLIST", 1)
    assert client.post("/api/watchlist", json={"ticker": "AAPL"}).status_code == 201
    assert client.post("/api/watchlist", json={"ticker": "AAPL"}).status_code == 201
    assert client.post("/api/watchlist", json={"ticker": "MSFT"}).status_code == 409
    with db() as session:
        assert session.scalar(select(func.count()).select_from(WatchlistEntry)) == 1


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/watchlist"),
        ("post", "/api/watchlist"),
        ("delete", "/api/watchlist/AAPL"),
        ("get", "/api/filings"),
    ],
)
def test_following_requires_auth(anon_client: TestClient, method, path):
    assert anon_client.request(method, path, json={"ticker": "AAPL"}).status_code == 401
