"""Private ticker watchlists; existing holdings are discovered by the worker.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("watchlist_entries",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ticker", sa.String(12), primary_key=True))


def downgrade() -> None:
    op.drop_table("watchlist_entries")
