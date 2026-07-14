from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BroadcastResponse(Base):
    __tablename__ = "broadcast_responses"
    __table_args__ = (
        UniqueConstraint("target_id", "vk_user_id", name="uq_broadcast_responses_recipient"),
        UniqueConstraint(
            "peer_id",
            "conversation_message_id",
            name="uq_broadcast_responses_vk_message",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    target_id: Mapped[int] = mapped_column(
        ForeignKey("broadcast_targets.id", ondelete="CASCADE")
    )
    outbound_message_id: Mapped[int] = mapped_column(
        ForeignKey("outbound_messages.id", ondelete="RESTRICT")
    )
    vk_user_id: Mapped[int] = mapped_column(
        ForeignKey("vk_users.vk_user_id", ondelete="RESTRICT")
    )
    peer_id: Mapped[int] = mapped_column(BigInteger)
    vk_message_id: Mapped[int] = mapped_column(BigInteger)
    conversation_message_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(Text, default="", server_default="")
    attachments: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
    responded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_late: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
