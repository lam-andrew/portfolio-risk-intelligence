"""Bounded HTTP client for Orbit's private CPU encoder; no model runtime in the API."""

import json
import math
from collections.abc import Sequence
from typing import Any

import httpx

from app.data.question_provider import EmbeddedWindow, ModelError

# Must match the checksum-pinned encoder. A model/tokenizer/window change needs a new version.
LOCAL_VERSION = (
    "BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    ":384:cls-l2:window450-overlap32:v1"
)


class LocalEmbeddings:
    embedding_version = LOCAL_VERSION
    local_embeddings = True

    def __init__(self, url: str, *, transport: httpx.BaseTransport | None = None) -> None:
        self.client = httpx.Client(
            base_url=url,
            timeout=httpx.Timeout(30, connect=3),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    def close(self) -> None:
        self.client.close()

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            with self.client.stream("POST", path, json=payload) as response:
                if response.status_code == 503:
                    raise ModelError("Local filing preparation is busy. Please try again shortly.")
                if response.status_code != 200:
                    raise ModelError("Local filing search is unavailable. Please try again later.")
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 100_000:
                        raise ValueError("Oversized response")
                result = json.loads(body)
                if not isinstance(result, dict) or result.get("version") != LOCAL_VERSION:
                    raise ValueError("Encoder version mismatch")
                return result
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelError("Local filing search could not complete this request.") from exc

    def embed(self, texts: Sequence[str], *, query: bool = False) -> list[list[float]]:
        if (
            not 1 <= len(texts) <= 4
            or (query and len(texts) != 1)
            or any(not text.strip() or len(text) > 8192 for text in texts)
        ):
            raise ModelError("Local embedding input is outside the supported limits.")
        result = self._post("/embed", {"texts": list(texts), "query": query})
        try:
            vectors = result["vectors"]
            if not isinstance(vectors, list) or len(vectors) != len(texts):
                raise ValueError("Count mismatch")
            normalized = []
            for vector in vectors:
                if (
                    not isinstance(vector, list)
                    or len(vector) != 384
                    or any(
                        isinstance(v, bool)
                        or not isinstance(v, (float, int))
                        or not math.isfinite(v)
                        for v in vector
                    )
                ):
                    raise ValueError("Invalid vector")
                norm = math.sqrt(sum(v * v for v in vector))
                if not math.isfinite(norm) or not 0.99 <= norm <= 1.01:
                    raise ValueError("Non-unit vector")
                normalized.append([float(v / norm) for v in vector])
            return normalized
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ModelError("Local filing search returned invalid embeddings.") from exc

    def embed_passage(self, text: str) -> list[EmbeddedWindow]:
        if not text.strip() or len(text) > 8192:
            raise ModelError("Local embedding input is outside the supported limits.")
        result = self._post("/windows", {"text": text})
        try:
            windows = result["windows"]
            if not isinstance(windows, list) or not 1 <= len(windows) <= 64:
                raise ValueError("Invalid windows")
            bounds: list[tuple[int, int]] = []
            covered = 0
            for window in windows:
                if not isinstance(window, list) or len(window) != 2:
                    raise ValueError("Invalid window")
                start, end = window
                if (
                    type(start) is not int
                    or type(end) is not int
                    or not 0 <= start < end <= len(text)
                ):
                    raise ValueError("Invalid offsets")
                if (bounds and (start <= bounds[-1][0] or end <= covered)) or text[
                    covered:start
                ].strip():
                    raise ValueError("Missing or unordered source text")
                bounds.append((start, end))
                covered = end
            if text[covered:].strip():
                raise ValueError("Missing source suffix")
        except (KeyError, TypeError, ValueError) as exc:
            raise ModelError("Local filing search returned invalid source windows.") from exc
        embedded: list[EmbeddedWindow] = []
        for i in range(0, len(bounds), 4):
            batch = bounds[i : i + 4]
            vectors = self.embed([text[start:end] for start, end in batch])
            embedded.extend(
                EmbeddedWindow(start, end, vector)
                for (start, end), vector in zip(batch, vectors, strict=True)
            )
        return embedded
