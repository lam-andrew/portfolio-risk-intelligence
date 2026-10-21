"""Opt-in real model smoke; no external model API or keys, not a quality evaluation."""

import os

import pytest
from sqlalchemy import select

from app.api.questions import get_question_provider
from app.core.config import settings
from app.data.filing_embeddings import coverage, prepare_batch
from app.data.local_embeddings import LOCAL_VERSION, LocalEmbeddings
from app.data.question_provider import ComposedQuestions
from app.main import app
from app.models import LocalPassageWindow, ModelBudget
from tests.test_questions import QUOTE, ask, db
from tests.test_questions import questions as question_fixture

questions = question_fixture
pytestmark = pytest.mark.skipif(
    os.environ.get("APP_TEST_LOCAL_ENCODER") != "1",
    reason="Requires an explicitly provisioned private local encoder",
)


def test_real_local_encoder_prepares_and_retrieves_for_cited_answer(client, questions, monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "local")
    encoder = LocalEmbeddings(settings.local_embedding_url)
    provider = ComposedQuestions(encoder, questions)  # Generator is deterministic; no Google calls.
    app.dependency_overrides[get_question_provider] = lambda: provider
    try:
        with db() as session:
            assert prepare_batch(session, encoder) == 1
            assert prepare_batch(session, encoder) == 0
            assert coverage(session, "0000000001", LOCAL_VERSION) == (1, 1)
            window = session.scalar(select(LocalPassageWindow))
            assert len(window.vector) == 384
        response = ask(client)
        assert response.status_code == 200, response.text
        citation = response.json()["claims"][0]["citations"][0]
        assert citation["quote"] == QUOTE
        assert citation["start_offset"] == 0 and citation["end_offset"] == len(QUOTE)
        with db() as session:
            assert session.get(ModelBudget, "embeddings") is None
    finally:
        provider.close()
