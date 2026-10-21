"""Portable boundaries for embedding and answer generation; pure engines own no I/O."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.engines.rag.grounding import AnswerDraft, Evidence, GroundingVerdict


class ModelError(Exception):
    """Sanitized provider failure safe to show in the UI."""


@dataclass(frozen=True)
class EmbeddedWindow:
    start: int
    end: int
    vector: list[float]


class EmbeddingProvider(Protocol):
    embedding_version: str
    local_embeddings: bool

    def embed(self, texts: Sequence[str], *, query: bool = False) -> list[list[float]]: ...

    def embed_passage(self, text: str) -> list[EmbeddedWindow]: ...

    def close(self) -> None: ...


class AnswerProvider(Protocol):
    model: str

    def answer(self, question: str, passages: Sequence[Evidence]) -> AnswerDraft: ...

    def verify(
        self, question: str, passages: Sequence[Evidence], draft: AnswerDraft
    ) -> GroundingVerdict: ...

    def close(self) -> None: ...


class QuestionProvider(EmbeddingProvider, AnswerProvider, Protocol):
    """Composition consumed by the API; workers need only EmbeddingProvider."""


class ComposedQuestions:
    def __init__(self, embeddings: EmbeddingProvider, answers: AnswerProvider) -> None:
        self.embeddings = embeddings
        self.answers = answers
        self.embedding_version = embeddings.embedding_version
        self.local_embeddings = embeddings.local_embeddings
        self.model = answers.model

    def embed(self, texts: Sequence[str], *, query: bool = False) -> list[list[float]]:
        return self.embeddings.embed(texts, query=query)

    def embed_passage(self, text: str) -> list[EmbeddedWindow]:
        return self.embeddings.embed_passage(text)

    def answer(self, question: str, passages: Sequence[Evidence]) -> AnswerDraft:
        return self.answers.answer(question, passages)

    def verify(
        self, question: str, passages: Sequence[Evidence], draft: AnswerDraft
    ) -> GroundingVerdict:
        return self.answers.verify(question, passages, draft)

    def close(self) -> None:
        try:
            self.embeddings.close()
        finally:
            self.answers.close()
