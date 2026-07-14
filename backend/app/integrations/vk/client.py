import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class VkApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChatReference:
    peer_id: int
    title: str | None


@dataclass(frozen=True)
class LongPollEndpoint:
    server: str
    key: str
    ts: str


def _request_json(
    url: str,
    *,
    data: dict[str, str] | None = None,
    timeout: int,
) -> dict[str, Any]:
    encoded_data = urlencode(data).encode() if data is not None else None
    request = Request(url, data=encoded_data, headers={"User-Agent": "vk-tutors-bot/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(5_000_001)
    except (HTTPError, URLError, TimeoutError) as error:
        raise VkApiError("VK request failed") from error

    if len(body) > 5_000_000:
        raise VkApiError("VK response is too large")
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VkApiError("VK returned invalid JSON") from error
    if not isinstance(payload, dict):
        raise VkApiError("VK returned an invalid response")
    return payload


class VkClient:
    def __init__(
        self,
        *,
        group_id: int,
        access_token: str,
        api_version: str,
        request_timeout: int,
        long_poll_wait: int,
    ) -> None:
        self.group_id = group_id
        self._access_token = access_token
        self._api_version = api_version
        self._request_timeout = request_timeout
        self._long_poll_wait = long_poll_wait

    async def api(self, method: str, **params: object) -> Any:
        form = {
            **{name: str(value) for name, value in params.items()},
            "access_token": self._access_token,
            "v": self._api_version,
        }
        payload = await asyncio.to_thread(
            _request_json,
            f"https://api.vk.com/method/{method}",
            data=form,
            timeout=self._request_timeout,
        )
        if "error" in payload:
            error = payload["error"]
            if isinstance(error, dict):
                code = error.get("error_code", "unknown")
                message = error.get("error_msg", "unknown error")
                raise VkApiError(f"VK API error {code}: {message}")
            raise VkApiError("VK API returned an error")
        if "response" not in payload:
            raise VkApiError("VK API response is missing data")
        return payload["response"]

    async def list_chats(self) -> list[ChatReference]:
        response = await self.api("messages.getConversations", count=200)
        if not isinstance(response, dict) or not isinstance(response.get("items"), list):
            raise VkApiError("VK conversations response is invalid")

        chats: list[ChatReference] = []
        for item in response["items"]:
            if not isinstance(item, dict) or not isinstance(item.get("conversation"), dict):
                continue
            conversation = item["conversation"]
            peer = conversation.get("peer")
            if not isinstance(peer, dict) or not isinstance(peer.get("id"), int):
                continue
            peer_id = peer["id"]
            if peer_id < 2_000_000_000:
                continue
            settings = conversation.get("chat_settings")
            title = settings.get("title") if isinstance(settings, dict) else None
            if isinstance(title, str) and len(title) > 255:
                raise VkApiError("VK chat title is too long")
            chats.append(ChatReference(peer_id, title if isinstance(title, str) else None))
        return chats

    async def get_members(self, peer_id: int) -> list[tuple[int, str, str]]:
        response = await self.api("messages.getConversationMembers", peer_id=peer_id)
        if not isinstance(response, dict):
            raise VkApiError("VK members response is invalid")
        items = response.get("items")
        profiles = response.get("profiles")
        if not isinstance(items, list) or not isinstance(profiles, list):
            raise VkApiError("VK members response is incomplete")

        profiles_by_id = {
            profile["id"]: profile
            for profile in profiles
            if isinstance(profile, dict) and isinstance(profile.get("id"), int)
        }
        members: dict[int, tuple[int, str, str]] = {}
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("member_id"), int):
                raise VkApiError("VK member entry is invalid")
            member_id = item["member_id"]
            if member_id <= 0:
                continue
            profile = profiles_by_id.get(member_id)
            if profile is None:
                raise VkApiError("VK member profile is missing")
            first_name = profile.get("first_name")
            last_name = profile.get("last_name")
            if not isinstance(first_name, str) or not isinstance(last_name, str):
                raise VkApiError("VK member name is invalid")
            if len(first_name) > 100 or len(last_name) > 100:
                raise VkApiError("VK member name is too long")
            members[member_id] = (member_id, first_name, last_name)
        return list(members.values())

    async def get_long_poll_endpoint(self) -> LongPollEndpoint:
        response = await self.api("groups.getLongPollServer", group_id=self.group_id)
        if not isinstance(response, dict):
            raise VkApiError("VK Long Poll response is invalid")
        server = response.get("server")
        key = response.get("key")
        ts = response.get("ts")
        if not isinstance(server, str) or not server.startswith("https://"):
            raise VkApiError("VK Long Poll server is invalid")
        if not isinstance(key, str) or not isinstance(ts, str):
            raise VkApiError("VK Long Poll credentials are invalid")
        return LongPollEndpoint(server, key, ts)

    async def poll(self, endpoint: LongPollEndpoint) -> tuple[str, list[dict[str, Any]]] | None:
        query = urlencode(
            {
                "act": "a_check",
                "key": endpoint.key,
                "ts": endpoint.ts,
                "wait": self._long_poll_wait,
            }
        )
        url = f"{endpoint.server}?{query}"
        payload = await asyncio.to_thread(
            _request_json,
            url,
            timeout=self._long_poll_wait + self._request_timeout,
        )
        if "failed" in payload:
            if payload["failed"] == 1 and isinstance(payload.get("ts"), str):
                return payload["ts"], []
            return None
        ts = payload.get("ts")
        updates = payload.get("updates")
        if not isinstance(ts, str) or not isinstance(updates, list):
            raise VkApiError("VK Long Poll update is invalid")
        return ts, [update for update in updates if isinstance(update, dict)]
