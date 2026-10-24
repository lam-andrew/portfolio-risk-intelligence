"""Independent embedding/generation selection; never fall back to paid or remote embeddings."""

from app.core.config import settings
from app.data.gemini import EMBEDDING_VERSION, GeminiProvider
from app.data.local_embeddings import LOCAL_VERSION, LocalEmbeddings
from app.data.ollama import OllamaAnswers
from app.data.question_provider import (
    AnswerProvider,
    ComposedQuestions,
    EmbeddingProvider,
    ModelError,
    QuestionProvider,
)


def embedding_version() -> str:
    return LOCAL_VERSION if settings.embedding_provider == "local" else EMBEDDING_VERSION


def create_embedding_provider() -> EmbeddingProvider:
    if not settings.embedding_configured:
        raise ModelError("Filing preparation is not configured yet.")
    if settings.embedding_provider == "local":
        return LocalEmbeddings(settings.local_embedding_url)
    return GeminiProvider(settings.gemini_api_key)


def create_answer_provider() -> AnswerProvider:
    if settings.qa_provider == "ollama":
        return OllamaAnswers(settings.ollama_url, settings.ollama_model)
    return GeminiProvider(settings.gemini_api_key)


def create_provider() -> QuestionProvider:
    if not settings.qa_configured or not settings.embedding_configured:
        raise ModelError("Filing questions are not configured yet.")
    return ComposedQuestions(create_embedding_provider(), create_answer_provider())
