"""Authenticated filing ingestion, status, sources and keyword retrieval (US-11)."""

from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.core.config import settings
from app.core.database import get_session
from app.models import Filing, FilingPassage, FilingSync, Holding, Portfolio, WatchlistEntry

router = APIRouter(prefix="/filings", tags=["filings"])
SessionDep = Annotated[Session, Depends(get_session)]
COVERAGE = (
    "Latest 10-K, latest 10-Q and five latest 8-K primary documents "
    "in SEC's recent submissions list."
)


class FilingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    accession: str
    form: str
    filed_on: date
    source_url: str
    passage_count: int
    indexed_at: datetime


class SyncRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ticker: str
    cik: str | None = None
    company: str | None = None
    status: str = "idle"
    stage: str = "Not started"
    completed: int = 0
    total: int = 0
    message: str | None = None
    updated_at: datetime | None = None


class FilingOverview(BaseModel):
    configured: bool
    coverage: str = COVERAGE
    sync: SyncRead
    filings: list[FilingRead]
    indexed_count: int


class SearchHit(BaseModel):
    passage_id: int
    accession: str
    form: str
    filed_on: date
    section: str
    text: str
    source_url: str


def authorize(session: Session, user_id: int, ticker: str) -> str:
    ticker = ticker.upper()
    holding = session.scalar(
        select(Holding.id)
        .join(Portfolio)
        .where(Portfolio.user_id == user_id, Holding.ticker == ticker)
    )
    if holding is None and session.get(WatchlistEntry, (user_id, ticker)) is None:
        raise HTTPException(status_code=404, detail="Held or watched company not found.")
    return ticker


class TrackedCompany(BaseModel):
    ticker: str
    held: bool
    watched: bool
    sync: SyncRead


class TrackedCompanies(BaseModel):
    configured: bool
    companies: list[TrackedCompany]


@router.get("", response_model=TrackedCompanies)
def list_companies(user: CurrentUser, session: SessionDep) -> TrackedCompanies:
    held = set(
        session.scalars(select(Holding.ticker).join(Portfolio).where(Portfolio.user_id == user.id))
    )
    watched = set(
        session.scalars(select(WatchlistEntry.ticker).where(WatchlistEntry.user_id == user.id))
    )
    tickers = held | watched
    jobs = {
        job.ticker: job
        for job in session.scalars(select(FilingSync).where(FilingSync.ticker.in_(tickers)))
    }
    return TrackedCompanies(
        configured=settings.sec_configured,
        companies=[
            TrackedCompany(
                ticker=ticker,
                held=ticker in held,
                watched=ticker in watched,
                sync=SyncRead.model_validate(jobs[ticker])
                if ticker in jobs
                else SyncRead(ticker=ticker),
            )
            for ticker in sorted(tickers)
        ],
    )


@router.get("/{ticker}", response_model=FilingOverview)
def overview(ticker: str, user: CurrentUser, session: SessionDep) -> FilingOverview:
    ticker = authorize(session, user.id, ticker)
    job = session.get(FilingSync, ticker)
    filings = (
        []
        if job is None or job.cik is None
        else list(
            session.scalars(
                select(Filing)
                .where(Filing.cik == job.cik)
                .order_by(Filing.filed_on.desc(), Filing.accession.desc())
                .limit(50)
            )
        )
    )
    count = (
        0
        if job is None or job.cik is None
        else session.scalar(select(func.count()).select_from(Filing).where(Filing.cik == job.cik))
        or 0
    )
    return FilingOverview(
        configured=settings.sec_configured,
        sync=SyncRead.model_validate(job) if job else SyncRead(ticker=ticker),
        filings=[FilingRead.model_validate(f) for f in filings],
        indexed_count=count,
    )


@router.post("/{ticker}/ingest", response_model=SyncRead, status_code=202)
def enqueue(ticker: str, user: CurrentUser, session: SessionDep) -> SyncRead:
    ticker = authorize(session, user.id, ticker)
    if not settings.sec_configured:
        raise HTTPException(status_code=503, detail="SEC ingestion is not configured yet.")
    job = session.scalar(select(FilingSync).where(FilingSync.ticker == ticker).with_for_update())
    now = datetime.now(UTC)
    if job is not None:
        if job.status in {"queued", "running"}:
            return SyncRead.model_validate(job)
        cooldown = 60 if job.status in {"failed", "partial"} else 900
        if now - job.updated_at.replace(tzinfo=UTC) < timedelta(seconds=cooldown):
            raise HTTPException(
                status_code=429, detail="Please wait before refreshing these filings."
            )
        job.status, job.stage, job.message = "queued", "Queued", None
        job.completed = job.total = 0
        job.updated_at = now
    else:
        job = FilingSync(ticker=ticker, updated_at=now)
        session.add(job)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # Another request queued the same public ticker; return that durable job.
        job = session.get(FilingSync, ticker)
        if job is None:
            raise
    return SyncRead.model_validate(job)


@router.get("/{ticker}/search", response_model=list[SearchHit])
def search(
    ticker: str,
    user: CurrentUser,
    session: SessionDep,
    q: Annotated[str, Query(min_length=2, max_length=200)],
) -> list[SearchHit]:
    ticker = authorize(session, user.id, ticker)
    job = session.get(FilingSync, ticker)
    if not job or not job.cik or not q.strip():
        return []
    if session.get_bind().dialect.name == "postgresql":
        rows = session.execute(
            text("""
            SELECT p.id AS passage_id, f.accession, f.form, f.filed_on,
                   p.section, p.text, f.source_url
            FROM filing_passages p JOIN filings f ON f.accession = p.accession
            WHERE f.cik = :cik
              AND to_tsvector('english', p.text) @@ plainto_tsquery('english', :query)
            ORDER BY ts_rank_cd(to_tsvector('english', p.text),
                     plainto_tsquery('english', :query)) DESC, f.filed_on DESC, p.id
            LIMIT 20
        """),
            {"cik": job.cik, "query": q},
        ).mappings()
        return [SearchHit.model_validate(dict(row)) for row in rows]
    # SQLite is only the fast unit-test environment, not the deployment search engine.
    matches = session.execute(
        select(FilingPassage, Filing)
        .join(Filing)
        .where(Filing.cik == job.cik, FilingPassage.text.icontains(q.strip(), autoescape=True))
        .order_by(Filing.filed_on.desc(), FilingPassage.id)
        .limit(20)
    )
    return [
        SearchHit(
            passage_id=p.id,
            accession=f.accession,
            form=f.form,
            filed_on=f.filed_on,
            section=p.section,
            text=p.text,
            source_url=f.source_url,
        )
        for p, f in matches
    ]
