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
