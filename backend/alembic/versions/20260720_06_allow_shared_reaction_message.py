"""Allow multiple students to react to the same outbound message.

Revision ID: 20260720_06
Revises: 20260714_05
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260720_06"
down_revision: str | Sequence[str] | None = "20260714_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_broadcast_responses_vk_message",
        "broadcast_responses",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_broadcast_responses_vk_message",
        "broadcast_responses",
        ["peer_id", "conversation_message_id"],
    )
