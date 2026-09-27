"""US-12 system specifications: authenticated retrieval, citations and safe failures."""

from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.api.questions import get_question_provider
from app.core.config import settings
from app.core.database import get_session
from app.data.filing_embeddings import coverage, prepare_batch, retrieve
from app.data.gemini import EMBEDDING_VERSION
from app.data.model_budget import ModelLimitError, pause, reserve
from app.data.question_provider import ModelError
from app.engines.rag.grounding import AnswerDraft, GroundingVerdict
from app.main import app
from app.models import Filing, FilingPassage, FilingSync, PassageEmbedding, User, WatchlistEntry

QUOTE = "We rely on a single supplier for certain components."
VECTOR = [1.0] + [0.0] * 767


@contextmanager
def db():
    gen = app.dependency_overrides[get_session]()
    try:
        yield next(gen)
    finally:
        gen.close()


class FakeQuestions:
    embedding_version = EMBEDDING_VERSION
    model = "offline-test-model"

    def __init__(self):
        self.calls = []
        self.status = "answered"
        self.supported = True
        self.bad_id = False
        self.failure = None
        self.on_answer = None

    def embed(self, texts, *, query=False):
        self.calls.append(("embed", list(texts), query))
        if self.failure:
            raise self.failure
        return [VECTOR for _ in texts]

    def answer(self, question, passages):
        self.calls.append(("answer", question, passages))
        if self.on_answer:
            self.on_answer()
        return AnswerDraft.model_validate(
            {
                "status": self.status,
                "claims": []
                if self.status == "insufficient_evidence"
                else [
                    {
                        "text": "The company depends on a single supplier for some components.",
                        "evidence": [
                            {
                                "passage_id": 99999 if self.bad_id else passages[0].passage_id,
                                "quote": QUOTE,
                            }
                        ],
                    }
                ],
            }
        )

    def verify(self, question, passages, draft):
        self.calls.append(("verify", question, passages))
        return GroundingVerdict.model_validate(
            {
                "answers_question": self.supported,
                "claims": [{"claim_index": 0, "supported": self.supported}],
            }
        )

    def close(self):
        pass


def seed(
    session,
    *,
    cik="0000000001",
    accession="0000000001-26-000001",
    text=QUOTE,
    embedded=True,
    version=EMBEDDING_VERSION,
):
    session.add(
        Filing(
            accession=accession,
            cik=cik,
            form="10-K",
            filed_on=date(2026, 9, 1),
            source_url=(
                f"https://www.sec.gov/Archives/edgar/data/1/{accession.replace('-', '')}/a.htm"
            ),
            text=text,
            text_sha256="a" * 64,
            parser_version="html-text-v1",
            passage_count=1,
            indexed_at=datetime.now(UTC),
        )
    )
    session.flush()
    passage = FilingPassage(
        accession=accession,
        ordinal=0,
        section="Item 1A. Risk factors",
        start_offset=0,
        end_offset=len(text),
        text=text,
    )
    session.add(passage)
    session.flush()
    if embedded:
        session.add(PassageEmbedding(passage_id=passage.id, version=version, vector=VECTOR))
    session.commit()
    return passage.id


@pytest.fixture()
def questions(client, monkeypatch):
    monkeypatch.setattr(settings, "qa_enabled", True)
    monkeypatch.setattr(settings, "gemini_api_key", "test-only")
    fake = FakeQuestions()
    app.dependency_overrides[get_question_provider] = lambda: fake
    with db() as session:
        owner = session.scalar(select(User))
        session.add(WatchlistEntry(user_id=owner.id, ticker="AAPL"))
        session.add(
            FilingSync(
                ticker="AAPL", cik="0000000001", status="ready", updated_at=datetime.now(UTC)
            )
        )
        seed(session)
        seed(
            session,
            cik="0000000002",
            accession="0000000002-26-000001",
            text="Different issuer; never disclose this passage in the AAPL answer.",
        )
    return fake


def ask(client, question="What supplier risks does the company disclose?"):
    return client.post("/api/filings/AAPL/questions", json={"question": question})


def test_answer_links_exact_evidence_for_only_selected_company(client, questions):
    status = client.get("/api/filings/AAPL/questions/status").json()
    assert status == {"configured": True, "total_passages": 1, "ready_passages": 1, "ready": True}
    response = ask(client)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "answered"
    citation = result["claims"][0]["citations"][0]
    assert citation["accession"] == "0000000001-26-000001"
    assert citation["quote"] == QUOTE
    assert citation["start_offset"] == 0 and citation["end_offset"] == len(QUOTE)
    assert "www.sec.gov/Archives/" in citation["source_url"]
    assert [c[0] for c in questions.calls] == ["embed", "answer", "verify"]
    assert len(questions.calls[1][2]) == 1
    assert "filed 2026-09-01" in questions.calls[1][2][0].source_label


@pytest.mark.parametrize("mode", ["abstain", "bad_id", "unsupported_claim"])
def test_withholds_unsupported_claims_without_fake_sources(client, questions, mode):
    if mode == "abstain":
        questions.status = "insufficient_evidence"
    elif mode == "bad_id":
        questions.bad_id = True
    else:
        questions.supported = False
    result = ask(client).json()
    assert result["status"] == "insufficient_evidence"
    assert result["claims"] == [] and "couldn't find" in result["message"]
    assert len(questions.calls) == (3 if mode == "unsupported_claim" else 2)


def test_unauthenticated_requests_rejected(anon_client):
    assert anon_client.get("/api/filings/AAPL/questions/status").status_code == 401
    assert ask(anon_client).status_code == 401


def test_other_user_and_untracked_ticker_do_not_reach_provider(client, questions):
    assert (
        client.post("/api/filings/MSFT/questions", json={"question": "What risks?"}).status_code
        == 404
    )
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/register", json={"email": "other@example.com", "password": "other-password"}
    )
    assert ask(client).status_code == 404
    assert questions.calls == []


@pytest.mark.parametrize("question", ["   ", "x" * 1001])
def test_invalid_question_has_no_provider_calls(client, questions, question):
    assert ask(client, question).status_code == 422
    assert questions.calls == []


def test_pending_embeddings_and_version_mismatch_stop_before_provider(client, questions):
    with db() as session:
        session.execute(delete(PassageEmbedding))
        session.commit()
    result = client.get("/api/filings/AAPL/questions/status").json()
    assert not result["ready"] and result["ready_passages"] == 0
    assert ask(client).status_code == 409
    assert questions.calls == []


@pytest.mark.parametrize(
    "error,code",
    [(ModelError("Service unavailable"), 503), (ModelLimitError("Free quota reached"), 429)],
)
def test_provider_outage_is_not_an_evidence_abstention(client, questions, error, code):
    questions.failure = error
    response = ask(client)
    assert response.status_code == code
    assert "status" not in response.json()
    assert len(questions.calls) == 1


def test_repeated_question_is_rate_limited(client, questions):
    assert ask(client).status_code == 200
    assert ask(client).status_code == 429
    assert len(questions.calls) == 3


def test_watch_removed_during_generation_revokes_response(client, questions):
    def remove():
        with db() as session:
            session.execute(delete(WatchlistEntry))
            session.commit()

    questions.on_answer = remove
    assert ask(client).status_code == 404


def test_disabled_configuration_keeps_cached_sources_available(client, questions, monkeypatch):
    app.dependency_overrides.pop(get_question_provider)
    monkeypatch.setattr(settings, "qa_enabled", False)
    assert ask(client).status_code == 503
    assert client.get("/api/filings/AAPL").status_code == 200
    assert not client.get("/api/filings/AAPL/questions/status").json()["configured"]


def test_worker_prepares_only_tracked_issuer_resumes_and_reuses(client, questions):
    with db() as session:
        session.execute(delete(PassageEmbedding))
        session.commit()
        assert prepare_batch(session, questions) == 1
        assert prepare_batch(session, questions) == 0
        assert coverage(session, "0000000001", EMBEDDING_VERSION) == (1, 1)
        assert coverage(session, "0000000002", EMBEDDING_VERSION) == (1, 0)
        assert coverage(session, "0000000001", "future-version") == (1, 0)
        assert retrieve(session, "0000000002", EMBEDDING_VERSION, VECTOR) == []
        session.execute(delete(WatchlistEntry))
        session.execute(delete(PassageEmbedding))
        session.commit()
        assert prepare_batch(session, questions) == 0


def test_worker_failure_keeps_missing_batch_resumable(client, questions):
    with db() as session:
        session.execute(delete(PassageEmbedding))
        session.commit()
        questions.failure = ModelLimitError("Quota")
        with pytest.raises(ModelLimitError):
            prepare_batch(session, questions)
        assert coverage(session, "0000000001", EMBEDDING_VERSION) == (1, 0)


def test_budget_survives_new_sessions_and_resets_next_day(client):
    now = datetime(2026, 9, 26, tzinfo=UTC)
    with db() as session:
        reserve(session, "test", daily=2, seconds=30, now=now)
    with db() as session:
        with pytest.raises(ModelLimitError):
            reserve(session, "test", daily=2, seconds=30, now=now)
        reserve(session, "test", daily=2, seconds=30, now=now + timedelta(seconds=31))
        with pytest.raises(ModelLimitError):
            reserve(session, "test", daily=2, seconds=30, now=now + timedelta(minutes=2))
        reserve(session, "test", daily=2, seconds=30, now=now + timedelta(days=1))


@pytest.mark.parametrize(
    "url",
    [
        "http://www.sec.gov/Archives/edgar/data/1/a.htm",
        "https://www.sec.gov.evil.example/Archives/edgar/data/1/a.htm",
        "https://evil.example/Archives/edgar/data/1/a.htm",
        "https://www.sec.gov/unrelated/a.htm",
    ],
)
def test_untrusted_source_url_never_reaches_answer(client, questions, url):
    with db() as session:
        filing = session.get(Filing, "0000000001-26-000001")
        filing.source_url = url
        session.commit()
    response = ask(client)
    assert response.status_code == 503
    assert "claims" not in response.json()
    assert url not in response.text


@pytest.mark.parametrize(
    "error,code",
    [(ModelError("Verifier unavailable"), 503), (ModelLimitError("Verifier quota"), 429)],
)
def test_verifier_failure_never_releases_unverified_draft(client, questions, error, code):
    def fail(*args):
        raise error

    questions.verify = fail
    response = ask(client)
    assert response.status_code == code
    assert "claims" not in response.json()
    assert "single supplier" not in response.text
    if code == 429:
        with db() as session, pytest.raises(ModelLimitError):
            reserve(session, "generation", daily=40, seconds=0)


def test_worker_discards_embedding_if_source_changes_during_remote_call(client, questions):
    def replace_source(texts, *, query=False):
        with db() as other:
            passage = other.scalar(
                select(FilingPassage).where(FilingPassage.accession == "0000000001-26-000001")
            )
            passage.text = "A replacement passage that needs its own embedding."
            other.commit()
        return [VECTOR for _ in texts]

    questions.embed = replace_source
    with db() as session:
        session.execute(delete(PassageEmbedding))
        session.commit()
        prepare_batch(session, questions)
        assert coverage(session, "0000000001", EMBEDDING_VERSION) == (1, 0)


def test_provider_pause_survives_sessions_then_allows_retry(client):
    with db() as session:
        reserve(session, "generation", daily=40, seconds=0)
        pause(session, "generation")
    with db() as session:
        with pytest.raises(ModelLimitError):
            reserve(session, "generation", daily=40, seconds=0)
        reserve(
            session,
            "generation",
            daily=40,
            seconds=0,
            now=datetime.now(UTC) + timedelta(minutes=11),
        )
