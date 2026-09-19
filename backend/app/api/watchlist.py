"""Authenticated ticker-only following preferences (US-21)."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.auth import CurrentUser
from app.api.holdings import ProviderDep, SessionDep
from app.api.schemas import TickerInput
from app.data.symbols import is_recognized_symbol
from app.models import User, WatchlistEntry

router = APIRouter(prefix="/watchlist", tags=["watchlist"])
MAX_WATCHLIST = 100


@router.get("", response_model=list[str])
def list_watchlist(session: SessionDep, user: CurrentUser) -> list[str]:
    return list(
        session.scalars(
            select(WatchlistEntry.ticker)
            .where(WatchlistEntry.user_id == user.id)
            .order_by(WatchlistEntry.ticker)
        )
    )


@router.post("", response_model=TickerInput, status_code=201)
def add_watch(
    payload: TickerInput, session: SessionDep, provider: ProviderDep, user: CurrentUser
) -> TickerInput:
    # Serialize per-account additions so concurrent requests cannot exceed the limit.
    if not is_recognized_symbol(payload.ticker, provider):
        raise HTTPException(
            status_code=422,
            detail=f"Unrecognized ticker '{payload.ticker}'. Check the symbol and try again.",
        )
    session.scalar(select(User.id).where(User.id == user.id).with_for_update())
    key = (user.id, payload.ticker)
    if session.get(WatchlistEntry, key):
        return payload
    count = (
        session.scalar(
            select(func.count())
            .select_from(WatchlistEntry)
            .where(WatchlistEntry.user_id == user.id)
        )
        or 0
    )
    if count >= MAX_WATCHLIST:
        raise HTTPException(
            status_code=409,
            detail="Your watchlist is full (100 companies). Remove one before adding another.",
        )
    session.add(WatchlistEntry(user_id=user.id, ticker=payload.ticker))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        if session.get(WatchlistEntry, key) is None:
            raise
    return payload


@router.delete("/{ticker}", status_code=204)
def remove_watch(ticker: str, session: SessionDep, user: CurrentUser) -> None:
    entry = session.get(WatchlistEntry, (user.id, ticker.upper()))
    if entry is None:
        raise HTTPException(status_code=404, detail="Watchlist company not found.")
    session.delete(entry)
    session.commit()
