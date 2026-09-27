"""Atomic, deployment-wide reservations; never store question or answer content."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, case, or_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import ModelBudget


class ModelLimitError(Exception):
    """A local budget or provider quota was exhausted. No paid fallback is allowed."""


def reserve(
    session: Session, scope: str, *, daily: int, seconds: int, now: datetime | None = None
) -> None:
    now = now or datetime.now(UTC)
    insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    result = session.execute(
        insert(ModelBudget)
        .values(scope=scope, day=now.date(), calls=1, next_at=now + timedelta(seconds=seconds))
        .on_conflict_do_update(
            index_elements=["scope"],
            set_={
                "day": now.date(),
                "calls": case((ModelBudget.day < now.date(), 1), else_=ModelBudget.calls + 1),
                "next_at": now + timedelta(seconds=seconds),
            },
            where=and_(
                ModelBudget.next_at <= now,
                or_(ModelBudget.day < now.date(), ModelBudget.calls < daily),
            ),
        )
        .returning(ModelBudget.scope)
    ).scalar_one_or_none()
    session.commit()
    if result is None:
        raise ModelLimitError("Question service quota reached. Please try again later.")


def pause(session: Session, scope: str) -> None:
    session.execute(
        update(ModelBudget)
        .where(ModelBudget.scope == scope)
        .values(next_at=datetime.now(UTC) + timedelta(minutes=10))
    )
    session.commit()
