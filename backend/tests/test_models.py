from sqlalchemy.orm import configure_mappers

from app.db.base import Base
from app.models import ChatMember, StudyGroup, VkChat, VkUser


def test_directory_models_are_registered() -> None:
    configure_mappers()

    assert set(Base.metadata.tables) == {
        "chat_members",
        "study_groups",
        "vk_chats",
        "vk_users",
    }
    assert ChatMember.chat.property.mapper.class_ is VkChat
    assert ChatMember.user.property.mapper.class_ is VkUser
    assert StudyGroup.chat.property.mapper.class_ is VkChat
