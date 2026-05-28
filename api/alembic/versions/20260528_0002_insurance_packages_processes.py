"""insurance package and process management

Revision ID: 20260528_0002
Revises: 20260528_0001
Create Date: 2026-05-28 00:00:01.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260528_0002"
down_revision: str | None = "20260528_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    package_status = sa.Enum(
        "active",
        "inactive",
        name="insurance_package_status",
        native_enum=False,
    )
    process_status = sa.Enum(
        "active",
        "inactive",
        name="insurance_process_status",
        native_enum=False,
    )
    required_role = sa.Enum(
        "ADMIN",
        "EMPLOYEE",
        "CUSTOMER",
        name="process_step_required_role",
        native_enum=False,
    )

    op.create_table(
        "insurance_packages",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("package_type", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("premium_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("coverage_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("status", package_status, server_default="active", nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_insurance_packages")),
        sa.UniqueConstraint("code", name=op.f("uq_insurance_packages_code")),
    )
    op.create_index(
        op.f("ix_insurance_packages_code"),
        "insurance_packages",
        ["code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_packages_id"),
        "insurance_packages",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_packages_name"),
        "insurance_packages",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_packages_package_type"),
        "insurance_packages",
        ["package_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_packages_status"),
        "insurance_packages",
        ["status"],
        unique=False,
    )

    op.create_table(
        "insurance_processes",
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", process_status, server_default="active", nullable=False),
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
            ["package_id"],
            ["insurance_packages.id"],
            name=op.f("fk_insurance_processes_package_id_insurance_packages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_insurance_processes")),
    )
    op.create_index(
        op.f("ix_insurance_processes_id"),
        "insurance_processes",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_processes_name"),
        "insurance_processes",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_processes_package_id"),
        "insurance_processes",
        ["package_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_processes_status"),
        "insurance_processes",
        ["status"],
        unique=False,
    )

    op.create_table(
        "process_steps",
        sa.Column("process_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("required_role", required_role, nullable=True),
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
            ["process_id"],
            ["insurance_processes.id"],
            name=op.f("fk_process_steps_process_id_insurance_processes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_process_steps")),
    )
    op.create_index(op.f("ix_process_steps_id"), "process_steps", ["id"], unique=False)
    op.create_index(
        op.f("ix_process_steps_process_id"),
        "process_steps",
        ["process_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_process_steps_process_id"), table_name="process_steps")
    op.drop_index(op.f("ix_process_steps_id"), table_name="process_steps")
    op.drop_table("process_steps")

    op.drop_index(op.f("ix_insurance_processes_status"), table_name="insurance_processes")
    op.drop_index(
        op.f("ix_insurance_processes_package_id"),
        table_name="insurance_processes",
    )
    op.drop_index(op.f("ix_insurance_processes_name"), table_name="insurance_processes")
    op.drop_index(op.f("ix_insurance_processes_id"), table_name="insurance_processes")
    op.drop_table("insurance_processes")

    op.drop_index(op.f("ix_insurance_packages_status"), table_name="insurance_packages")
    op.drop_index(
        op.f("ix_insurance_packages_package_type"),
        table_name="insurance_packages",
    )
    op.drop_index(op.f("ix_insurance_packages_name"), table_name="insurance_packages")
    op.drop_index(op.f("ix_insurance_packages_id"), table_name="insurance_packages")
    op.drop_index(op.f("ix_insurance_packages_code"), table_name="insurance_packages")
    op.drop_table("insurance_packages")
