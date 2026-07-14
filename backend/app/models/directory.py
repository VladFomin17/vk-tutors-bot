from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StudyGroup(Base):
    __tablename__ = "study_groups"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped["VkChat | None"] = relationship(back_populates="study_group")


class VkChat(Base):
    __tablename__ = "vk_chats"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    peer_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    title: Mapped[str | None] = mapped_column(String(255))
    study_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("study_groups.id", ondelete="SET NULL"),
        unique=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    study_group: Mapped[StudyGroup | None] = relationship(back_populates="chat")
    members: Mapped[list["ChatMember"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class VkUser(Base):
    __tablename__ = "vk_users"

    vk_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memberships: Mapped[list["ChatMember"]] = relationship(back_populates="user")


class ChatMember(Base):
    __tablename__ = "chat_members"
    __table_args__ = (
        CheckConstraint(
            "role IN ('unknown', 'student', 'tutor', 'leader')",
            name="valid_role",
        ),
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("vk_chats.id", ondelete="CASCADE"),
        primary_key=True,
    )
    vk_user_id: Mapped[int] = mapped_column(ForeignKey("vk_users.vk_user_id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(16), default="unknown", server_default="unknown")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped[VkChat] = relationship(back_populates="members")
    user: Mapped[VkUser] = relationship(back_populates="memberships")
