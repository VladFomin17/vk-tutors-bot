"""Create broadcast tables.

Revision ID: 20260714_03
Revises: 20260714_02
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_03"
down_revision: str | Sequence[str] | None = "20260714_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broadcasts",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("link", sa.String(length=2048), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmation_type", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "confirmation_type IN ('any_message', 'image')",
            name=op.f("ck_broadcasts_valid_confirmation_type"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_broadcasts")),
    )
    op.create_table(
        "broadcast_targets",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("broadcast_id", sa.BigInteger(), nullable=False),
        sa.Column("study_group_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["broadcast_id"], ["broadcasts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chat_id"], ["vk_chats.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["study_group_id"], ["study_groups.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_broadcast_targets")),
        sa.UniqueConstraint("broadcast_id", "chat_id", name="uq_broadcast_targets_broadcast_chat"),
        sa.UniqueConstraint(
            "broadcast_id",
            "study_group_id",
            name="uq_broadcast_targets_broadcast_study_group",
        ),
    )
    op.create_table(
        "broadcast_recipients",
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_user_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["target_id"], ["broadcast_targets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vk_user_id"], ["vk_users.vk_user_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("target_id", "vk_user_id", name=op.f("pk_broadcast_recipients")),
    )
    op.create_table(
        "outbound_messages",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("random_id", sa.Integer(), nullable=False),
        sa.Column("broadcast_token", sa.String(length=64), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vk_message_id", sa.BigInteger(), nullable=True),
        sa.Column("conversation_message_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("kind IN ('initial', 'reminder')", name=op.f("ck_outbound_messages_valid_kind")),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')",
            name=op.f("ck_outbound_messages_valid_status"),
        ),
        sa.ForeignKeyConstraint(["target_id"], ["broadcast_targets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbound_messages")),
        sa.UniqueConstraint("broadcast_token", name=op.f("uq_outbound_messages_broadcast_token")),
        sa.UniqueConstraint("target_id", "kind", name="uq_outbound_messages_target_kind"),
    )


def downgrade() -> None:
    op.drop_table("outbound_messages")
    op.drop_table("broadcast_recipients")
    op.drop_table("broadcast_targets")
    op.drop_table("broadcasts")
