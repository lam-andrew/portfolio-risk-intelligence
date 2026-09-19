"""FR-11 / US-9: independently computed shocks and authenticated API behavior."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.data.provider import MarketDataError, PriceBar
from app.engines.risk.stress import apply_price_shock
from tests.fakes import FakeProvider


def test_hand_computed_loss_and_contributions() -> None:
    result = apply_price_shock({"AAPL": Decimal(1000), "MSFT": Decimal(500)}, Decimal("-0.2"))
    assert (result.baseline_value, result.loss, result.stressed_value, result.loss_pct) == (
        Decimal(1500),
        Decimal(300),
        Decimal(1200),
        Decimal(20),
    )
    assert [(p.ticker, p.loss, p.stressed_value) for p in result.positions] == [
        ("AAPL", Decimal(200), Decimal(800)),
        ("MSFT", Decimal(100), Decimal(400)),
    ]


@pytest.mark.parametrize("shock,loss", [("0", "0"), ("-1", "1500")])
def test_boundary_shocks(shock: str, loss: str) -> None:
    result = apply_price_shock({"AAPL": Decimal(1500)}, Decimal(shock))
    assert result.loss == Decimal(loss)
    assert result.stressed_value + result.loss == result.baseline_value


def test_rounding_reconciles_with_visible_rows() -> None:
    result = apply_price_shock(
        {"AAPL": Decimal("10.05"), "MSFT": Decimal("10.05")}, Decimal("-0.1")
    )
    assert result.loss == Decimal("2.02")  # each $1.005 loss rounds half-up
    assert result.stressed_value == Decimal("18.08")
    assert sum(p.loss for p in result.positions) == result.loss
    assert sum(p.stressed_value for p in result.positions) == result.stressed_value


@pytest.mark.parametrize("shock", ["0.1", "-1.01", "NaN", "Infinity"])
def test_invalid_shocks(shock: str) -> None:
    with pytest.raises(ValueError):
        apply_price_shock({"AAPL": Decimal(100)}, Decimal(shock))


@pytest.mark.parametrize("value", ["0", "-1", "NaN", "Infinity", "0.001"])
def test_invalid_or_subcent_portfolio(value: str) -> None:
    with pytest.raises(ValueError):
        apply_price_shock({"AAPL": Decimal(value)}, Decimal("-0.1"))


def test_empty_engine_input() -> None:
    with pytest.raises(ValueError):
        apply_price_shock({}, Decimal("-0.1"))


def _add(client: TestClient, ticker: str, quantity: str = "10") -> None:
    response = client.post("/api/holdings", json={"ticker": ticker, "quantity": quantity})
    assert response.status_code == 201, response.text


def _bar(day: date, price: str) -> PriceBar:
    p = Decimal(price)
    return PriceBar(day, p, p, p, p, p, 1000)


def test_catalog_and_validation(client: TestClient, provider: FakeProvider) -> None:
    catalog = client.get("/api/portfolio/stress-scenarios").json()
    assert [Decimal(s["shock_pct"]) for s in catalog] == [-10, -20, -35]
    assert len({s["id"] for s in catalog}) == 3
    assert client.get("/api/portfolio/stress?scenario=made-up").status_code == 422
    assert provider.price_calls == 0


def test_empty_portfolio_is_not_a_zero_loss(client: TestClient) -> None:
    response = client.get("/api/portfolio/stress")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "empty"
    assert body["loss"] is None
    assert body["positions"] == []


def test_latest_common_date_and_fractional_shares(
    client: TestClient,
    provider: FakeProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)
    _add(client, "AAPL", "1.5")
    _add(client, "MSFT", "2")

    def prices(ticker: str, start: date, end: date) -> list[PriceBar]:
        return (
            [_bar(yesterday, "100"), _bar(today, "999")]
            if ticker == "AAPL"
            else [_bar(yesterday, "50")]
        )

    monkeypatch.setattr(provider, "get_daily_prices", prices)
    before = client.get("/api/holdings").json()
    body = client.get("/api/portfolio/stress?scenario=decline-20").json()
    assert body["status"] == "ready"
    assert body["as_of"] == yesterday.isoformat()
    assert Decimal(body["baseline_value"]) == 250
    assert Decimal(body["loss"]) == 50
    assert Decimal(body["stressed_value"]) == 200
    assert [Decimal(p["loss"]) for p in body["positions"]] == [30, 20]
    assert client.get("/api/holdings").json() == before


@pytest.mark.parametrize("mode", ["failure", "empty", "zero", "negative", "disjoint", "old"])
def test_incomplete_prices_never_produce_partial_totals(
    client: TestClient,
    provider: FakeProvider,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    today = datetime.now(UTC).date()
    _add(client, "AAPL")
    _add(client, "MSFT")

    def prices(ticker: str, start: date, end: date) -> list[PriceBar]:
        if ticker == "AAPL":
            return [_bar(today, "100")]
        if mode == "failure":
            raise MarketDataError("test failure")
        if mode == "empty":
            return []
        if mode == "disjoint":
            return [_bar(today - timedelta(days=1), "50")]
        if mode == "old":
            return [_bar(today - timedelta(days=45), "50")]
        return [_bar(today, "0" if mode == "zero" else "-1")]

    monkeypatch.setattr(provider, "get_daily_prices", prices)
    body = client.get("/api/portfolio/stress").json()
    assert body["status"] == "unavailable"
    assert body["baseline_value"] is None
    assert body["loss"] is None
    assert body["positions"] == []
    if mode != "disjoint":
        assert body["missing_tickers"] == ["MSFT"]


def test_changing_scenarios_reuses_cached_prices(
    client: TestClient, provider: FakeProvider
) -> None:
    _add(client, "AAPL")
    first = client.get("/api/portfolio/stress?scenario=decline-10").json()
    second = client.get("/api/portfolio/stress?scenario=decline-35").json()
    assert first["status"] == second["status"] == "ready"
    assert Decimal(second["loss"]) > Decimal(first["loss"])
    assert first["baseline_value"] == second["baseline_value"]
    assert provider.price_calls == 1


@pytest.mark.parametrize("path", ["/api/portfolio/stress", "/api/portfolio/stress-scenarios"])
def test_anonymous_rejected(anon_client: TestClient, path: str) -> None:
    assert anon_client.get(path).status_code == 401


def test_accounts_are_isolated(client: TestClient) -> None:
    _add(client, "AAPL")
    assert client.post("/api/auth/logout").status_code == 204
    response = client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    body = client.get("/api/portfolio/stress").json()
    assert body["status"] == "empty"
    assert body["positions"] == []
