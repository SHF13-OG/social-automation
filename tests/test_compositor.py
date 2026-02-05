"""Tests for src/media/compositor.py - FFmpeg video compositing and storage."""

import json

from src.db import connect, init_schema, now_utc
from src.media.compositor import _build_text_filter, save_video_record


def _seed_prayer_with_audio(conn):
    """Seed theme, verse, prayer, audio and return (prayer_id, audio_id)."""
    conn.execute(
        "INSERT INTO themes (slug, name, tone, is_active, created_at) "
        "VALUES ('test', 'Test', 'comforting', 1, ?)",
        (now_utc(),),
    )
    conn.commit()
    theme_id = conn.execute("SELECT id FROM themes WHERE slug = 'test'").fetchone()["id"]

    conn.execute(
        "INSERT INTO bible_verses (reference, text, theme_id, created_at) "
        "VALUES ('Test 1:1', 'Test verse', ?, ?)",
        (theme_id, now_utc()),
    )
    conn.commit()
    verse_id = conn.execute("SELECT id FROM bible_verses").fetchone()["id"]

    conn.execute(
        "INSERT INTO prayers (verse_id, theme_id, prayer_text, word_count, created_at) "
        "VALUES (?, ?, 'Lord, hear us.', 3, ?)",
        (verse_id, theme_id, now_utc()),
    )
    conn.commit()
    prayer_id = conn.execute("SELECT id FROM prayers").fetchone()["id"]

    conn.execute(
        "INSERT INTO audio_files (prayer_id, file_path, voice_id, created_at) "
        "VALUES (?, '/tmp/test.mp3', 'voice1', ?)",
        (prayer_id, now_utc()),
    )
    conn.commit()
    audio_id = conn.execute("SELECT id FROM audio_files").fetchone()["id"]

    return prayer_id, audio_id


def test_build_text_filter_contains_verse_ref():
    f = _build_text_filter("Psalm 23:4", "The Lord is my shepherd", 65.0)
    assert "Psalm 23" in f
    assert "drawtext" in f


def test_build_text_filter_escapes_colons():
    f = _build_text_filter("John 3:16", "For God so loved", 60.0)
    # Colons should be escaped for FFmpeg
    assert "\\:" in f


def test_build_text_filter_truncates_long_text():
    long_text = "A" * 200
    f = _build_text_filter("Test 1:1", long_text, 60.0)
    # Should contain truncated text (117 chars + "...")
    assert "..." in f


def test_save_video_record(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    prayer_id, audio_id = _seed_prayer_with_audio(conn)

    video_info = {
        "file_path": "/tmp/video_1.mp4",
        "duration_sec": 65.2,
        "resolution": "1080x1920",
        "file_size_bytes": 15_000_000,
    }
    vid = save_video_record(
        conn, prayer_id, audio_id, [1, 2], video_info
    )
    assert vid > 0

    row = conn.execute("SELECT * FROM generated_videos WHERE id = ?", (vid,)).fetchone()
    assert row["prayer_id"] == prayer_id
    assert row["audio_id"] == audio_id
    assert json.loads(row["footage_ids"]) == [1, 2]
    assert row["duration_sec"] == 65.2
    assert row["resolution"] == "1080x1920"
    assert row["file_size_bytes"] == 15_000_000
    conn.close()


def test_save_video_record_stores_font_info(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    prayer_id, audio_id = _seed_prayer_with_audio(conn)

    video_info = {
        "file_path": "/tmp/video_2.mp4",
        "duration_sec": 62.0,
        "resolution": "1080x1920",
        "file_size_bytes": 10_000_000,
    }
    vid = save_video_record(conn, prayer_id, audio_id, [], video_info)
    row = conn.execute("SELECT * FROM generated_videos WHERE id = ?", (vid,)).fetchone()

    # Should have default font info from config
    assert row["font_style"] is not None
    assert row["font_size"] is not None
    assert row["text_position"] is not None
    conn.close()
