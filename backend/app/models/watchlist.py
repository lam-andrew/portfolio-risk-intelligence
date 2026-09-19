"""Private following preferences, separate from portfolio positions (ADR 0021)."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    ticker: Mapped[str] = mapped_column(String(12), primary_key=True)
