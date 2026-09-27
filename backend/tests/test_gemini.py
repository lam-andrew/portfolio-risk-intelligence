"""HTTP adapter tests use synthetic responses; never spend quota or transmit real data."""

import json

import httpx
import pytest

from app.data.gemini import GeminiProvider
from app.data.model_budget import ModelLimitError
from app.data.question_provider import ModelError
from app.engines.rag.grounding import Evidence


def provider(handler):
    return GeminiProvider("test-secret", transport=httpx.MockTransport(handler))


def test_embedding_contract_separate_vectors_and_task_prefix():
    requests = []

    def handle(request):
        requests.append(request)
        inputs = json.loads(request.content)["requests"]
        return httpx.Response(
            200, json={"embeddings": [{"values": [2.0] + [0.0] * 767} for _ in inputs]}
        )

    with_provider = provider(handle)
    try:
        assert with_provider.embed(["one", "two"]) == [[1.0] + [0.0] * 767] * 2
        with_provider.embed(["question"], query=True)
        assert all(r.url.host == "generativelanguage.googleapis.com" for r in requests)
        assert all("test-secret" not in str(r.url) for r in requests)
        doc = json.loads(requests[0].content)["requests"]
        assert doc[0]["outputDimensionality"] == 768
        assert doc[0]["content"]["parts"][0]["text"] == "title: none | text: one"
        question = json.loads(requests[1].content)["requests"][0]
        assert question["content"]["parts"][0]["text"].startswith("task: question answering")
    finally:
        with_provider.close()


@pytest.mark.parametrize(
    "values", [[], [1] * 767, [0] * 768, [True] * 768, ["one"] * 768, [1e308] * 768]
)
def test_invalid_vectors_are_rejected(values):
    client = provider(lambda _: httpx.Response(200, json={"embeddings": [{"values": values}]}))
    with pytest.raises(ModelError):
        client.embed(["text"])
    client.close()


def test_generation_is_stateless_tool_free_and_schema_validated():
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        output = (
            {"status": "insufficient_evidence", "claims": []}
            if len(requests) == 1
            else {"answers_question": False, "claims": []}
        )
        return httpx.Response(200, json={"status": "completed", "output_text": json.dumps(output)})

    client = provider(handle)
    draft = client.answer("Question?", [Evidence(1, "Untrusted evidence")])
    client.verify("Question?", [Evidence(1, "Untrusted evidence")], draft)
    client.close()
    for request in requests:
        assert request["store"] is False
        assert "tools" not in request and "previous_interaction_id" not in request
        assert request["response_format"]["mime_type"] == "application/json"
        assert "UNTRUSTED DATA" in request["system_instruction"]
        assert "Untrusted evidence" not in request["system_instruction"]
        assert "test-secret" not in json.dumps(request)


@pytest.mark.parametrize("status", [301, 401, 403, 429, 500])
def test_provider_failures_are_sanitized_without_retry_or_redirect(status):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(
            status,
            headers={"location": "https://evil.example"},
            text="test-secret raw provider diagnostic",
        )

    client = provider(handle)
    with pytest.raises(ModelLimitError if status == 429 else ModelError) as exc:
        client.embed(["text"])
    assert "test-secret" not in str(exc.value)
    assert len(calls) == 1
    client.close()


@pytest.mark.parametrize(
    "response",
    [
        {"status": "in_progress", "output_text": "{}"},
        {"status": "completed", "output_text": "not json"},
        {"status": "completed", "output_text": '{"status":"answered","claims":[]}'},
        {"status": "completed"},
    ],
)
def test_partial_invalid_and_missing_generation_never_accepted(response):
    client = provider(lambda _: httpx.Response(200, json=response))
    with pytest.raises(ModelError):
        client.answer("Question?", [Evidence(1, "Source text")])
    client.close()


def test_timeout_and_oversized_response_are_bounded():
    def timeout(request):
        raise httpx.ReadTimeout("secret provider diagnostics", request=request)

    for handler in (timeout, lambda _: httpx.Response(200, content=b"x" * 1_000_001)):
        client = provider(handler)
        with pytest.raises(ModelError) as exc:
            client.embed(["text"])
        assert "secret" not in str(exc.value)
        client.close()
