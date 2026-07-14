"""Create directory tables.

Revision ID: 20260714_01
Revises:
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "study_groups",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_study_groups")),
        sa.UniqueConstraint("name", name=op.f("uq_study_groups_name")),
    )
    op.create_table(
        "vk_chats",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("peer_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("study_group_id", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_group_id"],
            ["study_groups.id"],
            name=op.f("fk_vk_chats_study_group_id_study_groups"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vk_chats")),
        sa.UniqueConstraint("peer_id", name=op.f("uq_vk_chats_peer_id")),
        sa.UniqueConstraint("study_group_id", name=op.f("uq_vk_chats_study_group_id")),
    )
    op.create_table(
        "vk_users",
        sa.Column("vk_user_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("vk_user_id", name=op.f("pk_vk_users")),
    )
    op.create_table(
        "chat_members",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=16), server_default="unknown", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "role IN ('unknown', 'student', 'tutor', 'leader')",
            name=op.f("ck_chat_members_valid_role"),
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["vk_chats.id"],
            name=op.f("fk_chat_members_chat_id_vk_chats"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vk_user_id"],
            ["vk_users.vk_user_id"],
            name=op.f("fk_chat_members_vk_user_id_vk_users"),
        ),
        sa.PrimaryKeyConstraint("chat_id", "vk_user_id", name=op.f("pk_chat_members")),
    )


def downgrade() -> None:
    op.drop_table("chat_members")
    op.drop_table("vk_users")
    op.drop_table("vk_chats")
    op.drop_table("study_groups")
