"""claims and claim attachments

Revision ID: 20260529_0005
Revises: 20260528_0004
Create Date: 2026-05-29 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260529_0005"
down_revision: str | None = "20260528_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    incident_type = sa.Enum(
        "accident",
        "hospital",
        "damage",
        "other",
        name="claim_incident_type",
        native_enum=False,
    )
    claim_status = sa.Enum(
        "pending",
        "reviewing",
        "need_more_documents",
        "approved",
        "rejected",
        "completed",
        name="claim_status",
        native_enum=False,
    )
    claim_priority = sa.Enum(
        "low",
        "medium",
        "high",
        "urgent",
        name="claim_priority",
        native_enum=False,
    )

    op.create_table(
        "claims",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("assigned_employee_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("incident_type", incident_type, nullable=False),
        sa.Column("incident_date", sa.Date(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("status", claim_status, server_default="pending", nullable=False),
        sa.Column(
            "priority",
            claim_priority,
            server_default="medium",
            nullable=False,
        ),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assigned_employee_id"],
            ["employees.id"],
            name=op.f("fk_claims_assigned_employee_id_employees"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name=op.f("fk_claims_customer_id_customers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["customer_insurance_subscriptions.id"],
            name=op.f(
                "fk_claims_subscription_id_customer_insurance_subscriptions"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claims")),
    )
    op.create_index(
        op.f("ix_claims_assigned_employee_id"),
        "claims",
        ["assigned_employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_claims_customer_id"),
        "claims",
        ["customer_id"],
        unique=False,
    )
    op.create_index(op.f("ix_claims_id"), "claims", ["id"], unique=False)
    op.create_index(
        op.f("ix_claims_incident_type"),
        "claims",
        ["incident_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_claims_priority"),
        "claims",
        ["priority"],
        unique=False,
    )
    op.create_index(
        op.f("ix_claims_status"),
        "claims",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_claims_subscription_id"),
        "claims",
        ["subscription_id"],
        unique=False,
    )
    op.create_index(op.f("ix_claims_title"), "claims", ["title"], unique=False)

    op.create_table(
        "claim_attachments",
        sa.Column("claim_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["claims.id"],
            name=op.f("fk_claim_attachments_claim_id_claims"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claim_attachments")),
    )
    op.create_index(
        op.f("ix_claim_attachments_claim_id"),
        "claim_attachments",
        ["claim_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_claim_attachments_id"),
        "claim_attachments",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_claim_attachments_id"), table_name="claim_attachments")
    op.drop_index(
        op.f("ix_claim_attachments_claim_id"),
        table_name="claim_attachments",
    )
    op.drop_table("claim_attachments")
    op.drop_index(op.f("ix_claims_title"), table_name="claims")
    op.drop_index(op.f("ix_claims_subscription_id"), table_name="claims")
    op.drop_index(op.f("ix_claims_status"), table_name="claims")
    op.drop_index(op.f("ix_claims_priority"), table_name="claims")
    op.drop_index(op.f("ix_claims_incident_type"), table_name="claims")
    op.drop_index(op.f("ix_claims_id"), table_name="claims")
    op.drop_index(op.f("ix_claims_customer_id"), table_name="claims")
    op.drop_index(op.f("ix_claims_assigned_employee_id"), table_name="claims")
    op.drop_table("claims")
