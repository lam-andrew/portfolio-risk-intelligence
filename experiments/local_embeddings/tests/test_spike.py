from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace

from download_model import verify
from model import Encoder
from service import create_app


def fake_encoder():
    encoder = Encoder.__new__(Encoder)
    tokenizer = Tokenizer(WordLevel({"[UNK]": 0, "risk": 1}, unk_token="[UNK]"))
    tokenizer.pre_tokenizer = Whitespace()
    encoder.tokenizer = tokenizer

    class Session:
        def get_inputs(self):
            return [SimpleNamespace(name="input_ids")]

        def run(self, _, inputs):
            shape = inputs["input_ids"].shape
            output = np.ones((*shape, 384), dtype=np.float32)
            output[:, 1:, :] = 0  # Only CLS pooling will produce a nonzero result.
            return [output]

    encoder.session = Session()
    return encoder


def test_windows_cover_long_text_and_preserve_source_offsets():
    encoder = fake_encoder()
    text = "risk " * 1200
    windows = encoder.windows(text)
    assert len(windows) == 3
    assert windows[0][0] == 0
    assert windows[-1][1] == len(text.rstrip())
    for previous, following in zip(windows, windows[1:], strict=False):
        assert following[0] < previous[1]
    for start, end in windows:
        assert len(encoder.tokenizer.encode(text[start:end]).ids) <= 450


def test_rejects_long_text_instead_of_truncating():
    with pytest.raises(ValueError, match="512"):
        fake_encoder().embed(["risk " * 513])


def test_normalized_cls_vectors_and_batch_shapes():
    vectors = fake_encoder().embed(["risk risk", "risk"])
    assert np.asarray(vectors).shape == (2, 384)
    np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-6)


def test_query_prefix_counts_toward_token_limit():
    with pytest.raises(ValueError, match="512"):
        fake_encoder().embed(["risk " * 512], query=True)


@pytest.mark.parametrize("value", [0.0, float("nan"), float("inf")])
def test_invalid_vectors_are_rejected(value):
    encoder = fake_encoder()
    encoder.session.run = lambda *_: [np.full((1, 1, 384), value)]
    with pytest.raises(ValueError):
        encoder.embed(["risk"])


@pytest.mark.parametrize("texts", [[], [" "], ["a" * 8193], ["risk"] * 5])
def test_invalid_model_inputs(texts):
    with pytest.raises(ValueError):
        fake_encoder().embed(texts)


def test_no_silent_multi_query_batch():
    with pytest.raises(ValueError):
        fake_encoder().embed(["risk", "risk"], query=True)


def test_checksum_rejects_missing_and_modified_artifact(tmp_path: Path):
    file = tmp_path / "model"
    assert not verify(file, 1, "wrong")
    file.write_bytes(b"a")
    assert not verify(file, 1, "wrong")


def test_service_validation_health_and_recovery():
    with TestClient(create_app(fake_encoder())) as client:
        assert client.get("/health").json()["dimensions"] == 384
        for texts in ([], [" "], ["x" * 8193], ["risk"] * 5, ["risk " * 513]):
            assert client.post("/embed", json={"texts": texts}).status_code == 422
        assert (
            client.post("/embed", json={"texts": ["risk"], "query": "yes"}).status_code
            == 422
        )
        response = client.post("/embed", json={"texts": ["risk"], "query": True})
        assert response.status_code == 200
        assert len(response.json()["vectors"][0]) == 384


def test_busy_service_rejects_work_without_parallel_inference():
    started, release = Event(), Event()

    class BlockingEncoder:
        def embed(self, texts, query):
            started.set()
            assert release.wait(5)
            return [[1.0] * 384]

    with (
        TestClient(create_app(BlockingEncoder())) as client,
        ThreadPoolExecutor() as pool,
    ):
        pending = pool.submit(client.post, "/embed", json={"texts": ["risk"]})
        try:
            assert started.wait(5)
            busy = client.post("/embed", json={"texts": ["risk"]})
            assert busy.status_code == 503
            assert busy.headers["Retry-After"] == "1"
        finally:
            release.set()
        assert pending.result().status_code == 200
