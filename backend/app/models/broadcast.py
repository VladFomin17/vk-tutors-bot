from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Broadcast(Base):
    __tablename__ = "broadcasts"
    __table_args__ = (
        CheckConstraint(
            "confirmation_type IN ('any_message', 'image')",
            name="valid_confirmation_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    message_text: Mapped[str] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(2048))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmation_type: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    targets: Mapped[list["BroadcastTarget"]] = relationship(
        back_populates="broadcast",
        cascade="all, delete-orphan",
    )


class BroadcastTarget(Base):
    __tablename__ = "broadcast_targets"
    __table_args__ = (
        UniqueConstraint(
            "broadcast_id",
            "study_group_id",
            name="uq_broadcast_targets_broadcast_study_group",
        ),
        UniqueConstraint(
            "broadcast_id",
            "chat_id",
            name="uq_broadcast_targets_broadcast_chat",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    broadcast_id: Mapped[int] = mapped_column(ForeignKey("broadcasts.id", ondelete="CASCADE"))
    study_group_id: Mapped[int] = mapped_column(ForeignKey("study_groups.id", ondelete="RESTRICT"))
    chat_id: Mapped[int] = mapped_column(ForeignKey("vk_chats.id", ondelete="RESTRICT"))

    broadcast: Mapped[Broadcast] = relationship(back_populates="targets")
    recipients: Mapped[list["BroadcastRecipient"]] = relationship(
        back_populates="target",
        cascade="all, delete-orphan",
    )
    outbound_messages: Mapped[list["OutboundMessage"]] = relationship(
        back_populates="target",
        cascade="all, delete-orphan",
    )


class BroadcastRecipient(Base):
    __tablename__ = "broadcast_recipients"

    target_id: Mapped[int] = mapped_column(
        ForeignKey("broadcast_targets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    vk_user_id: Mapped[int] = mapped_column(
        ForeignKey("vk_users.vk_user_id", ondelete="RESTRICT"),
        primary_key=True,
    )

    target: Mapped[BroadcastTarget] = relationship(back_populates="recipients")


class OutboundMessage(Base):
    __tablename__ = "outbound_messages"
    __table_args__ = (
        CheckConstraint("kind IN ('initial', 'reminder')", name="valid_kind"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')",
            name="valid_status",
        ),
        UniqueConstraint("target_id", "kind", name="uq_outbound_messages_target_kind"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("broadcast_targets.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="pending", server_default="pending")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    random_id: Mapped[int] = mapped_column(Integer)
    broadcast_token: Mapped[str] = mapped_column(String(64), unique=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(String(1000))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    vk_message_id: Mapped[int | None] = mapped_column(BigInteger)
    conversation_message_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    target: Mapped[BroadcastTarget] = relationship(back_populates="outbound_messages")
