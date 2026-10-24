"""Ollama answer adapter (ADR 0029): synthetic HTTP only; never contacts a real model server."""

import json

import httpx
import pytest

from app.core.config import Settings
from app.data import question_factory
from app.data.gemini import GeminiProvider
from app.data.ollama import OllamaAnswers
from app.data.question_provider import ModelError
from app.engines.rag.grounding import AnswerDraft, Evidence

PASSAGES = [Evidence(7, "We rely on a single supplier for certain components.", "10-K")]
CLAIM = {
    "text": "The company relies on a single supplier.",
    "evidence": [
        {"passage_id": 7, "quote": "We rely on a single supplier for certain components."}
    ],
}


def reply(content, *, thinking="Passage 7 names a supplier."):
    return httpx.Response(
        200,
        json={"message": {"role": "assistant", "content": content, "thinking": thinking}},
    )


def adapter(handler):
    return OllamaAnswers(
        "http://spark.example.ts.net:11434",
        "qwen3:30b-a3b",
        transport=httpx.MockTransport(handler),
    )


def test_answer_request_is_stateless_thinking_schema_constrained_and_claims_first():
    requests = []

    def handle(request):
        requests.append(request)
        return reply(json.dumps({"claims": [CLAIM]}))

    client = adapter(handle)
    try:
        draft = client.answer("Which supplier risk?", PASSAGES)
    finally:
        client.close()
    assert draft == AnswerDraft.model_validate({"status": "answered", "claims": [CLAIM]})
    (request,) = requests
    assert request.url.path == "/api/chat"
    body = json.loads(request.content)
    assert body["model"] == "qwen3:30b-a3b"
    assert body["stream"] is False and body["think"] is True
    assert body["options"]["temperature"] == 0
    assert list(body["format"]["properties"]) == ["claims"]  # no model-chosen status
    assert body["format"]["additionalProperties"] is False
    system, user = body["messages"]
    assert system["role"] == "system" and "UNTRUSTED DATA" in system["content"]
    assert "Return empty claims" in system["content"]
    assert json.loads(user["content"]) == {
        "question": "Which supplier risk?",
        "passages": [{"passage_id": 7, "text": PASSAGES[0].text, "source_label": "10-K"}],
    }


def test_empty_claims_become_an_abstention_and_thinking_is_never_evidence():
    client = adapter(lambda _: reply('{"claims": []}', thinking=json.dumps({"claims": [CLAIM]})))
    try:
        draft = client.answer("Should I buy?", PASSAGES)
    finally:
        client.close()
    assert draft.status == "insufficient_evidence" and draft.claims == []


def test_verify_uses_a_claims_first_verdict_schema():
    requests = []

    def handle(request):
        requests.append(request)
        return reply(
            json.dumps(
                {"claims": [{"claim_index": 0, "supported": True}], "answers_question": True}
            )
        )

    draft = AnswerDraft.model_validate({"status": "answered", "claims": [CLAIM]})
    client = adapter(handle)
    try:
        verdict = client.verify("Which supplier risk?", PASSAGES, draft)
    finally:
        client.close()
    assert verdict.answers_question and verdict.claims[0].supported
    body = json.loads(requests[0].content)
    assert list(body["format"]["properties"]) == ["claims", "answers_question"]
    assert json.loads(body["messages"][1]["content"])["draft"] == draft.model_dump()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500, json={"error": "model crashed"}),
        httpx.Response(404, json={"error": "model 'qwen3:30b-a3b' not found"}),
        httpx.Response(302, headers={"location": "http://elsewhere/"}),
        reply("not json"),
        reply('{"claims": [], "status": "answered"}'),  # extra key: the model may not set status
        reply(
            json.dumps({"claims": [{**CLAIM, "evidence": [{"passage_id": 7, "quote": "short"}]}]})
        ),
        reply(json.dumps({"claims": [{"text": "x", "evidence": [], "extra": 1}]})),
        httpx.Response(200, json={"message": {"content": None}}),
        httpx.Response(200, json=["unexpected"]),
        httpx.Response(200, content=b"{" + b" " * 1_000_001 + b"}"),
    ],
)
def test_failures_are_sanitized_model_errors(response):
    client = adapter(lambda _: response)
    with pytest.raises(ModelError) as raised:
        client.answer("Which supplier risk?", PASSAGES)
    client.close()
    assert "crashed" not in str(raised.value) and "elsewhere" not in str(raised.value)


def test_unreachable_server_is_a_service_error():
    def handle(request):
        raise httpx.ConnectError("no route", request=request)

    client = adapter(handle)
    with pytest.raises(ModelError):
        client.answer("Which supplier risk?", PASSAGES)
    client.close()


def test_gemini_stays_the_default_generator():
    defaults = Settings(_env_file=None)
    assert defaults.qa_provider == "gemini"
    assert not Settings(_env_file=None, qa_enabled=True, gemini_api_key="").qa_configured


def test_ollama_generator_needs_a_url_but_no_gemini_key():
    local = Settings(
        _env_file=None,
        qa_enabled=True,
        qa_provider="ollama",
        ollama_url="http://spark.example.ts.net:11434",
        embedding_provider="local",
    )
    assert local.qa_configured and local.embedding_configured
    assert not Settings(_env_file=None, qa_enabled=True, qa_provider="ollama").qa_configured
    # Hosted embeddings still need their own Gemini key even with a local generator.
    assert not Settings(
        _env_file=None,
        qa_enabled=True,
        qa_provider="ollama",
        ollama_url="http://spark.example.ts.net:11434",
    ).embedding_configured


def test_factory_composes_the_selected_generator(monkeypatch):
    monkeypatch.setattr(
        question_factory,
        "settings",
        Settings(
            _env_file=None,
            qa_enabled=True,
            qa_provider="ollama",
            ollama_url="http://spark.example.ts.net:11434",
            embedding_provider="local",
        ),
    )
    provider = question_factory.create_provider()
    try:
        assert isinstance(provider.answers, OllamaAnswers)
        assert provider.model == "qwen3:30b-a3b"
    finally:
        provider.close()
    monkeypatch.setattr(
        question_factory,
        "settings",
        Settings(_env_file=None, qa_enabled=True, gemini_api_key="k"),
    )
    provider = question_factory.create_provider()
    try:
        assert isinstance(provider.answers, GeminiProvider)
    finally:
        provider.close()


def test_production_names_the_missing_ollama_url():
    prod = Settings(
        _env_file=None,
        environment="production",
        database_url="postgresql+psycopg://orbit@db:5432/orbit",
        database_password="secret-value",
        market_data_api_key="k",
        sec_contact_email="ops@example.com",
        qa_enabled=True,
        qa_provider="ollama",
        embedding_provider="local",
    )
    assert prod.production_problems(api=True) == ["APP_OLLAMA_URL"]


def test_question_limits_keep_gemini_safe_defaults_and_are_configurable():
    defaults = Settings(_env_file=None)
    assert (defaults.qa_user_daily, defaults.qa_deployment_daily, defaults.qa_generation_daily) == (
        10,
        20,
        40,
    )
    raised = Settings(_env_file=None, qa_user_daily=50, qa_deployment_daily=100)
    assert (raised.qa_user_daily, raised.qa_deployment_daily) == (50, 100)
    with pytest.raises(ValueError):
        Settings(_env_file=None, qa_user_daily=0)
