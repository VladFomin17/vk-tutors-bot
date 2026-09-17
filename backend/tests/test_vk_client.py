import asyncio

from pytest import MonkeyPatch

from app.integrations.vk.client import VkClient


def test_get_chat_reads_title(monkeypatch: MonkeyPatch) -> None:
    client = VkClient(
        group_id=1,
        access_token="token",
        api_version="5.199",
        request_timeout=10,
        long_poll_wait=25,
    )

    async def fake_api(method: str, **params: object) -> object:
        assert method == "messages.getConversationsById"
        peer_id = params["peer_ids"]
        return {
            "items": [
                {
                    "peer": {"id": peer_id},
                    "chat_settings": {"title": "ИВТ-101"},
                }
            ]
        }

    monkeypatch.setattr(client, "api", fake_api)

    reference = asyncio.run(client.get_chat(2_000_000_001))

    assert reference.peer_id == 2_000_000_001
    assert reference.title == "ИВТ-101"


def test_get_message_payload(monkeypatch: MonkeyPatch) -> None:
    client = VkClient(
        group_id=1,
        access_token="token",
        api_version="5.199",
        request_timeout=10,
        long_poll_wait=25,
    )

    async def fake_api(method: str, **params: object) -> object:
        assert method == "messages.getByConversationMessageId"
        assert params == {
            "peer_id": 2_000_000_001,
            "conversation_message_ids": "42",
            "group_id": 1,
        }
        return {
            "items": [
                {
                    "conversation_message_id": 42,
                    "payload": '{"broadcast_token":"token"}',
                }
            ]
        }

    monkeypatch.setattr(client, "api", fake_api)

    assert asyncio.run(client.get_message_payload(2_000_000_001, 42)) == (
        '{"broadcast_token":"token"}'
    )


def test_get_reacted_peers(monkeypatch: MonkeyPatch) -> None:
    client = VkClient(
        group_id=1,
        access_token="token",
        api_version="5.199",
        request_timeout=10,
        long_poll_wait=25,
    )

    async def fake_api(method: str, **params: object) -> object:
        assert method == "messages.getReactedPeers"
        assert params == {"peer_id": 2_000_000_001, "cmid": 42}
        return {"reactions": [{"peer_id": 123, "reaction_id": 1}]}

    monkeypatch.setattr(client, "api", fake_api)

    assert asyncio.run(client.get_reacted_peers(2_000_000_001, 42)) == [123]
