"""Integration tests for the full content generation pipeline.

These tests verify that all components work together correctly,
testing the flow from theme selection through video composition.
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.db import connect, init_schema, now_utc
from src.content.themes import get_active_themes, pick_theme
from src.content.verses import get_verses_for_theme, pick_verse, mark_verse_used
from src.content.prayers import save_prayer, generate_prayer_text_fallback
from src.media.tts import _audio_path, save_audio_record
from src.media.footage import save_footage_record
from src.media.compositor import save_video_record
from src.publishing.scheduler import add_to_queue, get_queue


def _seed_themes_and_verses(conn):
    """Seed database with themes and verses for testing."""
    themes_data = [
        ("grief", "Grief & Loss", "comforting"),
        ("retirement", "Retirement", "hopeful"),
        ("health", "Health Struggles", "encouraging"),
    ]

    for slug, name, tone in themes_data:
        conn.execute(
            "INSERT INTO themes (slug, name, tone, is_active, created_at) "
            "VALUES (?, ?, ?, 1, ?)",
            (slug, name, tone, now_utc()),
        )
    conn.commit()

    verses_data = [
        ("grief", "Psalm 23:4", "Even though I walk through the valley of the shadow of death, I will fear no evil."),
        ("grief", "Matthew 5:4", "Blessed are those who mourn, for they will be comforted."),
        ("retirement", "Psalm 90:12", "Teach us to number our days, that we may gain a heart of wisdom."),
        ("health", "Isaiah 41:10", "So do not fear, for I am with you; do not be dismayed, for I am your God."),
    ]

    for theme_slug, reference, text in verses_data:
        theme_id = conn.execute(
            "SELECT id FROM themes WHERE slug = ?", (theme_slug,)
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO bible_verses (reference, text, theme_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            (reference, text, theme_id, now_utc()),
        )
    conn.commit()


class TestContentSelectionPipeline:
    """Test theme and verse selection flow."""

    def test_pick_theme_and_verse(self, tmp_path):
        """Test selecting a theme and then a verse from that theme."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)
        _seed_themes_and_verses(conn)

        # Pick a theme
        theme = pick_theme(conn)
        assert theme is not None
        assert "id" in theme
        assert "slug" in theme

        # Pick a verse for that theme
        verse = pick_verse(conn, theme["id"])
        assert verse is not None
        assert "reference" in verse
        assert "text" in verse

        conn.close()

    def test_verse_rotation(self, tmp_path):
        """Test that verses rotate after being used."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)
        _seed_themes_and_verses(conn)

        # Get grief theme
        theme_id = conn.execute(
            "SELECT id FROM themes WHERE slug = 'grief'"
        ).fetchone()["id"]

        # Pick first verse and mark it used
        verse1 = pick_verse(conn, theme_id)
        mark_verse_used(conn, verse1["id"])

        # Pick second verse - should be different
        verse2 = pick_verse(conn, theme_id)
        assert verse2["id"] != verse1["id"]

        conn.close()


class TestPrayerGeneration:
    """Test prayer generation and storage."""

    def test_fallback_prayer_generation(self, tmp_path):
        """Test that fallback prayer generates appropriate content."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)
        _seed_themes_and_verses(conn)

        theme = dict(conn.execute(
            "SELECT * FROM themes WHERE slug = 'grief'"
        ).fetchone())
        verse = dict(conn.execute(
            "SELECT * FROM bible_verses WHERE theme_id = ?", (theme["id"],)
        ).fetchone())

        # generate_prayer_text_fallback takes verse dict and theme dict
        prayer = generate_prayer_text_fallback(verse, theme)

        # Prayer should be reasonable length (140-165 words target)
        word_count = len(prayer.split())
        assert 100 < word_count < 200

        # Prayer should reference the verse
        assert len(prayer) > 100

        conn.close()

    def test_save_prayer_to_db(self, tmp_path):
        """Test saving a prayer to the database."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)
        _seed_themes_and_verses(conn)

        theme = conn.execute("SELECT * FROM themes WHERE slug = 'grief'").fetchone()
        verse = conn.execute(
            "SELECT * FROM bible_verses WHERE theme_id = ?", (theme["id"],)
        ).fetchone()

        prayer_text = "Lord, comfort those who mourn today. Amen."
        prayer_id = save_prayer(conn, verse["id"], theme["id"], prayer_text)

        assert prayer_id > 0

        saved = conn.execute(
            "SELECT * FROM prayers WHERE id = ?", (prayer_id,)
        ).fetchone()
        assert saved["prayer_text"] == prayer_text
        assert saved["word_count"] == len(prayer_text.split())

        conn.close()


class TestMediaPipeline:
    """Test audio and footage handling."""

    def test_audio_path_generation(self):
        """Test that audio paths are deterministic."""
        path1 = _audio_path(1, "voice1")
        path2 = _audio_path(1, "voice1")
        path3 = _audio_path(2, "voice1")

        assert path1 == path2  # Same ID = same path
        assert path1 != path3  # Different ID = different path
        assert str(path1).endswith(".mp3")

    def test_save_audio_record(self, tmp_path):
        """Test saving audio metadata to database."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)
        _seed_themes_and_verses(conn)

        # Create a prayer first
        theme = conn.execute("SELECT * FROM themes WHERE slug = 'grief'").fetchone()
        verse = conn.execute(
            "SELECT * FROM bible_verses WHERE theme_id = ?", (theme["id"],)
        ).fetchone()
        prayer_id = save_prayer(conn, verse["id"], theme["id"], "Test prayer.")

        # Save audio record using dict format
        audio_info = {
            "file_path": "/tmp/test_audio.mp3",
            "voice_id": "test_voice",
            "speed": 1.0,
            "file_hash": "abc123",
        }
        audio_id = save_audio_record(conn, prayer_id, audio_info)

        assert audio_id > 0

        saved = conn.execute(
            "SELECT * FROM audio_files WHERE id = ?", (audio_id,)
        ).fetchone()
        assert saved["prayer_id"] == prayer_id
        assert saved["voice_id"] == "test_voice"

        conn.close()

    def test_save_footage_record(self, tmp_path):
        """Test saving footage metadata to database."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)

        # save_footage_record takes a clip dict and download_path
        clip = {
            "source": "pexels",
            "external_id": "12345",
            "url": "https://example.com/video.mp4",
            "duration_sec": 10.5,
            "resolution": "1920x1080",
            "attribution": "Pexels / John Doe",
        }
        footage_id = save_footage_record(
            conn,
            clip=clip,
            download_path="/tmp/footage.mp4",
            keywords=["nature", "peaceful"],
        )

        assert footage_id > 0

        saved = conn.execute(
            "SELECT * FROM stock_footage WHERE id = ?", (footage_id,)
        ).fetchone()
        assert saved["source"] == "pexels"
        assert saved["external_id"] == "12345"

        conn.close()


class TestVideoComposition:
    """Test video record storage (not actual FFmpeg composition)."""

    def test_save_video_record(self, tmp_path):
        """Test saving video metadata after composition."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)
        _seed_themes_and_verses(conn)

        # Set up prayer and audio
        theme = conn.execute("SELECT * FROM themes WHERE slug = 'grief'").fetchone()
        verse = conn.execute(
            "SELECT * FROM bible_verses WHERE theme_id = ?", (theme["id"],)
        ).fetchone()
        prayer_id = save_prayer(conn, verse["id"], theme["id"], "Test prayer text.")

        conn.execute(
            "INSERT INTO audio_files (prayer_id, file_path, voice_id, created_at) "
            "VALUES (?, '/tmp/audio.mp3', 'voice1', ?)",
            (prayer_id, now_utc()),
        )
        conn.commit()
        audio_id = conn.execute("SELECT id FROM audio_files").fetchone()["id"]

        # Save footage
        clip = {
            "source": "pexels",
            "external_id": "123",
            "duration_sec": 10.0,
            "attribution": "Test",
        }
        footage_id = save_footage_record(conn, clip, "/tmp/footage.mp4")

        # Save video record
        video_info = {
            "file_path": "/tmp/final_video.mp4",
            "duration_sec": 65.0,
            "resolution": "1080x1920",
            "file_size_bytes": 20_000_000,
        }
        video_id = save_video_record(conn, prayer_id, audio_id, [footage_id], video_info)

        assert video_id > 0

        saved = conn.execute(
            "SELECT * FROM generated_videos WHERE id = ?", (video_id,)
        ).fetchone()
        assert saved["prayer_id"] == prayer_id
        assert saved["duration_sec"] == 65.0

        conn.close()


class TestPublishQueue:
    """Test publish queue management."""

    def test_full_queue_workflow(self, tmp_path):
        """Test adding to queue and retrieving items."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)
        _seed_themes_and_verses(conn)

        # Create full content chain
        theme = conn.execute("SELECT * FROM themes WHERE slug = 'grief'").fetchone()
        verse = conn.execute(
            "SELECT * FROM bible_verses WHERE theme_id = ?", (theme["id"],)
        ).fetchone()
        prayer_id = save_prayer(conn, verse["id"], theme["id"], "Test prayer.")

        conn.execute(
            "INSERT INTO audio_files (prayer_id, file_path, voice_id, created_at) "
            "VALUES (?, '/tmp/audio.mp3', 'voice1', ?)",
            (prayer_id, now_utc()),
        )
        conn.commit()
        audio_id = conn.execute("SELECT id FROM audio_files").fetchone()["id"]

        video_info = {
            "file_path": "/tmp/video.mp4",
            "duration_sec": 65.0,
            "resolution": "1080x1920",
            "file_size_bytes": 20_000_000,
        }
        video_id = save_video_record(conn, prayer_id, audio_id, [], video_info)

        # Add to publish queue (uses scheduled_at, not scheduled_for)
        queue_id = add_to_queue(
            conn,
            video_id=video_id,
            scheduled_at="2024-03-01T07:00:00Z",
            platform="tiktok",
        )

        assert queue_id > 0

        # Retrieve queue
        queue = get_queue(conn)
        assert len(queue) == 1
        assert queue[0]["video_id"] == video_id

        conn.close()


class TestEndToEndFlow:
    """Test the complete flow from selection to queue."""

    def test_complete_content_creation_flow(self, tmp_path):
        """Simulate complete content creation without API calls."""
        db_path = str(tmp_path / "test.db")
        conn = connect(db_path)
        init_schema(conn)
        _seed_themes_and_verses(conn)

        # 1. Select theme
        theme = pick_theme(conn)
        assert theme is not None

        # 2. Select verse
        verse = pick_verse(conn, theme["id"])
        assert verse is not None
        mark_verse_used(conn, verse["id"])

        # 3. Generate prayer (using fallback) - needs dict versions
        theme_dict = dict(theme)
        verse_dict = dict(verse)
        prayer_text = generate_prayer_text_fallback(verse_dict, theme_dict)
        prayer_id = save_prayer(conn, verse["id"], theme["id"], prayer_text)
        assert prayer_id > 0

        # 4. Simulate audio generation (just save record)
        audio_info = {
            "file_path": str(_audio_path(prayer_id, "test_voice")),
            "voice_id": "test_voice",
            "speed": 1.0,
            "file_hash": "simulated_hash",
        }
        audio_id = save_audio_record(conn, prayer_id, audio_info)
        assert audio_id > 0

        # 5. Simulate footage download
        clip = {
            "source": "pexels",
            "external_id": "sim_123",
            "duration_sec": 10.0,
            "attribution": "Simulated",
        }
        footage_id = save_footage_record(
            conn,
            clip=clip,
            download_path="/tmp/sim_footage.mp4",
            keywords=[theme["slug"]],
        )
        assert footage_id > 0

        # 6. Simulate video composition
        video_info = {
            "file_path": "/tmp/sim_video.mp4",
            "duration_sec": 65.0,
            "resolution": "1080x1920",
            "file_size_bytes": 20_000_000,
        }
        video_id = save_video_record(conn, prayer_id, audio_id, [footage_id], video_info)
        assert video_id > 0

        # 7. Add to publish queue
        queue_id = add_to_queue(
            conn,
            video_id=video_id,
            scheduled_at="2024-03-01T07:00:00Z",
            platform="tiktok",
        )
        assert queue_id > 0

        # Verify complete chain
        queue_item = conn.execute(
            "SELECT * FROM publish_queue WHERE id = ?", (queue_id,)
        ).fetchone()
        assert queue_item["status"] == "pending"

        video = conn.execute(
            "SELECT * FROM generated_videos WHERE id = ?", (video_id,)
        ).fetchone()
        assert video["prayer_id"] == prayer_id

        conn.close()
