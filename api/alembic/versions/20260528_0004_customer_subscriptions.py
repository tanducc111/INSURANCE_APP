"""customer insurance subscriptions

Revision ID: 20260528_0004
Revises: 20260528_0003
Create Date: 2026-05-28 00:00:03.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260528_0004"
down_revision: str | None = "20260528_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    subscription_status = sa.Enum(
        "pending",
        "active",
        "expired",
        "cancelled",
        name="subscription_status",
        native_enum=False,
    )
    payment_status = sa.Enum(
        "unpaid",
        "paid",
        "overdue",
        name="subscription_payment_status",
        native_enum=False,
    )

    op.create_table(
        "customer_insurance_subscriptions",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", subscription_status, server_default="pending", nullable=False),
        sa.Column(
            "payment_status",
            payment_status,
            server_default="unpaid",
            nullable=False,
        ),
        sa.Column("policy_number", sa.String(length=80), nullable=False),
        sa.Column("premium_amount", sa.Numeric(12, 2), nullable=False),
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
            ["customer_id"],
            ["customers.id"],
            name=op.f("fk_customer_insurance_subscriptions_customer_id_customers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["insurance_packages.id"],
            name=op.f(
                "fk_customer_insurance_subscriptions_package_id_insurance_packages"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_customer_insurance_subscriptions"),
        ),
        sa.UniqueConstraint(
            "policy_number",
            name=op.f("uq_customer_insurance_subscriptions_policy_number"),
        ),
    )
    op.create_index(
        op.f("ix_customer_insurance_subscriptions_customer_id"),
        "customer_insurance_subscriptions",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_insurance_subscriptions_id"),
        "customer_insurance_subscriptions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_insurance_subscriptions_package_id"),
        "customer_insurance_subscriptions",
        ["package_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_insurance_subscriptions_payment_status"),
        "customer_insurance_subscriptions",
        ["payment_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_insurance_subscriptions_policy_number"),
        "customer_insurance_subscriptions",
        ["policy_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_insurance_subscriptions_status"),
        "customer_insurance_subscriptions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_customer_insurance_subscriptions_status"),
        table_name="customer_insurance_subscriptions",
    )
    op.drop_index(
        op.f("ix_customer_insurance_subscriptions_policy_number"),
        table_name="customer_insurance_subscriptions",
    )
    op.drop_index(
        op.f("ix_customer_insurance_subscriptions_payment_status"),
        table_name="customer_insurance_subscriptions",
    )
    op.drop_index(
        op.f("ix_customer_insurance_subscriptions_package_id"),
        table_name="customer_insurance_subscriptions",
    )
    op.drop_index(
        op.f("ix_customer_insurance_subscriptions_id"),
        table_name="customer_insurance_subscriptions",
    )
    op.drop_index(
        op.f("ix_customer_insurance_subscriptions_customer_id"),
        table_name="customer_insurance_subscriptions",
    )
    op.drop_table("customer_insurance_subscriptions")
