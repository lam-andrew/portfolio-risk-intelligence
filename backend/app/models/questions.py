"""Versioned public embeddings and content-free request budgets (US-12)."""

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PassageEmbedding(Base):
    __tablename__ = "passage_embeddings"

    passage_id: Mapped[int] = mapped_column(
        ForeignKey("filing_passages.id", ondelete="CASCADE"), primary_key=True
    )
    version: Mapped[str] = mapped_column(String(100), primary_key=True)
    # JSON is only the offline SQLite test representation; production uses pgvector.
    vector: Mapped[list[float]] = mapped_column(Vector(768).with_variant(JSON(), "sqlite"))


class ModelBudget(Base):
    __tablename__ = "model_budgets"

    scope: Mapped[str] = mapped_column(String(100), primary_key=True)
    day: Mapped[date] = mapped_column(Date)
    calls: Mapped[int]
    next_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
