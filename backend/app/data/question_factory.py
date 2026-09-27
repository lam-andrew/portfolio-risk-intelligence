"""One composition point for external model implementations (ADR 0022)."""

from app.core.config import settings
from app.data.gemini import EMBEDDING_VERSION, GeminiProvider
from app.data.question_provider import ModelError, QuestionProvider


def embedding_version() -> str:
    return EMBEDDING_VERSION if settings.qa_provider == "gemini" else "unconfigured"


def create_provider() -> QuestionProvider:
    if not settings.qa_configured:
        raise ModelError("Filing questions are not configured yet.")
    return GeminiProvider(settings.gemini_api_key)
