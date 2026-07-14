"""Create response media table.

Revision ID: 20260714_05
Revises: 20260714_04
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_05"
down_revision: str | Sequence[str] | None = "20260714_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "response_media",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("response_id", sa.BigInteger(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("storage_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["response_id"],
            ["broadcast_responses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_response_media")),
        sa.UniqueConstraint(
            "response_id",
            "position",
            name="uq_response_media_position",
        ),
        sa.UniqueConstraint("storage_name", name="uq_response_media_storage_name"),
    )


def downgrade() -> None:
    op.drop_table("response_media")
