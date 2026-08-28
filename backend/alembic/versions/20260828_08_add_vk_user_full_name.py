"""Add manually assigned full names to VK users.

Revision ID: 20260828_08
Revises: 20260720_07
Create Date: 2026-08-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260828_08"
down_revision: str | Sequence[str] | None = "20260720_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("vk_users", sa.Column("full_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("vk_users", "full_name")
