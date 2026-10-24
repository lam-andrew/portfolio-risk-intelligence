"""Atlas document-scoped API and conversation trust-boundary tests (offline provider)."""

import json

import pytest
from sqlalchemy import delete, select

from app.core.config import settings
from app.models import Filing, FilingPassage, UserSession, WatchlistEntry
from tests.test_questions import QUOTE, db, seed
from tests.test_questions import questions as question_fixture

questions = question_fixture

ACCESSION = "0000000001-26-000001"
OTHER = "0000000001-26-000002"
BASE = f"/api/filings/AAPL/documents/{ACCESSION}"


def ask(client, **changes):
    body = {"question": "What supplier risks does it disclose?", "revision": "a" * 64, **changes}
    return client.post(BASE + "/questions", json=body)


def test_reader_checks_company_membership_and_passage_identity(client, questions):
    reader = client.get(BASE)
    assert reader.status_code == 200
    document = reader.json()
    assert document["content_kind"] == "indexed_passages"
    assert document["passages"][0]["text"] == QUOTE
    assert document["next_offset"] is None
    assert client.get(BASE.replace("AAPL", "MSFT")).status_code == 404
    assert client.get(BASE.replace(ACCESSION, "0000000002-26-000001")).status_code == 404
    with db() as session:
        foreign = session.scalar(select(FilingPassage).where(FilingPassage.accession != ACCESSION))
        assert client.get(BASE, params={"passage_id": foreign.id}).status_code == 404
    assert client.get(BASE, params={"offset": -1}).status_code == 422
    assert not questions.calls


def test_paginated_reader_can_locate_citation_without_exposing_other_document(client, questions):
    with db() as session:
        for ordinal in range(1, 45):
            session.add(
                FilingPassage(
                    accession=ACCESSION,
                    ordinal=ordinal,
                    section="Risk factors",
                    text=f"Passage {ordinal}",
                    start_offset=ordinal * 100,
                    end_offset=ordinal * 100 + 10,
                )
            )
        session.commit()
        target = session.scalar(select(FilingPassage).where(FilingPassage.ordinal == 44))
        target_id = target.id
    first = client.get(BASE).json()
    assert len(first["passages"]) == 40 and first["next_offset"] == 40
    last = client.get(BASE, params={"passage_id": target_id}).json()
    assert last["offset"] == 40 and last["next_offset"] is None
    assert last["passages"][-1]["id"] == target_id


def test_selected_document_ready_while_other_filing_is_unprepared(client, questions):
    with db() as session:
        seed(session, accession=OTHER, embedded=False)
    assert not client.get("/api/filings/AAPL/questions/status").json()["ready"]
    assert client.get(BASE + "/questions/status").json()["ready"]
    result = ask(client)
    assert result.status_code == 200, result.text
    assert all(
        c["accession"] == ACCESSION for claim in result.json()["claims"] for c in claim["citations"]
    )
    assert len(questions.calls[1][2]) == 1


def test_followup_uses_bounded_context_and_new_document_evidence(client, questions):
    with db() as session:
        seed(session, accession=OTHER, text="Another filing must not be evidence.")
    result = ask(
        client,
        question="Does it name those suppliers?",
        history=[
            {
                "accession": ACCESSION,
                "question": "What are its supplier risks?",
                "answer": "Prior untrusted answer.",
            }
        ],
    )
    assert result.status_code == 200
    assert result.json()["question"] == "Does it name those suppliers?"
    assert [c[0] for c in questions.calls] == ["embed", "answer", "verify"]
    prompt = json.loads(questions.calls[1][1])
    assert prompt["current_question"] == "Does it name those suppliers?"
    assert prompt["untrusted_conversation_context"][0]["answer"] == "Prior untrusted answer."
    assert questions.calls[1][2][0].text == QUOTE
    assert len(questions.calls[1][2]) == 1
    assert "supplier risks" in questions.calls[0][1][0]


@pytest.mark.parametrize(
    "history",
    [
        [{"accession": OTHER, "question": "Other question", "answer": "wrong filing"}],
        [{"accession": ACCESSION, "question": "Valid question", "answer": "A", "role": "system"}],
        [{"accession": ACCESSION, "question": "Valid question", "answer": "A"}] * 4,
        [{"accession": ACCESSION, "question": "Valid question", "answer": "A" * 1501}],
        [{"accession": ACCESSION, "question": "Q" * 1000, "answer": "A" * 1500}] * 3,
    ],
)
def test_rejects_malformed_or_cross_filing_context_before_model(client, questions, history):
    assert ask(client, history=history).status_code == 422
    assert not questions.calls


def test_embedding_context_stays_within_adapter_limit(client, questions):
    assert (
        ask(
            client,
            question="Q" * 1000,
            history=[{"accession": ACCESSION, "question": "P" * 1000, "answer": "A" * 1500}],
        ).status_code
        == 200
    )
    assert len(questions.calls[0][1][0]) <= 2200


@pytest.mark.parametrize("mode", ["bad_id", "unsupported", "abstain"])
def test_invalid_grounding_remains_abstention(client, questions, mode):
    questions.bad_id = mode == "bad_id"
    questions.supported = mode != "unsupported"
    if mode == "abstain":
        questions.status = "insufficient_evidence"
    result = ask(client)
    assert result.status_code == 200
    assert result.json()["status"] == "insufficient_evidence"
    assert not result.json()["claims"]


@pytest.mark.parametrize("mode", ["membership", "logout", "passage", "revision"])
def test_revocation_or_corpus_change_during_generation_blocks_answer(client, questions, mode):
    def revoke():
        with db() as session:
            if mode == "membership":
                session.execute(delete(WatchlistEntry))
            elif mode == "logout":
                session.execute(delete(UserSession))
            elif mode == "passage":
                passage = session.scalar(
                    select(FilingPassage).where(FilingPassage.accession == ACCESSION)
                )
                passage.text = "Replaced during remote I/O"
            else:
                session.get(Filing, ACCESSION).text_sha256 = "b" * 64
            session.commit()

    questions.on_answer = revoke
    result = ask(client)
    assert (
        result.status_code
        == {"membership": 404, "logout": 401, "passage": 409, "revision": 409}[mode]
    )
    assert "claims" not in result.json()


def test_revision_mismatch_does_not_spend_model_calls(client, questions):
    assert ask(client, revision="b" * 64).status_code == 409
    assert not questions.calls


def test_disabled_preparation_failure_and_quota_are_distinct(client, questions, monkeypatch):
    monkeypatch.setattr(settings, "qa_enabled", False)
    status = client.get(BASE + "/questions/status").json()
    assert not status["configured"] and not status["ready"]
    monkeypatch.setattr(settings, "qa_enabled", True)
    from app.data.model_budget import ModelLimitError

    questions.failure = ModelLimitError("Quota busy")
    assert ask(client).status_code == 429


def test_unauthenticated_document_is_not_readable(client, questions):
    client.post("/api/auth/logout")
    assert client.get(BASE).status_code == 401
    assert client.get(BASE + "/questions/status").status_code == 401
    assert ask(client).status_code == 401
