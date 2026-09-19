"""Discover active holdings/watchlist tickers and enqueue due work (ADR 0021).

The worker is the scheduler. No SEC I/O or queue dependency is added to portfolio writes.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import CompoundSelect

from app.core.config import settings
from app.models import FilingSync, Holding, WatchlistEntry


def tracked_tickers() -> CompoundSelect[tuple[str]]:
    """One global set; public work must not depend on which account requested it."""
    return select(Holding.ticker).union(select(WatchlistEntry.ticker))


def due_condition(now: datetime) -> ColumnElement[bool]:
    return or_(
        and_(FilingSync.status == "ready", FilingSync.updated_at <= now - timedelta(days=1)),
        and_(
            FilingSync.status.in_(["failed", "partial"]),
            FilingSync.updated_at <= now - timedelta(hours=1),
        ),
        and_(FilingSync.status == "unsupported", FilingSync.updated_at <= now - timedelta(days=7)),
    )


def schedule_due(session: Session, *, now: datetime | None = None) -> int:
    """Schedule at most 100 oldest due tickers; atomic upserts preserve active/manual jobs.

    Called by the advisory-lock owner at startup and between jobs every 30 seconds.
    New positions/imports and watchlist entries are picked up from committed DB state.
    """
    if not settings.sec_configured:
        return 0
    now = now or datetime.now(UTC)
    tracked = tracked_tickers().subquery()
    tickers = list(
        session.scalars(
            select(tracked.c.ticker)
            .outerjoin(FilingSync, FilingSync.ticker == tracked.c.ticker)
            .where(or_(FilingSync.ticker.is_(None), due_condition(now)))
            .order_by(FilingSync.updated_at.asc().nullsfirst(), tracked.c.ticker)
            .limit(100)
        )
    )
    insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    for ticker in tickers:
        values = {
            "status": "queued",
            "stage": "Queued automatically",
            "completed": 0,
            "total": 0,
            "message": None,
            "updated_at": now,
        }
        session.execute(
            insert(FilingSync)
            .values(ticker=ticker, **values)
            .on_conflict_do_update(index_elements=["ticker"], set_=values, where=due_condition(now))
        )
    session.commit()
    return len(tickers)


def next_job(session: Session) -> FilingSync | None:
    """Skip queued work when no account holds or watches the ticker anymore."""
    return session.scalar(
        select(FilingSync)
        .where(FilingSync.status == "queued", FilingSync.ticker.in_(tracked_tickers()))
        .order_by(FilingSync.updated_at, FilingSync.ticker)
        .limit(1)
    )
