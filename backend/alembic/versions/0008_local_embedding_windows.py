"""Add a separate, reversible local 384-dimensional window index.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-10
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("local_passage_windows",
        sa.Column("passage_id", sa.Integer(), sa.ForeignKey("filing_passages.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("version", sa.String(160), primary_key=True),
        sa.Column("ordinal", sa.Integer(), primary_key=True),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("vector", Vector(384), nullable=False))


def downgrade() -> None:
    op.drop_table("local_passage_windows")
