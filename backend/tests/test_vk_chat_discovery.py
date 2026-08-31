import asyncio

from pytest import MonkeyPatch

from app.integrations.vk.client import VkClient


def test_list_chats_uses_community_context(monkeypatch: MonkeyPatch) -> None:
    client = VkClient(
        group_id=7,
        access_token="token",
        api_version="5.199",
        request_timeout=10,
        long_poll_wait=25,
    )

    async def fake_api(method: str, **params: object) -> object:
        assert method == "messages.getConversations"
        assert params == {"count": 200, "group_id": 7}
        return {"items": []}

    monkeypatch.setattr(client, "api", fake_api)

    assert asyncio.run(client.list_chats()) == []


def test_get_members_uses_community_context(monkeypatch: MonkeyPatch) -> None:
    client = VkClient(
        group_id=7,
        access_token="token",
        api_version="5.199",
        request_timeout=10,
        long_poll_wait=25,
    )

    async def fake_api(method: str, **params: object) -> object:
        assert method == "messages.getConversationMembers"
        assert params == {"peer_id": 2_000_000_001, "group_id": 7}
        return {"items": [], "profiles": []}

    monkeypatch.setattr(client, "api", fake_api)

    assert asyncio.run(client.get_members(2_000_000_001)) == []
