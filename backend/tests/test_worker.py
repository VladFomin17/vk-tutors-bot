import asyncio

from pytest import MonkeyPatch

from app.integrations.vk.client import VkClient
from app.scheduler.worker import format_message
from app.services.outbox import OutboundJob


def make_job(*, kind: str = "initial", link: str | None = None) -> OutboundJob:
    return OutboundJob(
        id=1,
        peer_id=2_000_000_001,
        kind=kind,
        message_text="Пройдите опрос",
        link=link,
        random_id=123,
        broadcast_token="token",
        attempt_count=1,
    )


def test_format_message_adds_all_and_optional_link() -> None:
    assert format_message(make_job()) == "@all\n\nПройдите опрос"
    assert format_message(make_job(kind="reminder", link="https://example.com")) == (
        "@all\n\nНапоминание:\nПройдите опрос\n\nhttps://example.com"
    )


def test_send_message_passes_idempotency_payload(monkeypatch: MonkeyPatch) -> None:
    client = VkClient(
        group_id=1,
        access_token="token",
        api_version="5.199",
        request_timeout=10,
        long_poll_wait=25,
    )
    received: dict[str, object] = {}

    async def fake_api(method: str, **params: object) -> object:
        received["method"] = method
        received.update(params)
        return 0

    monkeypatch.setattr(client, "api", fake_api)

    result = asyncio.run(
        client.send_message(
            peer_id=2_000_000_001,
            random_id=123,
            message="@all test",
            broadcast_token="secret-token",
        )
    )

    assert result == 0
    assert received["method"] == "messages.send"
    assert received["random_id"] == 123
    assert received["payload"] == '{"broadcast_token":"secret-token"}'
