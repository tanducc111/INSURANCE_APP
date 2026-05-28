"""customer employee assignment management

Revision ID: 20260528_0003
Revises: 20260528_0002
Create Date: 2026-05-28 00:00:02.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260528_0003"
down_revision: str | None = "20260528_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    assignment_status = sa.Enum(
        "active",
        "inactive",
        name="customer_assignment_status",
        native_enum=False,
    )

    op.create_table(
        "employees",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("employee_code", sa.String(length=50), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("position", sa.String(length=120), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=True),
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
            ["user_id"],
            ["users.id"],
            name=op.f("fk_employees_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employees")),
        sa.UniqueConstraint("employee_code", name=op.f("uq_employees_employee_code")),
        sa.UniqueConstraint("user_id", name=op.f("uq_employees_user_id")),
    )
    op.create_index(
        op.f("ix_employees_employee_code"),
        "employees",
        ["employee_code"],
        unique=False,
    )
    op.create_index(op.f("ix_employees_id"), "employees", ["id"], unique=False)
    op.create_index(op.f("ix_employees_user_id"), "employees", ["user_id"], unique=False)

    op.create_table(
        "customers",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("customer_code", sa.String(length=50), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("identity_number", sa.String(length=80), nullable=True),
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
            ["user_id"],
            ["users.id"],
            name=op.f("fk_customers_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customers")),
        sa.UniqueConstraint("customer_code", name=op.f("uq_customers_customer_code")),
        sa.UniqueConstraint("identity_number", name=op.f("uq_customers_identity_number")),
        sa.UniqueConstraint("user_id", name=op.f("uq_customers_user_id")),
    )
    op.create_index(
        op.f("ix_customers_customer_code"),
        "customers",
        ["customer_code"],
        unique=False,
    )
    op.create_index(op.f("ix_customers_id"), "customers", ["id"], unique=False)
    op.create_index(
        op.f("ix_customers_identity_number"),
        "customers",
        ["identity_number"],
        unique=False,
    )
    op.create_index(op.f("ix_customers_user_id"), "customers", ["user_id"], unique=False)

    op.create_table(
        "customer_assignments",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("status", assignment_status, server_default="active", nullable=False),
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
            name=op.f("fk_customer_assignments_customer_id_customers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name=op.f("fk_customer_assignments_employee_id_employees"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_assignments")),
    )
    op.create_index(
        op.f("ix_customer_assignments_customer_id"),
        "customer_assignments",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_assignments_employee_id"),
        "customer_assignments",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_assignments_id"),
        "customer_assignments",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_assignments_status"),
        "customer_assignments",
        ["status"],
        unique=False,
    )

    op.create_table(
        "follow_up_notes",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
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
            name=op.f("fk_follow_up_notes_customer_id_customers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name=op.f("fk_follow_up_notes_employee_id_employees"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_follow_up_notes")),
    )
    op.create_index(
        op.f("ix_follow_up_notes_customer_id"),
        "follow_up_notes",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_follow_up_notes_employee_id"),
        "follow_up_notes",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_follow_up_notes_id"),
        "follow_up_notes",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_follow_up_notes_id"), table_name="follow_up_notes")
    op.drop_index(op.f("ix_follow_up_notes_employee_id"), table_name="follow_up_notes")
    op.drop_index(op.f("ix_follow_up_notes_customer_id"), table_name="follow_up_notes")
    op.drop_table("follow_up_notes")

    op.drop_index(
        op.f("ix_customer_assignments_status"),
        table_name="customer_assignments",
    )
    op.drop_index(op.f("ix_customer_assignments_id"), table_name="customer_assignments")
    op.drop_index(
        op.f("ix_customer_assignments_employee_id"),
        table_name="customer_assignments",
    )
    op.drop_index(
        op.f("ix_customer_assignments_customer_id"),
        table_name="customer_assignments",
    )
    op.drop_table("customer_assignments")

    op.drop_index(op.f("ix_customers_user_id"), table_name="customers")
    op.drop_index(op.f("ix_customers_identity_number"), table_name="customers")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_index(op.f("ix_customers_customer_code"), table_name="customers")
    op.drop_table("customers")

    op.drop_index(op.f("ix_employees_user_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_employee_code"), table_name="employees")
    op.drop_table("employees")
