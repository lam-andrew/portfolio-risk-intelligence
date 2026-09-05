"""Top-level API router.

Aggregates the feature routers that make up the backend's public contract.

Everything hangs off the ``/api`` prefix. That is what lets the built frontend and the API
be served from a single origin in production: without it, a page route and an API route
would compete for the same path (``/holdings`` was already both), and the browser would be
handed JSON where it expected the application. Serving both from one origin is what keeps
the session cookie same-site, so ``SameSite=Lax`` continues to hold (ADR 0017).
"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.api import auth, exposure, holdings, imports, market_data, portfolio, risk
from app.api.schemas import HealthResponse
from app.core.config import settings
from app.core.database import check_database

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(holdings.router)
api_router.include_router(imports.router)
api_router.include_router(market_data.router)
api_router.include_router(portfolio.router)
api_router.include_router(risk.router)
api_router.include_router(exposure.router)


@api_router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Report service liveness and database connectivity.

    Always returns ``200`` so the frontend and orchestrators can distinguish "backend up,
    database down" from "backend down". The ``database`` field carries the DB status.
    """
    return HealthResponse(
        service=settings.app_name,
        version=__version__,
        environment=settings.environment,
        database="connected" if check_database() else "unavailable",
        market_data="configured" if settings.market_data_configured else "unconfigured",
    )
