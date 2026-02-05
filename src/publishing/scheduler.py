"""Publishing scheduler: queue management, safety checks, and processing."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from src.config import get_config_value
from src.db import now_utc

# ---------------------------------------------------------------------------
# Safety constants
# ---------------------------------------------------------------------------
HUMAN_APPROVAL_THRESHOLD = 10  # First N posts require manual approval
MAX_CONSECUTIVE_FAILURES = 3   # Pause after this many failures in a row


# ---------------------------------------------------------------------------
# Queue helpers
# ---------------------------------------------------------------------------


def add_to_queue(
    conn: sqlite3.Connection,
    video_id: int,
    scheduled_at: str,
    platform: str = "tiktok",
) -> int:
    """Add a video to the publish queue. Returns the queue row id."""
    cur = conn.execute(
        """
        INSERT INTO publish_queue
            (video_id, platform, scheduled_at, status, created_at, updated_at)
        VALUES (?, ?, ?, 'pending', ?, ?)
        """,
        (video_id, platform, scheduled_at, now_utc(), now_utc()),
    )
    conn.commit()
    return cur.lastrowid


def get_queue(
    conn: sqlite3.Connection,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Fetch queue items, optionally filtered by status."""
    if status:
        cur = conn.execute(
            "SELECT * FROM publish_queue WHERE status = ? "
            "ORDER BY scheduled_at ASC LIMIT ?",
            (status, limit),
        )
    else:
        cur = conn.execute(
            "SELECT * FROM publish_queue ORDER BY scheduled_at ASC LIMIT ?",
            (limit,),
        )
    return [dict(row) for row in cur.fetchall()]


def get_due_items(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return queue items that are approved and past their scheduled time."""
    now = now_utc()
    cur = conn.execute(
        """
        SELECT * FROM publish_queue
        WHERE status = 'approved'
          AND scheduled_at <= ?
        ORDER BY scheduled_at ASC
        """,
        (now,),
    )
    return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Safety checks
# ---------------------------------------------------------------------------


def check_min_interval(
    conn: sqlite3.Connection,
    db_path: str | None = None,
) -> bool:
    """Return True if enough time has passed since the last published post."""
    min_hours = get_config_value(
        "publishing.min_hours_between_posts", 4, db_path
    )

    last = conn.execute(
        "SELECT published_at FROM publish_queue "
        "WHERE status = 'published' ORDER BY published_at DESC LIMIT 1"
    ).fetchone()

    if last is None or last["published_at"] is None:
        return True

    last_dt = datetime.fromisoformat(last["published_at"])
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)
    cutoff = last_dt + timedelta(hours=min_hours)
    now_dt = datetime.now(timezone.utc)
    return now_dt >= cutoff


def check_consecutive_failures(conn: sqlite3.Connection) -> bool:
    """Return True if we have NOT hit the max consecutive failure limit."""
    cur = conn.execute(
        "SELECT status FROM publish_queue "
        "ORDER BY updated_at DESC LIMIT ?",
        (MAX_CONSECUTIVE_FAILURES,),
    )
    rows = cur.fetchall()
    if len(rows) < MAX_CONSECUTIVE_FAILURES:
        return True
    return not all(row["status"] == "failed" for row in rows)


def needs_human_approval(conn: sqlite3.Connection) -> bool:
    """Return True if the next post requires human approval.

    The first HUMAN_APPROVAL_THRESHOLD published posts must be approved
    manually. After that, posts can be auto-approved.
    """
    cur = conn.execute(
        "SELECT COUNT(*) as cnt FROM publish_queue WHERE status = 'published'"
    )
    published_count = cur.fetchone()["cnt"]
    return published_count < HUMAN_APPROVAL_THRESHOLD


def approve_item(conn: sqlite3.Connection, queue_id: int) -> bool:
    """Mark a pending queue item as approved. Returns True if updated."""
    cur = conn.execute(
        "UPDATE publish_queue SET status = 'approved', updated_at = ? "
        "WHERE id = ? AND status = 'pending'",
        (now_utc(), queue_id),
    )
    conn.commit()
    return cur.rowcount > 0


def can_publish(
    conn: sqlite3.Connection,
    db_path: str | None = None,
) -> tuple[bool, str]:
    """Run all safety checks. Returns (ok, reason)."""
    if not check_consecutive_failures(conn):
        return False, (
            f"Paused: {MAX_CONSECUTIVE_FAILURES} consecutive failures. "
            "Review errors before continuing."
        )

    if not check_min_interval(conn, db_path):
        min_hours = get_config_value(
            "publishing.min_hours_between_posts", 4, db_path
        )
        return False, f"Too soon: must wait {min_hours}h between posts."

    return True, "OK"


# ---------------------------------------------------------------------------
# Process queue
# ---------------------------------------------------------------------------


def process_queue(
    conn: sqlite3.Connection,
    db_path: str | None = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Process due items in the publish queue.

    Returns a list of result dicts with queue_id, status, and details.
    """
    from src.publishing.tiktok import (
        STATUS_FAILED,
        STATUS_PUBLISHED,
        STATUS_UPLOADING,
        publish_video,
        update_queue_status,
    )

    ok, reason = can_publish(conn, db_path)
    if not ok:
        return [{"queue_id": None, "status": "blocked", "reason": reason}]

    due = get_due_items(conn)
    if not due:
        return [{"queue_id": None, "status": "empty", "reason": "No due items."}]

    results: list[dict[str, Any]] = []

    for item in due:
        # Re-check interval for each item
        if not check_min_interval(conn, db_path):
            results.append({
                "queue_id": item["id"],
                "status": "skipped",
                "reason": "Min interval not met.",
            })
            break

        # Load video info
        video = conn.execute(
            "SELECT * FROM generated_videos WHERE id = ?",
            (item["video_id"],),
        ).fetchone()

        if not video:
            update_queue_status(
                conn, item["id"], STATUS_FAILED,
                error_message="Video record not found.",
            )
            results.append({
                "queue_id": item["id"],
                "status": "failed",
                "reason": "Video not found.",
            })
            continue

        # Load verse + theme for caption
        prayer = conn.execute(
            "SELECT * FROM prayers WHERE id = ?", (video["prayer_id"],)
        ).fetchone()
        verse = conn.execute(
            "SELECT reference FROM bible_verses WHERE id = ?",
            (prayer["verse_id"],),
        ).fetchone() if prayer else None
        theme = conn.execute(
            "SELECT name FROM themes WHERE id = ?",
            (prayer["theme_id"],),
        ).fetchone() if prayer else None

        verse_ref = verse["reference"] if verse else "Scripture"
        theme_name = theme["name"] if theme else "Faith"

        if dry_run:
            results.append({
                "queue_id": item["id"],
                "status": "dry_run",
                "video_path": video["file_path"],
                "verse_ref": verse_ref,
            })
            continue

        # Publish
        update_queue_status(conn, item["id"], STATUS_UPLOADING)
        try:
            pub_info = publish_video(
                video["file_path"], verse_ref, theme_name, db_path
            )
            update_queue_status(
                conn, item["id"], STATUS_PUBLISHED,
                external_post_id=pub_info.get("publish_id"),
            )
            results.append({
                "queue_id": item["id"],
                "status": "published",
                "publish_id": pub_info.get("publish_id"),
            })
        except Exception as exc:
            update_queue_status(
                conn, item["id"], STATUS_FAILED,
                error_message=str(exc)[:500],
            )
            results.append({
                "queue_id": item["id"],
                "status": "failed",
                "reason": str(exc)[:200],
            })

    return results
