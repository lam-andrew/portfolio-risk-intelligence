"""Versioned pgvector passage embeddings and shared model request budgets.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("passage_embeddings",
        sa.Column("passage_id", sa.Integer(), sa.ForeignKey("filing_passages.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("version", sa.String(100), primary_key=True),
        sa.Column("vector", Vector(768), nullable=False))
    # Exact cosine ranking after issuer/version filtering: no approximate-index recall loss.
    op.create_table("model_budgets",
        sa.Column("scope", sa.String(100), primary_key=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("calls", sa.Integer(), nullable=False),
        sa.Column("next_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    op.drop_table("model_budgets")
    op.drop_table("passage_embeddings")
