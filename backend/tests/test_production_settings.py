"""Production start guard (ADR 0028): unsafe or missing settings refuse to start by name."""

import pytest
from sqlalchemy.engine import make_url

from app.core.config import Settings

READY = {
    "environment": "production",
    "database_url": "postgresql+psycopg://orbit:s3cret-value@db:5432/orbit",
    "market_data_api_key": "tiingo-test",
    "sec_contact_email": "ops@example.com",
    "qa_enabled": True,
    "gemini_api_key": "gemini-test",
}


def settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **{**READY, **overrides})  # type: ignore[arg-type]


def test_development_keeps_zero_configuration_defaults() -> None:
    dev = Settings(_env_file=None)
    assert dev.environment == "development"
    assert dev.production_problems(api=True) == []
    dev.require_production_ready(api=True)


def test_complete_production_settings_start() -> None:
    settings().require_production_ready(api=True)
    settings().require_production_ready(api=False)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://orbit:orbit@db:5432/orbit",
        "postgresql+psycopg://orbit@db:5432/orbit",
    ],
)
def test_default_or_missing_database_password_is_refused(url: str) -> None:
    assert settings(database_url=url).production_problems(api=False) == ["APP_DATABASE_PASSWORD"]


def test_password_supplied_separately_from_the_url() -> None:
    separate = settings(
        database_url="postgresql+psycopg://orbit@db:5432/orbit", database_password="p%w/d@x"
    )
    assert separate.production_problems(api=True) == []
    assert make_url(separate.database_dsn).password == "p%w/d@x"
    assert make_url(separate.database_dsn).host == "db"
    assert "p%w/d@x" not in repr(separate)


def test_development_url_is_used_unchanged_without_a_separate_password() -> None:
    dev = Settings(_env_file=None)
    assert dev.database_dsn == dev.database_url


@pytest.mark.parametrize(
    ("override", "name"),
    [
        ({"market_data_api_key": " "}, "APP_MARKET_DATA_API_KEY"),
        ({"sec_contact_email": "not-an-address"}, "APP_SEC_CONTACT_EMAIL"),
        ({"gemini_api_key": ""}, "APP_GEMINI_API_KEY"),
    ],
)
def test_api_requires_its_provider_settings(override: dict[str, object], name: str) -> None:
    assert settings(**override).production_problems(api=True) == [name]


def test_disabled_questions_need_no_generator_key() -> None:
    assert settings(qa_enabled=False, gemini_api_key="").production_problems(api=True) == []


def test_workers_do_not_need_api_credentials() -> None:
    worker = settings(market_data_api_key="", gemini_api_key="", sec_contact_email="")
    assert worker.production_problems(api=False) == []


def test_refusal_names_settings_without_revealing_values() -> None:
    bad = settings(database_url="postgresql+psycopg://orbit:orbit@db:5432/orbit", gemini_api_key="")
    with pytest.raises(RuntimeError) as raised:
        bad.require_production_ready(api=True)
    message = str(raised.value)
    assert "APP_DATABASE_PASSWORD" in message and "APP_GEMINI_API_KEY" in message
    assert "orbit@db" not in message and "tiingo-test" not in message
