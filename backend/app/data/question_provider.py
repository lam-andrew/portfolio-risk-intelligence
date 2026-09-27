"""Model adapter boundary. Production adapters own I/O; pure engines never do."""

from collections.abc import Sequence
from typing import Protocol

from app.engines.rag.grounding import AnswerDraft, Evidence, GroundingVerdict


class ModelError(Exception):
    """Sanitized provider failure safe to show in the UI."""


class QuestionProvider(Protocol):
    embedding_version: str
    model: str

    def embed(self, texts: Sequence[str], *, query: bool = False) -> list[list[float]]: ...

    def answer(self, question: str, passages: Sequence[Evidence]) -> AnswerDraft: ...

    def verify(
        self, question: str, passages: Sequence[Evidence], draft: AnswerDraft
    ) -> GroundingVerdict: ...

    def close(self) -> None: ...
