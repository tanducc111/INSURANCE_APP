"""add document ingestion metrics

Revision ID: 20260603_0011
Revises: 20260603_0010
Create Date: 2026-06-03 01:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260603_0011"
down_revision: str | None = "20260603_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column("extracted_character_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column("average_chunk_length", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column("max_chunk_length", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute("UPDATE documents SET extracted_character_count = length(coalesce(raw_text, ''))")
    op.execute(
        """
        UPDATE documents
        SET average_chunk_length = counts.avg_length,
            max_chunk_length = counts.max_length
        FROM (
            SELECT
                document_id,
                COALESCE(ROUND(AVG(length(content))), 0)::int AS avg_length,
                COALESCE(MAX(length(content)), 0)::int AS max_length
            FROM document_chunks
            GROUP BY document_id
        ) AS counts
        WHERE documents.id = counts.document_id
        """
    )


def downgrade() -> None:
    op.drop_column("documents", "max_chunk_length")
    op.drop_column("documents", "average_chunk_length")
    op.drop_column("documents", "extracted_character_count")
    op.drop_column("documents", "page_count")
