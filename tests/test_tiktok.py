"""Tests for src/publishing/tiktok.py - TikTok API integration."""

from src.db import connect, init_schema, now_utc
from src.publishing.tiktok import (
    STATUS_FAILED,
    STATUS_PUBLISHED,
    _build_caption,
    update_queue_status,
)


def _seed_video(conn):
    """Create minimal chain: theme → verse → prayer → video. Return video id."""
    conn.execute(
        "INSERT INTO themes (slug, name, tone, is_active, created_at) "
        "VALUES ('t', 'T', 'c', 1, ?)",
        (now_utc(),),
    )
    conn.commit()
    tid = conn.execute("SELECT id FROM themes").fetchone()["id"]
    conn.execute(
        "INSERT INTO bible_verses (reference, text, theme_id, created_at) "
        "VALUES ('T 1:1', 'text', ?, ?)",
        (tid, now_utc()),
    )
    conn.commit()
    vid = conn.execute("SELECT id FROM bible_verses").fetchone()["id"]
    conn.execute(
        "INSERT INTO prayers (verse_id, theme_id, prayer_text, word_count, created_at) "
        "VALUES (?, ?, 'prayer', 1, ?)",
        (vid, tid, now_utc()),
    )
    conn.commit()
    pid = conn.execute("SELECT id FROM prayers").fetchone()["id"]
    conn.execute(
        "INSERT INTO generated_videos (prayer_id, file_path, duration_sec, resolution, "
        "file_size_bytes, created_at) VALUES (?, '/tmp/v.mp4', 65, '1080x1920', 1000, ?)",
        (pid, now_utc()),
    )
    conn.commit()
    return conn.execute("SELECT id FROM generated_videos").fetchone()["id"]


def test_build_caption_includes_verse_and_hashtags():
    caption = _build_caption("Psalm 23:4", "Grief & Loss")
    assert "Psalm 23:4" in caption
    assert "Grief & Loss" in caption
    assert "#faith" in caption
    assert "#prayer" in caption


def test_build_caption_respects_max_hashtags(tmp_path, monkeypatch):
    """With default config, should include up to 5 hashtags."""
    caption = _build_caption("John 3:16", "Faith")
    tags = [w for w in caption.split() if w.startswith("#")]
    assert len(tags) <= 5


def test_get_access_token_raises_without_env(monkeypatch):
    monkeypatch.delenv("TIKTOK_ACCESS_TOKEN", raising=False)
    from src.publishing.tiktok import _get_access_token

    try:
        _get_access_token()
        assert False, "Should have raised"
    except RuntimeError as exc:
        assert "TIKTOK_ACCESS_TOKEN" in str(exc)


def test_update_queue_status_published(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    video_id = _seed_video(conn)

    conn.execute(
        "INSERT INTO publish_queue (video_id, status, created_at, updated_at) "
        "VALUES (?, 'uploading', ?, ?)",
        (video_id, now_utc(), now_utc()),
    )
    conn.commit()
    qid = conn.execute("SELECT id FROM publish_queue").fetchone()["id"]

    update_queue_status(conn, qid, STATUS_PUBLISHED, external_post_id="tiktok_123")

    row = conn.execute("SELECT * FROM publish_queue WHERE id = ?", (qid,)).fetchone()
    assert row["status"] == "published"
    assert row["external_post_id"] == "tiktok_123"
    assert row["published_at"] is not None
    conn.close()


def test_update_queue_status_failed(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    video_id = _seed_video(conn)

    conn.execute(
        "INSERT INTO publish_queue (video_id, status, retry_count, created_at, updated_at) "
        "VALUES (?, 'uploading', 0, ?, ?)",
        (video_id, now_utc(), now_utc()),
    )
    conn.commit()
    qid = conn.execute("SELECT id FROM publish_queue").fetchone()["id"]

    update_queue_status(conn, qid, STATUS_FAILED, error_message="API timeout")

    row = conn.execute("SELECT * FROM publish_queue WHERE id = ?", (qid,)).fetchone()
    assert row["status"] == "failed"
    assert row["error_message"] == "API timeout"
    assert row["retry_count"] == 1
    conn.close()


def test_update_queue_status_increments_retry(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    video_id = _seed_video(conn)

    conn.execute(
        "INSERT INTO publish_queue (video_id, status, retry_count, created_at, updated_at) "
        "VALUES (?, 'uploading', 2, ?, ?)",
        (video_id, now_utc(), now_utc()),
    )
    conn.commit()
    qid = conn.execute("SELECT id FROM publish_queue").fetchone()["id"]

    update_queue_status(conn, qid, STATUS_FAILED, error_message="Error")
    row = conn.execute("SELECT retry_count FROM publish_queue WHERE id = ?", (qid,)).fetchone()
    assert row["retry_count"] == 3
    conn.close()
