"""Disposable browser-acceptance entry point. Never used by the production app.

Start only against a database named orbit_acceptance. Fixtures supply prices through the
normal provider/service boundary; real routes, authentication, storage and risk math run.
"""

import json
import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from math import cos, pi, sin, sqrt
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.engine import make_url

from app.api.holdings import get_symbol_provider
from app.api.market_data import SessionDep, get_market_data_service
from app.core.config import settings
from app.data.provider import PriceBar, UnknownSymbolError
from app.data.service import MarketDataService
from app.main import app

if make_url(settings.database_url).database != "orbit_acceptance":
    raise RuntimeError("Browser acceptance requires the disposable orbit_acceptance database")

FIXTURE = Path(os.environ.get("ORBIT_ACCEPTANCE_FIXTURE", "/fixtures/current.json"))
KNOWN = {"AAPL", "MSFT", "NVDA", "TSLA", "VTI", "VOO", "QQQ", "BND", "BIG", "MID", "A", "B"}


class AcceptanceProvider:
    def symbol_exists(self, ticker: str) -> bool:
        return ticker in KNOWN

    def get_daily_prices(self, ticker: str, start: date, end: date) -> list[PriceBar]:
        if ticker not in KNOWN:
            raise UnknownSymbolError(ticker)
        profile = json.loads(FIXTURE.read_text())["profile"]
        prices = [100 * 1.01 ** ((t + 1) // 2) * 0.99 ** (t // 2) for t in range(25)]
        if profile == "overlap":
            prices = [100.0]
            for t in range(24):
                common = sin(2 * pi * t / 24)
                independent = cos(2 * pi * t / 24)
                change = common
                if ticker == "QQQ":
                    change = 0.93 * common + sqrt(1 - 0.93**2) * independent
                elif ticker == "BND":
                    change = sin(4 * pi * t / 24)
                prices.append(prices[-1] * (1 + 0.01 * change))
            prices = [value / prices[-1] * 100 for value in prices]
        elif profile == "constant" and ticker == "MSFT":
            prices = [200.0] * 25
        elif profile == "concentration":
            prices = [value / prices[-1] * 100 for value in prices]
        elif profile == "recovered":
            prices = [100.0] * 20 + [100.0, 80.0, 100.0, 120.0, 72.0, 130.0]
        elif profile == "ongoing":
            prices = [100.0] * 20 + [100.0, 120.0, 90.0]
        elif ticker == "MSFT":
            prices = [2 * value for value in prices]
        anchor = datetime.now(UTC).date() - timedelta(days=len(prices))
        bars = []
        for index, value in enumerate(prices):
            day = anchor + timedelta(days=index)
            if start <= day <= end:
                close = Decimal(str(value)).quantize(Decimal("0.00000001"))
                bars.append(PriceBar(day, close, close, close, close, close, 1000))
        return bars


provider = AcceptanceProvider()


def acceptance_service(session: SessionDep) -> MarketDataService:
    if json.loads(FIXTURE.read_text())["profile"] == "error":
        raise HTTPException(503, "Acceptance fixture: market data temporarily unavailable")
    return MarketDataService(session, provider)


app.dependency_overrides[get_symbol_provider] = lambda: provider
app.dependency_overrides[get_market_data_service] = acceptance_service
