"""Local provider contract, atomic preparation and grounded Q&A without hosted embeddings."""

import json

import httpx
import pytest
from sqlalchemy import delete, select

from app.core.config import Settings, settings
from app.data.filing_embeddings import coverage, prepare_batch, retrieve
from app.data.local_embeddings import LOCAL_VERSION, LocalEmbeddings
from app.data.question_factory import create_embedding_provider
from app.data.question_provider import EmbeddedWindow, ModelError
from app.models import (
    FilingPassage,
    LocalPassageWindow,
    ModelBudget,
    PassageEmbedding,
    WatchlistEntry,
)
from tests.test_questions import QUOTE, ask, db, seed
from tests.test_questions import questions as question_fixture

questions = question_fixture

LOCAL_VECTOR = [1.0] + [0.0] * 383


def adapter(handler):
    return LocalEmbeddings("http://encoder:8081", transport=httpx.MockTransport(handler))


def response(**values):
    return httpx.Response(200, json={"version": LOCAL_VERSION, **values})


def test_windowed_documents_send_exact_source_slices_and_query_flag():
    calls = []
    text = "risk " * 1000

    def handler(request):
        body = json.loads(request.content)
        calls.append((request.url.path, body))
        if request.url.path == "/windows":
            return response(windows=[[0, 2200], [2100, 4200], [4100, len(text)]])
        return response(vectors=[LOCAL_VECTOR for _ in body["texts"]])

    provider = adapter(handler)
    try:
        windows = provider.embed_passage(text)
        assert [(w.start, w.end) for w in windows] == [(0, 2200), (2100, 4200), (4100, 5000)]
        assert calls[1][1] == {
            "texts": [text[w.start : w.end] for w in windows],
            "query": False,
        }
        assert provider.embed(["What risks?"], query=True) == [LOCAL_VECTOR]
        assert calls[-1][1]["query"] is True
    finally:
        provider.close()


@pytest.mark.parametrize(
    "windows",
    [
        [],
        [[0, 3]],
        [[1, 4]],
        [[0, 2], [3, 4]],
        [[0, 4], [0, 4]],
        [[-1, 4]],
        [[0, 5]],
        [[False, 4]],
        [[0, "4"]],
        [[0, 4, 1]],
        None,
    ],
)
def test_rejects_incomplete_or_malformed_windows_without_embedding(windows):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return response(windows=windows)

    provider = adapter(handler)
    with pytest.raises(ModelError):
        provider.embed_passage("risk")
    assert calls == ["/windows"]
    provider.close()


@pytest.mark.parametrize(
    "vectors", [[], [[0] * 384], [[True] * 384], [[1.0] * 383], [[2.0] * 384], None]
)
def test_rejects_invalid_vectors(vectors):
    provider = adapter(lambda _: response(vectors=vectors))
    with pytest.raises(ModelError):
        provider.embed(["risk"])
    provider.close()


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(503, text="private details"),
        httpx.Response(429, text="private details"),
        httpx.Response(302, headers={"Location": "https://other.example"}),
        httpx.Response(200, json={"version": "other", "vectors": [LOCAL_VECTOR]}),
        httpx.Response(200, content=b"x" * 100_001),
        httpx.Response(200, content=b"invalid json"),
    ],
)
def test_service_errors_are_sanitized_not_evidence_abstentions(reply):
    provider = adapter(lambda _: reply)
    with pytest.raises(ModelError) as error:
        provider.embed(["risk"])
    assert "private details" not in str(error.value)
    provider.close()


def test_network_timeout_is_sanitized():
    def handler(request):
        raise httpx.ReadTimeout("internal URL", request=request)

    provider = adapter(handler)
    with pytest.raises(ModelError, match="could not complete"):
        provider.embed(["risk"])
    provider.close()


def test_local_preparation_is_independent_of_generator_key(monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "local")
    monkeypatch.setattr(settings, "qa_enabled", True)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert settings.embedding_configured and not settings.qa_configured
    provider = create_embedding_provider()
    assert isinstance(provider, LocalEmbeddings)
    provider.close()
    assert Settings(_env_file=None).embedding_provider == "gemini"


def localize(fake):
    fake.local_embeddings = True
    fake.embedding_version = LOCAL_VERSION
    fake.embed = lambda texts, query=False: [LOCAL_VECTOR for _ in texts]
    fake.embed_passage = lambda text: [
        EmbeddedWindow(0, len(text), LOCAL_VECTOR),
        EmbeddedWindow(5, len(text), LOCAL_VECTOR),
    ]
    return fake


def test_atomic_local_preparation_counts_parents_reuses_and_preserves_remote(client, questions):
    localize(questions)
    with db() as session:
        assert prepare_batch(session, questions) == 1
        assert prepare_batch(session, questions) == 0
        assert coverage(session, "0000000001", LOCAL_VERSION) == (1, 1)
        assert len(list(session.scalars(select(LocalPassageWindow)))) == 2
        assert len(list(session.scalars(select(PassageEmbedding)))) == 2
        assert coverage(session, "0000000002", LOCAL_VERSION) == (1, 0)
        assert list(session.scalars(select(ModelBudget))) == []
        rows = retrieve(session, "0000000001", LOCAL_VERSION, LOCAL_VECTOR)
        assert len(rows) == 1 and rows[0].passage.text == QUOTE
        assert retrieve(session, "0000000002", LOCAL_VERSION, LOCAL_VECTOR) == []


def test_local_failure_keeps_passage_missing_and_retryable(client, questions):
    localize(questions)
    original = questions.embed_passage

    def fail(text):
        raise ModelError("Busy")

    questions.embed_passage = fail
    with db() as session:
        with pytest.raises(ModelError):
            prepare_batch(session, questions)
        assert coverage(session, "0000000001", LOCAL_VERSION) == (1, 0)
        questions.embed_passage = original
        assert prepare_batch(session, questions) == 1


@pytest.mark.parametrize("change", ["text", "untracked"])
def test_local_worker_rechecks_source_and_tracking_after_inference(client, questions, change):
    localize(questions)
    original = questions.embed_passage

    def modified(text):
        with db() as other:
            if change == "text":
                passage = other.scalar(select(FilingPassage).order_by(FilingPassage.id))
                passage.text = "Replacement"
            else:
                other.execute(delete(WatchlistEntry))
            other.commit()
        return original(text)

    questions.embed_passage = modified
    with db() as session:
        prepare_batch(session, questions)
        assert coverage(session, "0000000001", LOCAL_VERSION) == (1, 0)


def test_local_api_answer_keeps_original_citations_and_no_embedding_budget(
    client, questions, monkeypatch
):
    monkeypatch.setattr(settings, "embedding_provider", "local")
    localize(questions)
    with db() as session:
        prepare_batch(session, questions)
    assert client.get("/api/filings/AAPL/questions/status").json()["ready"]
    result = ask(client)
    assert result.status_code == 200, result.text
    citation = result.json()["claims"][0]["citations"][0]
    assert citation["quote"] == QUOTE
    assert citation["start_offset"] == 0 and citation["end_offset"] == len(QUOTE)
    with db() as session:
        assert session.get(ModelBudget, "embeddings") is None
        assert session.get(ModelBudget, "generation").calls == 2


def test_busy_query_does_not_consume_user_allowance(client, questions):
    localize(questions)
    with db() as session:
        prepare_batch(session, questions)

    def fail(*args, **kwargs):
        raise ModelError("Local preparation busy")

    questions.embed = fail
    assert ask(client).status_code == 503
    with db() as session:
        assert list(session.scalars(select(ModelBudget))) == []


def test_local_rank_uses_best_window_and_deduplicates_passages(client, questions):
    localize(questions)
    with db() as session:
        prepare_batch(session, questions)
        second = seed(session, accession="0000000001-26-000003", embedded=False)
        session.add(
            LocalPassageWindow(
                passage_id=second,
                version=LOCAL_VERSION,
                ordinal=0,
                start_offset=0,
                end_offset=len(QUOTE),
                vector=[-1.0] + [0.0] * 383,
            )
        )
        session.commit()
        rows = retrieve(session, "0000000001", LOCAL_VERSION, LOCAL_VECTOR)
        assert len(rows) == 2 and rows[-1].passage.id == second
