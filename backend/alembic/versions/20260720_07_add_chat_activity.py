"""Add chat activity timestamp.

Revision ID: 20260720_07
Revises: 20260720_06
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260720_07"
down_revision: str | Sequence[str] | None = "20260720_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "vk_chats",
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("vk_chats", "last_activity_at")
