"""US-11 specifications: deterministic corpus, network boundaries and authorization."""

from datetime import date

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_session
from app.data.filing_ingestion import ingest
from app.data.sec import FilingRef, SecClient, SecError, UnsupportedIssuer
from app.engines.rag.passages import extract_passages
from app.main import app
from app.models import FilingSync

BODY = (
    "<html><head><title>Hidden title</title></head><body><h2>Item 1A. Risk Factors</h2>"
    + ("<p>Supplier concentration could interrupt manufacturing and reduce revenue.</p>" * 60)
    + "<script>steal()</script><ix:hidden>secret facts</ix:hidden></body></html>"
)


class FakeSec(SecClient):
    def __init__(self) -> None:
        self.downloads = 0
        self.fail = False

    def issuer(self, ticker: str) -> tuple[str, str]:
        if ticker == "BND":
            raise UnsupportedIssuer("No supported corporate filer matches this ticker.")
        return "0000000001", "Example issuer"

    def recent_filings(self, cik: str) -> list[FilingRef]:
        return [
            FilingRef(
                f"0000000001-26-00000{i}",
                form,
                date(2026, 9, i),
                f"https://www.sec.gov/Archives/edgar/data/1/00000000012600000{i}/report.htm",
            )
            for i, form in enumerate(["10-K", "10-Q", "8-K"], 1)
        ]

    def document(self, ref: FilingRef) -> str:
        self.downloads += 1
        if self.fail and ref.form == "10-Q":
            raise SecError("SEC is busy.")
        return BODY


def run_job(ticker: str, provider: FakeSec) -> None:
    generator = app.dependency_overrides[get_session]()
    session = next(generator)
    try:
        job = session.get(FilingSync, ticker)
        assert job is not None
        ingest(session, job, provider)
    finally:
        generator.close()


def test_extraction_excludes_active_and_hidden_content_and_preserves_offsets() -> None:
    text, passages = extract_passages(BODY)
    assert "steal" not in text and "secret" not in text and "Hidden title" not in text
    assert len(passages) > 1
    assert "Risk Factors" in passages[-1].section
    for p in passages:
        assert text[p.start : p.end] == p.text
        assert len(p.text) <= 1800
    assert passages[1].start < passages[0].end
    assert passages[-1].end == len(text)


def test_parser_handles_inline_text_entities_and_hidden_nested_elements() -> None:
    text, _ = extract_passages(
        "<p>Supply <b>chain</b> &amp; liquidity. </p>" * 10
        + '<div style="display: none"><p>hidden</p></div><p>Visible</p>'
    )
    assert "Supply chain & liquidity" in text
    assert "hidden" not in text and "Visible" in text
    with pytest.raises(ValueError):
        extract_passages("<script>not evidence</script>")


def test_ingestion_search_deduplication_and_source_identity(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "sec_contact_email", "test@example.com")
    client.post("/api/holdings", json={"ticker": "AAPL", "quantity": "1"})
    assert client.get("/api/filings/AAPL").json()["sync"]["status"] == "idle"
    assert client.post("/api/filings/AAPL/ingest").status_code == 202
    assert client.post("/api/filings/AAPL/ingest").status_code == 202
    provider = FakeSec()
    run_job("AAPL", provider)
    payload = client.get("/api/filings/AAPL").json()
    assert payload["sync"]["status"] == "ready"
    assert payload["sync"]["completed"] == payload["sync"]["total"] == 3
    assert {f["form"] for f in payload["filings"]} == {"10-K", "10-Q", "8-K"}
    hits = client.get("/api/filings/AAPL/search", params={"q": "supplier"}).json()
    assert hits and all(h["source_url"].startswith("https://www.sec.gov/") for h in hits)
    assert "Supplier" in hits[0]["text"]
    assert client.get("/api/filings/AAPL/search", params={"q": "absentphrase"}).json() == []
    assert client.post("/api/filings/AAPL/ingest").status_code == 429
    run_job("AAPL", provider)
    assert provider.downloads == 3
    assert client.get("/api/filings/AAPL").json()["indexed_count"] == 3
    # Another user cannot discover jobs or sources for the first user's holdings.
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/register", json={"email": "other@example.com", "password": "different-password"}
    )
    for path in ["/api/filings/AAPL", "/api/filings/AAPL/search?q=supplier"]:
        assert client.get(path).status_code == 404
    assert client.post("/api/filings/AAPL/ingest").status_code == 404


def test_partial_ingestion_retries_only_missing_document(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "sec_contact_email", "test@example.com")
    client.post("/api/holdings", json={"ticker": "AAPL", "quantity": "1"})
    client.post("/api/filings/AAPL/ingest")
    provider = FakeSec()
    provider.fail = True
    run_job("AAPL", provider)
    payload = client.get("/api/filings/AAPL").json()
    assert payload["sync"]["status"] == "partial"
    assert payload["sync"]["completed"] == 2
    assert payload["indexed_count"] == 2
    provider.fail = False
    run_job("AAPL", provider)
    assert provider.downloads == 4
    assert client.get("/api/filings/AAPL").json()["sync"]["status"] == "ready"


def test_unsupported_and_configuration(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "sec_contact_email", "")
    client.post("/api/holdings", json={"ticker": "BND", "quantity": "1"})
    assert client.post("/api/filings/BND/ingest").status_code == 503
    monkeypatch.setattr(settings, "sec_contact_email", "test@example.com")
    client.post("/api/filings/BND/ingest")
    run_job("BND", FakeSec())
    result = client.get("/api/filings/BND").json()
    assert result["sync"]["status"] == "unsupported"
    assert result["filings"] == []


@pytest.mark.parametrize("path", ["/api/filings/AAPL", "/api/filings/AAPL/search?q=supplier"])
def test_filing_reads_require_auth(anon_client: TestClient, path: str) -> None:
    assert anon_client.get(path).status_code == 401


def test_filing_write_requires_auth(anon_client: TestClient) -> None:
    assert anon_client.post("/api/filings/AAPL/ingest").status_code == 401


def test_deletion_revokes_filing_access(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "sec_contact_email", "test@example.com")
    holding = client.post("/api/holdings", json={"ticker": "AAPL", "quantity": "1"}).json()
    client.post("/api/filings/AAPL/ingest")
    run_job("AAPL", FakeSec())
    client.delete(f"/api/holdings/{holding['id']}")
    assert client.get("/api/filings/AAPL").status_code == 404


def test_sec_mapping_and_selection_use_exact_issuer_and_bounded_forms(monkeypatch) -> None:
    monkeypatch.setattr("app.data.sec.time.sleep", lambda _: None)
    paths = []

    def respond(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        assert "test@example.com" in request.headers["user-agent"]
        if request.url.path.endswith("company_tickers.json"):
            return httpx.Response(
                200, json={"0": {"ticker": "BRK-B", "cik_str": 1, "title": "Example"}}
            )
        return httpx.Response(
            200,
            json={
                "cik": "1",
                "filings": {
                    "recent": {
                        "accessionNumber": [f"0000000001-26-{i:06}" for i in range(10)],
                        "form": ["10-K", "10-K", "10-Q"] + ["8-K"] * 7,
                        "filingDate": [f"2026-09-{i + 1:02}" for i in range(10)],
                        "primaryDocument": ["report.htm"] * 10,
                    }
                },
            },
        )

    provider = SecClient("test@example.com", transport=httpx.MockTransport(respond))
    assert provider.issuer("BRK.B")[0] == "0000000001"
    assert provider.issuer("BRK.B")[0] == "0000000001"
    assert len(paths) == 1
    refs = provider.recent_filings("0000000001")
    assert len(refs) == 7
    assert sum(r.form == "8-K" for r in refs) == 5
    assert next(r for r in refs if r.form == "10-K").filed_on == date(2026, 9, 2)
    with pytest.raises(UnsupportedIssuer):
        provider.issuer("UNKNOWN")
    provider.close()


@pytest.mark.parametrize("status", [403, 302, 429, 503])
def test_sec_retries_are_bounded_and_no_redirects(monkeypatch, status: int) -> None:
    monkeypatch.setattr("app.data.sec.time.sleep", lambda _: None)
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status, headers={"Location": "https://evil.test/"})

    provider = SecClient("test@example.com", transport=httpx.MockTransport(respond))
    with pytest.raises(SecError):
        provider.issuer("AAPL")
    assert len(requests) == (3 if status in {429, 503} else 1)
    provider.close()


def test_size_limit_and_host_allowlist(monkeypatch) -> None:
    monkeypatch.setattr("app.data.sec.time.sleep", lambda _: None)
    provider = SecClient(
        "test@example.com",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"123456")),
    )
    with pytest.raises(SecError, match="size limit"):
        provider._get("https://www.sec.gov/test", limit=5)
    with pytest.raises(SecError, match="source"):
        provider._get("https://evil.test/test")
    provider.close()


def test_malicious_document_path_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr("app.data.sec.time.sleep", lambda _: None)
    provider = SecClient(
        "test@example.com",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "cik": "1",
                    "filings": {
                        "recent": {
                            "accessionNumber": ["0000000001-26-000001"],
                            "form": ["10-K"],
                            "filingDate": ["2026-09-01"],
                            "primaryDocument": ["../../secrets.htm"],
                        }
                    },
                },
            )
        ),
    )
    with pytest.raises(SecError, match="catalogue"):
        provider.recent_filings("0000000001")
    provider.close()


def test_interrupted_job_is_recovered_and_completed(client: TestClient, monkeypatch) -> None:
    from app.filing_worker import recover_interrupted

    monkeypatch.setattr(settings, "sec_contact_email", "test@example.com")
    client.post("/api/holdings", json={"ticker": "AAPL", "quantity": "1"})
    client.post("/api/filings/AAPL/ingest")
    generator = app.dependency_overrides[get_session]()
    session = next(generator)
    try:
        job = session.get(FilingSync, "AAPL")
        assert job is not None
        job.status = "running"
        session.commit()
        recover_interrupted(session)
        session.refresh(job)
        assert job.status == "queued"
        ingest(session, job, FakeSec())
        assert job.status == "ready"
    finally:
        generator.close()


def test_refresh_failure_preserves_existing_sources(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "sec_contact_email", "test@example.com")
    client.post("/api/holdings", json={"ticker": "AAPL", "quantity": "1"})
    client.post("/api/filings/AAPL/ingest")
    provider = FakeSec()
    run_job("AAPL", provider)

    def unavailable(cik: str) -> list[FilingRef]:
        raise SecError("SEC is busy. Please retry later.")

    monkeypatch.setattr(provider, "recent_filings", unavailable)
    run_job("AAPL", provider)
    result = client.get("/api/filings/AAPL").json()
    assert result["sync"]["status"] == "failed"
    assert result["indexed_count"] == 3
    assert client.get("/api/filings/AAPL/search?q=supplier").json()
