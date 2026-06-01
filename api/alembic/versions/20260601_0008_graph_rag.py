"""graph rag entities relationships and chat logs

Revision ID: 20260601_0008
Revises: 20260531_0007
Create Date: 2026-06-01 00:08:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260601_0008"
down_revision: str | None = "20260531_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rag_entities",
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
            name=op.f("fk_rag_entities_chunk_id_document_chunks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_rag_entities_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rag_entities")),
    )
    op.create_index(op.f("ix_rag_entities_chunk_id"), "rag_entities", ["chunk_id"])
    op.create_index(op.f("ix_rag_entities_document_id"), "rag_entities", ["document_id"])
    op.create_index(op.f("ix_rag_entities_entity_type"), "rag_entities", ["entity_type"])
    op.create_index(op.f("ix_rag_entities_id"), "rag_entities", ["id"])
    op.create_index(op.f("ix_rag_entities_name"), "rag_entities", ["name"])

    op.create_table(
        "rag_relationships",
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("target_entity_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
            name=op.f("fk_rag_relationships_chunk_id_document_chunks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_rag_relationships_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_entity_id"],
            ["rag_entities.id"],
            name=op.f("fk_rag_relationships_source_entity_id_rag_entities"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_entity_id"],
            ["rag_entities.id"],
            name=op.f("fk_rag_relationships_target_entity_id_rag_entities"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rag_relationships")),
    )
    op.create_index(op.f("ix_rag_relationships_chunk_id"), "rag_relationships", ["chunk_id"])
    op.create_index(op.f("ix_rag_relationships_document_id"), "rag_relationships", ["document_id"])
    op.create_index(op.f("ix_rag_relationships_id"), "rag_relationships", ["id"])
    op.create_index(
        op.f("ix_rag_relationships_relationship_type"),
        "rag_relationships",
        ["relationship_type"],
    )
    op.create_index(
        op.f("ix_rag_relationships_source_entity_id"),
        "rag_relationships",
        ["source_entity_id"],
    )
    op.create_index(
        op.f("ix_rag_relationships_target_entity_id"),
        "rag_relationships",
        ["target_entity_id"],
    )

    op.create_table(
        "rag_chat_logs",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("retrieved_context_json", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_rag_chat_logs_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rag_chat_logs")),
    )
    op.create_index(op.f("ix_rag_chat_logs_id"), "rag_chat_logs", ["id"])
    op.create_index(op.f("ix_rag_chat_logs_user_id"), "rag_chat_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_rag_chat_logs_user_id"), table_name="rag_chat_logs")
    op.drop_index(op.f("ix_rag_chat_logs_id"), table_name="rag_chat_logs")
    op.drop_table("rag_chat_logs")
    op.drop_index(op.f("ix_rag_relationships_target_entity_id"), table_name="rag_relationships")
    op.drop_index(op.f("ix_rag_relationships_source_entity_id"), table_name="rag_relationships")
    op.drop_index(op.f("ix_rag_relationships_relationship_type"), table_name="rag_relationships")
    op.drop_index(op.f("ix_rag_relationships_id"), table_name="rag_relationships")
    op.drop_index(op.f("ix_rag_relationships_document_id"), table_name="rag_relationships")
    op.drop_index(op.f("ix_rag_relationships_chunk_id"), table_name="rag_relationships")
    op.drop_table("rag_relationships")
    op.drop_index(op.f("ix_rag_entities_name"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_id"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_entity_type"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_document_id"), table_name="rag_entities")
    op.drop_index(op.f("ix_rag_entities_chunk_id"), table_name="rag_entities")
    op.drop_table("rag_entities")
