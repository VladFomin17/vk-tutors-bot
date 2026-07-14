from sqlalchemy.orm import configure_mappers

from app.db.base import Base
from app.models import BroadcastTarget, ChatMember, StudyGroup, VkChat, VkUser


def test_directory_models_are_registered() -> None:
    configure_mappers()

    assert set(Base.metadata.tables) == {
        "auth_sessions",
        "broadcast_recipients",
        "broadcast_responses",
        "broadcast_targets",
        "broadcasts",
        "chat_members",
        "outbound_messages",
        "study_groups",
        "vk_chats",
        "vk_users",
    }
    assert ChatMember.chat.property.mapper.class_ is VkChat
    assert ChatMember.user.property.mapper.class_ is VkUser
    assert StudyGroup.chat.property.mapper.class_ is VkChat
    assert BroadcastTarget.broadcast.property.mapper.class_.__name__ == "Broadcast"
