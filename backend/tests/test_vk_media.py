import asyncio
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from app.integrations.vk import media as vk_media
from app.integrations.vk.media import (
    MediaDownloadError,
    _detect_image,
    _photo_urls,
    _validate_url,
)
from app.services.media import MediaJob


def test_vk_media_accepts_only_supported_vk_images() -> None:
    attachments = [
        {
            "type": "photo",
            "photo": {
                "orig_photo": {"url": "https://sun9-1.userapi.com/image.jpg"},
                "sizes": [{"url": "https://sun9-1.userapi.com/small.jpg"}],
            },
        }
    ]

    assert _photo_urls(attachments) == ["https://sun9-1.userapi.com/image.jpg"]
    assert _detect_image(b"\xff\xd8\xffdata") == ("image/jpeg", "jpg")
    _validate_url("https://sun9-1.userapi.com/image.jpg")
    with pytest.raises(MediaDownloadError):
        _validate_url("http://127.0.0.1/private.jpg")


def test_vk_media_is_stored_under_response_directory(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        vk_media,
        "_download_image",
        lambda *_: (b"\xff\xd8\xffdata", "image/jpeg", "jpg"),
    )
    job = MediaJob(
        response_id=7,
        conversation_message_id=42,
        attachments=[
            {
                "type": "photo",
                "photo": {"orig_photo": {"url": "https://sun9-1.userapi.com/image.jpg"}},
            }
        ],
    )

    files = asyncio.run(vk_media.store_images(job, tmp_path, 1024, 1))

    assert files[0].storage_name == "7/42-0.jpg"
    assert (tmp_path / files[0].storage_name).read_bytes() == b"\xff\xd8\xffdata"
