"""TikTok Content Posting API integration.

Uses the TikTok Content Posting API v2 flow:
  1. Initialize upload → get publish_id + upload_url
  2. Upload video file to the upload_url
  3. Check publish status until complete

Docs: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import httpx

from src.config import get_config_value
from src.db import now_utc

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

# Publish statuses we track in the queue
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_UPLOADING = "uploading"
STATUS_PUBLISHED = "published"
STATUS_FAILED = "failed"


def _get_access_token() -> str:
    token = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError(
            "TIKTOK_ACCESS_TOKEN is not set. Add it to your .env file."
        )
    return token


def _build_caption(
    verse_ref: str,
    theme_name: str,
    db_path: str | None = None,
) -> str:
    """Build a TikTok caption with verse reference and hashtags."""
    hashtags = get_config_value(
        "publishing.hashtags",
        ["#faith", "#prayer", "#ChristianTikTok"],
        db_path,
    )
    max_tags = get_config_value("publishing.max_hashtags", 5, db_path)
    tags = " ".join(hashtags[:max_tags])
    return f"{verse_ref} | {theme_name}\n\n{tags}"


def init_direct_post(
    video_path: str,
    caption: str,
) -> dict[str, Any]:
    """Initialize a direct post upload with TikTok.

    Returns the API response dict containing publish_id and upload_url.
    """
    token = _get_access_token()
    file_size = Path(video_path).stat().st_size

    resp = httpx.post(
        f"{TIKTOK_API_BASE}/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "title": caption[:150],  # TikTok title max ~150 chars
                "privacy_level": "SELF_ONLY",  # Start as private for safety
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("error", {}).get("code") != "ok":
        raise RuntimeError(
            f"TikTok init failed: {data.get('error', {}).get('message', 'Unknown error')}"
        )

    return data.get("data", {})


def upload_video(upload_url: str, video_path: str) -> None:
    """Upload the video file to TikTok's upload_url."""
    file_size = Path(video_path).stat().st_size

    with open(video_path, "rb") as f:
        resp = httpx.put(
            upload_url,
            content=f.read(),
            headers={
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                "Content-Type": "video/mp4",
            },
            timeout=300,
        )
    resp.raise_for_status()


def check_publish_status(publish_id: str) -> dict[str, Any]:
    """Check the status of a TikTok publish request."""
    token = _get_access_token()

    resp = httpx.post(
        f"{TIKTOK_API_BASE}/post/publish/status/fetch/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={"publish_id": publish_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


def publish_video(
    video_path: str,
    verse_ref: str,
    theme_name: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Full publish flow: init → upload → return publish info.

    Returns dict with publish_id and status.
    """
    caption = _build_caption(verse_ref, theme_name, db_path)

    # Step 1: Init
    init_data = init_direct_post(video_path, caption)
    publish_id = init_data.get("publish_id", "")
    upload_url = init_data.get("upload_url", "")

    if not upload_url:
        raise RuntimeError("TikTok did not return an upload_url.")

    # Step 2: Upload
    upload_video(upload_url, video_path)

    return {
        "publish_id": publish_id,
        "caption": caption,
        "status": "uploaded",
    }


def update_queue_status(
    conn: sqlite3.Connection,
    queue_id: int,
    status: str,
    external_post_id: str | None = None,
    error_message: str | None = None,
) -> None:
    """Update a publish_queue row's status."""
    now = now_utc()
    if status == STATUS_PUBLISHED:
        conn.execute(
            """
            UPDATE publish_queue
            SET status = ?, published_at = ?, external_post_id = ?,
                error_message = NULL, updated_at = ?
            WHERE id = ?
            """,
            (status, now, external_post_id, now, queue_id),
        )
    elif status == STATUS_FAILED:
        conn.execute(
            """
            UPDATE publish_queue
            SET status = ?, error_message = ?,
                retry_count = retry_count + 1, updated_at = ?
            WHERE id = ?
            """,
            (status, error_message, now, queue_id),
        )
    else:
        conn.execute(
            "UPDATE publish_queue SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, queue_id),
        )
    conn.commit()
