"""Real PostgreSQL verification. Run only against a disposable migrated test database.

APP_TEST_POSTGRES=1 pytest tests/test_filings_postgres.py
CI runs this in its disposable Compose database; normal pytest skips it.
"""

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.filings import search
from app.core.database import engine
from app.data.filing_ingestion import ingest
from app.filing_worker import LOCK_ID
from app.models import FilingSync, Holding, Portfolio, User
from tests.test_filings import FakeSec

pytestmark = pytest.mark.skipif(
    os.environ.get("APP_TEST_POSTGRES") != "1", reason="Requires disposable PostgreSQL database"
)


def test_native_index_atomic_ingestion_and_stemming() -> None:
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            job = FilingSync(ticker="QAUS11", updated_at=datetime.now(UTC))
            session.add(job)
            session.commit()
            provider = FakeSec()
            provider.fail = True
            ingest(session, job, provider)
            assert job.status == "partial" and job.completed == 2
            provider.fail = False
            ingest(session, job, provider)
            assert job.status == "ready" and job.completed == 3
            assert provider.downloads == 4
            index = session.scalar(
                text(
                    "SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_filing_passages_search'"
                )
            )
            assert index and "gin" in index
            rows = session.execute(
                text("""
                SELECT p.text, f.source_url FROM filing_passages p
                JOIN filings f ON p.accession = f.accession
                WHERE f.cik = '0000000001' AND
                to_tsvector('english', p.text) @@ plainto_tsquery('english', :q)
            """),
                {"q": "suppliers manufacturing"},
            ).all()
            assert rows and all("Supplier concentration" in row.text for row in rows)
            assert all(row.source_url.startswith("https://www.sec.gov/") for row in rows)
            owner = User(email="native-us11@example.com", password_hash="test-only")
            session.add(owner)
            session.flush()
            portfolio = Portfolio(user_id=owner.id, name="US11 test")
            session.add(portfolio)
            session.flush()
            session.add(Holding(portfolio_id=portfolio.id, ticker="QAUS11", quantity=1))
            session.flush()
            hits = search("QAUS11", owner, session, "suppliers manufacturing")
            assert hits and hits[0].accession.startswith("0000000001-")
            assert search("QAUS11", owner, session, "zzznomatch'; DROP TABLE filings; --") == []

            assert (
                session.scalar(text("SELECT count(*) FROM filings WHERE cik = '0000000001'")) == 3
            )
        finally:
            session.close()
            transaction.rollback()


def test_only_one_worker_can_hold_deployment_lock() -> None:
    # Use a test-only key so this check cannot interfere with a running worker.
    key = LOCK_ID + 100
    with engine.connect() as first, engine.connect() as second:
        try:
            assert first.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": key})
            assert not second.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": key})
        finally:
            first.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
