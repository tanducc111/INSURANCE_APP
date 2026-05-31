"""chat rooms messages and appointments

Revision ID: 20260531_0006
Revises: 20260529_0005
Create Date: 2026-05-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260531_0006"
down_revision: str | None = "20260529_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    appointment_status = sa.Enum(
        "pending",
        "accepted",
        "rejected",
        "rescheduled",
        "cancelled",
        "completed",
        name="appointment_status",
        native_enum=False,
    )

    op.create_table(
        "chat_rooms",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
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
            name=op.f("fk_chat_rooms_customer_id_customers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name=op.f("fk_chat_rooms_employee_id_employees"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_rooms")),
        sa.UniqueConstraint(
            "customer_id",
            "employee_id",
            name="uq_chat_rooms_customer_id_employee_id",
        ),
    )
    op.create_index(
        op.f("ix_chat_rooms_customer_id"),
        "chat_rooms",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_rooms_employee_id"),
        "chat_rooms",
        ["employee_id"],
        unique=False,
    )
    op.create_index(op.f("ix_chat_rooms_id"), "chat_rooms", ["id"], unique=False)

    op.create_table(
        "appointments",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("status", appointment_status, server_default="pending", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
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
            name=op.f("fk_appointments_customer_id_customers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name=op.f("fk_appointments_employee_id_employees"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointments")),
    )
    op.create_index(
        op.f("ix_appointments_customer_id"),
        "appointments",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_employee_id"),
        "appointments",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_id"),
        "appointments",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_scheduled_at"),
        "appointments",
        ["scheduled_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointments_status"),
        "appointments",
        ["status"],
        unique=False,
    )

    op.create_table(
        "chat_messages",
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("sender_user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
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
            ["room_id"],
            ["chat_rooms.id"],
            name=op.f("fk_chat_messages_room_id_chat_rooms"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_user_id"],
            ["users.id"],
            name=op.f("fk_chat_messages_sender_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
    )
    op.create_index(
        op.f("ix_chat_messages_id"),
        "chat_messages",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_messages_room_id"),
        "chat_messages",
        ["room_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_messages_sender_user_id"),
        "chat_messages",
        ["sender_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_messages_sender_user_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_room_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_id"), table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index(op.f("ix_appointments_status"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_scheduled_at"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_id"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_employee_id"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_customer_id"), table_name="appointments")
    op.drop_table("appointments")
    op.drop_index(op.f("ix_chat_rooms_id"), table_name="chat_rooms")
    op.drop_index(op.f("ix_chat_rooms_employee_id"), table_name="chat_rooms")
    op.drop_index(op.f("ix_chat_rooms_customer_id"), table_name="chat_rooms")
    op.drop_table("chat_rooms")
