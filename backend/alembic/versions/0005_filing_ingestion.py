"""Public filing corpus, durable queue and PostgreSQL full-text index.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-19
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("filing_syncs",
        sa.Column("ticker", sa.String(12), primary_key=True),
        sa.Column("cik", sa.String(10)), sa.Column("company", sa.String(300)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("completed", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("filings",
        sa.Column("accession", sa.String(20), primary_key=True),
        sa.Column("cik", sa.String(10), nullable=False),
        sa.Column("form", sa.String(10), nullable=False),
        sa.Column("filed_on", sa.Date(), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_sha256", sa.String(64), nullable=False),
        sa.Column("parser_version", sa.String(40), nullable=False),
        sa.Column("passage_count", sa.Integer(), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_filings_cik", "filings", ["cik"])
    op.create_table("filing_passages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("accession", sa.String(20), sa.ForeignKey("filings.accession", ondelete="CASCADE"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(200), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.UniqueConstraint("accession", "ordinal", name="uq_filing_passage"))
    op.create_index("ix_filing_passages_accession", "filing_passages", ["accession"])
    op.execute("CREATE INDEX ix_filing_passages_search ON filing_passages USING gin (to_tsvector('english', text))")


def downgrade() -> None:
    op.drop_table("filing_passages")
    op.drop_table("filings")
    op.drop_table("filing_syncs")
