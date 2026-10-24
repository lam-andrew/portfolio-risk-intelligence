"""The local index must obey the same document boundary as hosted embeddings."""

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.data.filing_embeddings import coverage, retrieve
from app.data.local_embeddings import LOCAL_VERSION
from app.models import FilingPassage, LocalPassageWindow, ModelBudget
from tests.test_filing_chat import ACCESSION, BASE, OTHER, ask
from tests.test_questions import QUOTE, db, seed
from tests.test_questions import questions as question_fixture

questions = question_fixture
VECTOR = [1.0] + [0.0] * 383


@pytest.fixture()
def local_questions(questions, monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "local")
    questions.local_embeddings = True
    questions.embedding_version = LOCAL_VERSION

    def embed(texts, *, query=False):
        questions.calls.append(("embed", list(texts), query))
        return [VECTOR for _ in texts]

    questions.embed = embed
    with db() as session:
        passage = session.scalar(select(FilingPassage).where(FilingPassage.accession == ACCESSION))
        session.add(
            LocalPassageWindow(
                passage_id=passage.id,
                version=LOCAL_VERSION,
                ordinal=0,
                start_offset=0,
                end_offset=len(QUOTE),
                vector=[-v for v in VECTOR],
            )
        )
        session.commit()
    return questions


def test_local_selected_filing_ready_without_other_filing_preparation(client, local_questions):
    with db() as session:
        seed(session, accession=OTHER, embedded=False)
    status = client.get(BASE + "/questions/status").json()
    assert status["ready"] and status["ready_passages"] == status["total_passages"] == 1
    assert not client.get("/api/filings/AAPL/questions/status").json()["ready"]
    assert ask(client).status_code == 200


def test_local_followup_excludes_better_ranked_other_filing(client, local_questions):
    with db() as session:
        other = seed(session, accession=OTHER, embedded=False)
        session.add(
            LocalPassageWindow(
                passage_id=other,
                version=LOCAL_VERSION,
                ordinal=0,
                start_offset=0,
                end_offset=len(QUOTE),
                vector=VECTOR,
            )
        )
        session.commit()
        scoped = retrieve(session, "0000000001", LOCAL_VERSION, VECTOR, accession=ACCESSION)
        assert [row.filing.accession for row in scoped] == [ACCESSION]
        assert coverage(session, "0000000002", LOCAL_VERSION, accession=ACCESSION) == (0, 0)
    result = ask(
        client,
        question="How could that supplier affect operations?",
        history=[{"accession": ACCESSION, "question": "What supplier risks?", "answer": "Context"}],
    )
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "answered"
    citations = [c for claim in result.json()["claims"] for c in claim["citations"]]
    assert citations and all(c["accession"] == ACCESSION for c in citations)
    assert len(local_questions.calls[1][2]) == 1
    assert "supplier risks" in local_questions.calls[0][1][0]
    with db() as session:
        assert session.get(ModelBudget, "embeddings") is None
