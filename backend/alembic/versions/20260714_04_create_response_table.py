"""Create response table.

Revision ID: 20260714_04
Revises: 20260714_03
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_04"
down_revision: str | Sequence[str] | None = "20260714_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broadcast_responses",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("outbound_message_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_user_id", sa.BigInteger(), nullable=False),
        sa.Column("peer_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_message_id", sa.BigInteger(), nullable=False),
        sa.Column("conversation_message_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), server_default="", nullable=False),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_late", sa.Boolean(), server_default="false", nullable=False),
        sa.ForeignKeyConstraint(
            ["outbound_message_id"],
            ["outbound_messages.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["target_id"], ["broadcast_targets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vk_user_id"], ["vk_users.vk_user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_broadcast_responses")),
        sa.UniqueConstraint(
            "target_id",
            "vk_user_id",
            name="uq_broadcast_responses_recipient",
        ),
        sa.UniqueConstraint(
            "peer_id",
            "conversation_message_id",
            name="uq_broadcast_responses_vk_message",
        ),
    )


def downgrade() -> None:
    op.drop_table("broadcast_responses")
