"""US-12 native pgvector, FK cascade and shared-budget concurrency; disposable DB only."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.core.database import engine
from app.data.filing_embeddings import retrieve
from app.data.gemini import EMBEDDING_VERSION
from app.data.model_budget import ModelLimitError, reserve
from app.embedding_worker import LOCK_ID
from app.models import FilingPassage, ModelBudget, PassageEmbedding
from tests.test_questions import VECTOR, seed

pytestmark = pytest.mark.skipif(
    os.environ.get("APP_TEST_POSTGRES") != "1", reason="Requires disposable PostgreSQL database"
)


def test_native_cosine_ranking_issuer_version_and_cascade():
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            first = seed(session)
            second = seed(session, accession="0000000001-26-000002")
            seed(session, cik="0000000002", accession="0000000002-26-000001")
            seed(session, accession="0000000001-26-000003", version="old-version")
            embedding = session.get(PassageEmbedding, (second, EMBEDDING_VERSION))
            embedding.vector = [-1.0] + [0.0] * 767
            session.commit()
            rows = retrieve(session, "0000000001", EMBEDDING_VERSION, VECTOR)
            assert [r.passage.id for r in rows] == [first, second]
            assert (
                session.scalar(text("SELECT vector_dims(vector) FROM passage_embeddings LIMIT 1"))
                == 768
            )
            session.execute(delete(FilingPassage).where(FilingPassage.id == first))
            session.commit()
            assert (
                session.scalar(select(PassageEmbedding).where(PassageEmbedding.passage_id == first))
                is None
            )
        finally:
            session.close()
            transaction.rollback()


def test_native_budget_allows_only_one_concurrent_reservation():
    scope = "qa-native-concurrency"
    now = datetime(2026, 9, 26, tzinfo=UTC)

    def attempt(_):
        with Session(engine) as session:
            try:
                reserve(session, scope, daily=1, seconds=30, now=now)
                return True
            except ModelLimitError:
                return False

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(attempt, range(2))) == [False, True]
    finally:
        with Session(engine) as session:
            session.execute(delete(ModelBudget).where(ModelBudget.scope == scope))
            session.commit()


def test_only_one_embedding_worker_can_claim_the_queue():
    key = LOCK_ID + 100
    with engine.connect() as first, engine.connect() as second:
        try:
            assert first.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": key})
            assert not second.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": key})
        finally:
            first.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})


def test_native_local_windows_rank_by_best_window_and_preserve_remote_index():
    from app.data.filing_embeddings import coverage
    from app.data.local_embeddings import LOCAL_VERSION
    from app.models import LocalPassageWindow

    vector = [1.0] + [0.0] * 383
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            first = seed(session)
            second = seed(session, accession="0000000001-26-000002")
            other = seed(session, cik="0000000002", accession="0000000002-26-000001")
            for pid, version, ordinal, values in [
                (first, LOCAL_VERSION, 0, [-v for v in vector]),
                (first, LOCAL_VERSION, 1, vector),
                (second, LOCAL_VERSION, 0, [-v for v in vector]),
                (other, LOCAL_VERSION, 0, vector),
                (second, "old-local-version", 0, vector),
            ]:
                session.add(
                    LocalPassageWindow(
                        passage_id=pid,
                        version=version,
                        ordinal=ordinal,
                        start_offset=0,
                        end_offset=10,
                        vector=values,
                    )
                )
            session.commit()
            rows = retrieve(session, "0000000001", LOCAL_VERSION, vector)
            assert [row.passage.id for row in rows] == [first, second]
            assert coverage(session, "0000000001", LOCAL_VERSION) == (2, 2)
            assert coverage(session, "0000000001", EMBEDDING_VERSION) == (2, 2)
            assert (
                session.scalar(
                    text("SELECT vector_dims(vector) FROM local_passage_windows LIMIT 1")
                )
                == 384
            )
            session.execute(delete(FilingPassage).where(FilingPassage.id == first))
            session.commit()
            assert (
                list(
                    session.scalars(
                        select(LocalPassageWindow).where(LocalPassageWindow.passage_id == first)
                    )
                )
                == []
            )
            assert coverage(session, "0000000001", LOCAL_VERSION) == (1, 1)
            assert coverage(session, "0000000001", EMBEDDING_VERSION) == (1, 1)
        finally:
            session.close()
            transaction.rollback()
