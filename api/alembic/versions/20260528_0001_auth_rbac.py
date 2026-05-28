"""auth rbac foundation

Revision ID: 20260528_0001
Revises:
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260528_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    user_role = sa.Enum(
        "ADMIN",
        "EMPLOYEE",
        "CUSTOMER",
        name="user_role",
        native_enum=False,
    )
    user_status = sa.Enum(
        "active",
        "inactive",
        name="user_status",
        native_enum=False,
    )

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("status", user_status, server_default="active", nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "activity_logs",
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
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
            ["actor_user_id"],
            ["users.id"],
            name=op.f("fk_activity_logs_actor_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity_logs")),
    )
    op.create_index(
        op.f("ix_activity_logs_action"),
        "activity_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_actor_user_id"),
        "activity_logs",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_entity_type"),
        "activity_logs",
        ["entity_type"],
        unique=False,
    )
    op.create_index(op.f("ix_activity_logs_id"), "activity_logs", ["id"], unique=False)

    op.create_table(
        "login_history",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
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
            name=op.f("fk_login_history_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_login_history")),
    )
    op.create_index(
        op.f("ix_login_history_email"),
        "login_history",
        ["email"],
        unique=False,
    )
    op.create_index(op.f("ix_login_history_id"), "login_history", ["id"], unique=False)
    op.create_index(
        op.f("ix_login_history_user_id"),
        "login_history",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_login_history_user_id"), table_name="login_history")
    op.drop_index(op.f("ix_login_history_id"), table_name="login_history")
    op.drop_index(op.f("ix_login_history_email"), table_name="login_history")
    op.drop_table("login_history")

    op.drop_index(op.f("ix_activity_logs_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_entity_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_actor_user_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_action"), table_name="activity_logs")
    op.drop_table("activity_logs")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
