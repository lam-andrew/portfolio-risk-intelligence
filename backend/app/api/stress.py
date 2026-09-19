"""Authenticated hypothetical stress scenarios; complete, same-date pricing only."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.api.market_data import ServiceDep
from app.api.schemas import PortfolioStressRead, StressPositionRead, StressScenarioRead
from app.core.database import get_session
from app.data.provider import MarketDataError
from app.engines.risk.stress import apply_price_shock
from app.models import Holding, Portfolio

router = APIRouter(prefix="/portfolio", tags=["risk"])
SessionDep = Annotated[Session, Depends(get_session)]

# Server-owned catalogue: these are illustrative assumptions, not calibrated events.
SCENARIOS = (
    StressScenarioRead(id="decline-10", name="Broad decline · 10%", shock_pct=Decimal(-10)),
    StressScenarioRead(id="decline-20", name="Broad decline · 20%", shock_pct=Decimal(-20)),
    StressScenarioRead(id="decline-35", name="Broad decline · 35%", shock_pct=Decimal(-35)),
)


@router.get("/stress-scenarios", response_model=list[StressScenarioRead])
def get_stress_scenarios(user: CurrentUser) -> list[StressScenarioRead]:
    return list(SCENARIOS)


@router.get("/stress", response_model=PortfolioStressRead)
def get_stress(
    user: CurrentUser,
    session: SessionDep,
    service: ServiceDep,
    scenario: str = "decline-10",
) -> PortfolioStressRead:
    """Estimate a selected shock without modifying holdings or persisting results."""
    selected = next((s for s in SCENARIOS if s.id == scenario), None)
    if selected is None:
        raise HTTPException(status_code=422, detail="Choose a supported stress scenario.")
    holdings = list(
        session.scalars(
            select(Holding)
            .join(Portfolio)
            .where(Portfolio.user_id == user.id)
            .order_by(Holding.ticker)
        )
    )
    if not holdings:
        return PortfolioStressRead(
            scenario=selected, status="empty", message="Add holdings to run a stress test."
        )

    end = datetime.now(UTC).date()
    start = end - timedelta(days=30)
    prices: dict[str, dict[date, Decimal]] = {}
    for holding in holdings:
        try:
            series = service.get_daily_prices(holding.ticker, start, end)
            prices[holding.ticker] = {
                b.date: b.adj_close
                for b in series.bars
                if start <= b.date <= end and b.adj_close.is_finite() and b.adj_close > 0
            }
        except MarketDataError:
            prices[holding.ticker] = {}
    missing = [h.ticker for h in holdings if not prices[h.ticker]]
    if missing:
        return PortfolioStressRead(
            scenario=selected,
            status="unavailable",
            missing_tickers=missing,
            message=(
                "A complete estimate needs usable prices for every holding. "
                "Try again after prices are available."
            ),
        )
    common = set.intersection(*(set(p) for p in prices.values()))
    if not common:
        return PortfolioStressRead(
            scenario=selected,
            status="unavailable",
            message=(
                "No shared pricing date in the last 30 days. "
                "A complete same-date estimate is unavailable."
            ),
        )
    as_of = max(common)
    values = {h.ticker: prices[h.ticker][as_of] * h.quantity for h in holdings}
    try:
        result = apply_price_shock(values, selected.shock_pct / 100)
    except ValueError:
        return PortfolioStressRead(
            scenario=selected,
            status="unavailable",
            message="Portfolio values cannot support an estimate at cent precision.",
        )
    return PortfolioStressRead(
        scenario=selected,
        status="ready",
        as_of=as_of,
        baseline_value=result.baseline_value,
        loss=result.loss,
        stressed_value=result.stressed_value,
        loss_pct=result.loss_pct,
        positions=[
            StressPositionRead(
                ticker=p.ticker,
                baseline_value=p.baseline_value,
                loss=p.loss,
                stressed_value=p.stressed_value,
            )
            for p in result.positions
        ],
    )
