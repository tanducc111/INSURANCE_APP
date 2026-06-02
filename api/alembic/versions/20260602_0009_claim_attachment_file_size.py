"""add claim attachment file size

Revision ID: 20260602_0009
Revises: 20260601_0008
Create Date: 2026-06-02 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260602_0009"
down_revision: str | None = "20260601_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "claim_attachments",
        sa.Column("file_size", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("claim_attachments", "file_size")
