"""add document processing status fields

Revision ID: 20260603_0010
Revises: 20260602_0009
Create Date: 2026-06-03 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260603_0010"
down_revision: str | None = "20260602_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("source_file_path", sa.String(length=500), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "processing_status",
            sa.String(length=30),
            nullable=False,
            server_default="completed",
        ),
    )
    op.add_column("documents", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column("entity_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column("relationship_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column(
            "skipped_duplicate_chunks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_index(
        "ix_documents_processing_status",
        "documents",
        ["processing_status"],
        unique=False,
    )

    op.execute(
        """
        UPDATE documents
        SET chunk_count = counts.chunk_count
        FROM (
            SELECT document_id, COUNT(*) AS chunk_count
            FROM document_chunks
            GROUP BY document_id
        ) AS counts
        WHERE documents.id = counts.document_id
        """
    )
    op.execute(
        """
        UPDATE documents
        SET entity_count = counts.entity_count
        FROM (
            SELECT document_id, COUNT(*) AS entity_count
            FROM rag_entities
            GROUP BY document_id
        ) AS counts
        WHERE documents.id = counts.document_id
        """
    )
    op.execute(
        """
        UPDATE documents
        SET relationship_count = counts.relationship_count
        FROM (
            SELECT document_id, COUNT(*) AS relationship_count
            FROM rag_relationships
            GROUP BY document_id
        ) AS counts
        WHERE documents.id = counts.document_id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_documents_processing_status", table_name="documents")
    op.drop_column("documents", "skipped_duplicate_chunks")
    op.drop_column("documents", "relationship_count")
    op.drop_column("documents", "entity_count")
    op.drop_column("documents", "chunk_count")
    op.drop_column("documents", "processing_error")
    op.drop_column("documents", "processing_status")
    op.drop_column("documents", "source_file_path")
