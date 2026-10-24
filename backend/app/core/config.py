"""Application configuration, loaded from environment variables.

All external configuration (database DSN, allowed CORS origins, etc.) is supplied via the
environment — never hard-coded and never committed. See ``.env.example`` at the repo root
for the full list of variables.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings resolved from environment variables (prefixed ``APP_``).

    The prefix is deliberately brand-neutral so a product rename never touches env var
    names (see docs/renaming.md).

    Defaults are development-friendly and match ``docker-compose.yml`` so the stack boots
    with zero manual configuration; override them via the environment in other contexts.
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application metadata. app_name is pinned to the exact env var APP_NAME (rather than
    # the prefixed APP_APP_NAME) via an explicit alias.
    app_name: str = Field(default="Orbit API", validation_alias="APP_NAME")
    environment: str = "development"

    # Database (PostgreSQL 16 + pgvector). Async-agnostic SQLAlchemy DSN.
    database_url: str = "postgresql+psycopg://orbit:orbit@db:5432/orbit"
    # Optional password kept out of the URL (production supplies it separately; ADR 0028).
    database_password: str = Field(default="", repr=False)

    @property
    def database_dsn(self) -> str:
        """The connection URL actually used: ``database_url`` plus any separate password."""
        if not self.database_password:
            return self.database_url
        from sqlalchemy.engine import make_url

        url = make_url(self.database_url).set(password=self.database_password)
        return url.render_as_string(hide_password=False)

    # CORS: origins allowed to call the API (the frontend dev server by default).
    cors_origins: list[str] = ["http://localhost:5173"]

    # Market data (US-4; see docs/adr/0011-market-data-provider.md). The provider is
    # selected by name and reached behind the MarketDataProvider interface, so swapping
    # providers is a config change. The key is secret — set it in .env, never commit it.
    market_data_provider: str = "tiingo"
    market_data_api_key: str = ""
    # How long cached daily prices stay fresh before we re-fetch (FR-6).
    market_data_cache_ttl_hours: int = 24

    # SEC identifies the application operator, not the signed-in user.
    sec_contact_email: str = ""

    # Enable only with a Google AI Studio project whose billing is disabled (ADR 0022).
    qa_enabled: bool = False
    qa_provider: str = "gemini"
    gemini_api_key: str = Field(default="", repr=False)

    embedding_provider: Literal["gemini", "local"] = "gemini"
    local_embedding_url: str = "http://encoder:8081"

    @property
    def embedding_configured(self) -> bool:
        return self.qa_enabled and (
            bool(self.local_embedding_url.strip())
            if self.embedding_provider == "local"
            else self.qa_configured
        )

    @property
    def qa_configured(self) -> bool:
        return (
            self.qa_enabled and self.qa_provider == "gemini" and bool(self.gemini_api_key.strip())
        )

    @property
    def sec_configured(self) -> bool:
        import re

        return re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", self.sec_contact_email) is not None

    @property
    def market_data_configured(self) -> bool:
        """Whether a market-data API key is present. Lets the app boot (and /health report)
        without a key, instead of crashing, so the stack runs before US-4 is configured."""
        return bool(self.market_data_api_key.strip())

    def production_problems(self, *, api: bool) -> list[str]:
        """Names (never values) of settings unsafe or missing for a production start (ADR 0028).

        Development keeps its zero-configuration defaults; production must not silently run on
        them. Workers pass ``api=False``: they never receive the API's provider credentials.
        """
        if self.environment != "production":
            return []
        from sqlalchemy.engine import make_url

        problems = []
        password = make_url(self.database_dsn).password
        if not password or password == "orbit":
            problems.append("APP_DATABASE_PASSWORD")
        if api:
            if not self.market_data_configured:
                problems.append("APP_MARKET_DATA_API_KEY")
            if not self.sec_configured:
                problems.append("APP_SEC_CONTACT_EMAIL")
            if self.qa_enabled and not self.qa_configured:
                problems.append("APP_GEMINI_API_KEY")
        return problems

    def require_production_ready(self, *, api: bool) -> None:
        problems = self.production_problems(api=api)
        if problems:
            raise RuntimeError(
                "Refusing to start with APP_ENVIRONMENT=production; set: " + ", ".join(problems)
            )


settings = Settings()
"""Process-wide settings singleton. Import this rather than instantiating ``Settings``."""
