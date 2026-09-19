"""Shared public SEC corpus and durable serial ingestion queue (ADR 0019)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FilingSync(Base):
    __tablename__ = "filing_syncs"
    ticker: Mapped[str] = mapped_column(String(12), primary_key=True)
    cik: Mapped[str | None] = mapped_column(String(10))
    company: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="queued")
    stage: Mapped[str] = mapped_column(String(40), default="Queued")
    completed: Mapped[int] = mapped_column(default=0)
    total: Mapped[int] = mapped_column(default=0)
    message: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Filing(Base):
    __tablename__ = "filings"
    accession: Mapped[str] = mapped_column(String(20), primary_key=True)
    cik: Mapped[str] = mapped_column(String(10), index=True)
    form: Mapped[str] = mapped_column(String(10))
    filed_on: Mapped[date] = mapped_column(Date)
    source_url: Mapped[str] = mapped_column(String(500))
    text: Mapped[str] = mapped_column(Text)
    text_sha256: Mapped[str] = mapped_column(String(64))
    parser_version: Mapped[str] = mapped_column(String(40))
    passage_count: Mapped[int]
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FilingPassage(Base):
    __tablename__ = "filing_passages"
    __table_args__ = (UniqueConstraint("accession", "ordinal", name="uq_filing_passage"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    accession: Mapped[str] = mapped_column(
        ForeignKey("filings.accession", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int]
    section: Mapped[str] = mapped_column(String(200))
    start_offset: Mapped[int]
    end_offset: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
