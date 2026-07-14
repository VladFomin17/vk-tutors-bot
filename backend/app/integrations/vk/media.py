import asyncio
import logging
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.services.media import MediaFile, MediaJob

ALLOWED_HOST_SUFFIXES = (".userapi.com", ".vkuserphoto.ru")
logger = logging.getLogger(__name__)


class MediaDownloadError(OSError):
    pass


async def store_images(
    job: MediaJob,
    root: Path,
    max_bytes: int,
    timeout: int,
) -> list[MediaFile]:
    stored: list[MediaFile] = []
    try:
        for position, url in enumerate(_photo_urls(job.attachments)):
            data, content_type, extension = await asyncio.to_thread(
                _download_image, url, max_bytes, timeout
            )
            storage_name = (
                f"{job.response_id}/{job.conversation_message_id}-{position}.{extension}"
            )
            target = root / storage_name
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(f"{target.suffix}.tmp")
            try:
                temporary.write_bytes(data)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            stored.append(MediaFile(storage_name, content_type, len(data)))
        return stored
    except OSError:
        remove_files(root, [file.storage_name for file in stored])
        raise


def remove_files(root: Path, storage_names: list[str]) -> None:
    resolved_root = root.resolve()
    for storage_name in storage_names:
        path = (resolved_root / storage_name).resolve()
        if not path.is_relative_to(resolved_root):
            logger.error("Refused to remove image outside media root: %s", storage_name)
            continue
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to remove stored image %s", storage_name, exc_info=True)


def _photo_urls(attachments: list[dict[str, object]]) -> list[str]:
    urls: list[str] = []
    for attachment in attachments:
        photo = attachment.get("photo") if attachment.get("type") == "photo" else None
        if not isinstance(photo, dict):
            continue
        original = photo.get("orig_photo")
        url = original.get("url") if isinstance(original, dict) else None
        if not isinstance(url, str):
            sizes = photo.get("sizes")
            last_size = sizes[-1] if isinstance(sizes, list) and sizes else None
            url = last_size.get("url") if isinstance(last_size, dict) else None
        if isinstance(url, str):
            urls.append(url)
    return urls


def _download_image(url: str, max_bytes: int, timeout: int) -> tuple[bytes, str, str]:
    _validate_url(url)
    request = Request(url, headers={"User-Agent": "vk-tutors-bot/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            _validate_url(response.geturl())
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > max_bytes:
                raise MediaDownloadError("VK image is too large")
            data = response.read(max_bytes + 1)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise MediaDownloadError("VK image download failed") from error
    if len(data) > max_bytes:
        raise MediaDownloadError("VK image is too large")
    content_type, extension = _detect_image(data)
    return data, content_type, extension


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if parsed.scheme != "https" or not any(
        hostname == suffix[1:] or hostname.endswith(suffix)
        for suffix in ALLOWED_HOST_SUFFIXES
    ):
        raise MediaDownloadError("Untrusted VK image URL")


def _detect_image(data: bytes) -> tuple[str, str]:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", "gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    raise MediaDownloadError("VK attachment is not a supported image")
