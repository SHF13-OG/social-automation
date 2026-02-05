"""Tests for src/media/tts.py - TTS audio generation and storage."""

from src.db import connect, init_schema, now_utc
from src.media.tts import AUDIO_DIR, _audio_path, _file_hash, save_audio_record


def _seed_prayer(conn):
    """Create a theme + verse + prayer and return prayer_id."""
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
    return conn.execute("SELECT id FROM prayers").fetchone()["id"]


def test_audio_path_deterministic():
    p = _audio_path(42, "abc123")
    assert p == AUDIO_DIR / "prayer_42_abc123.mp3"


def test_audio_path_different_ids():
    p1 = _audio_path(1, "voice_a")
    p2 = _audio_path(2, "voice_a")
    assert p1 != p2


def test_file_hash_consistent(tmp_path):
    f = tmp_path / "test.bin"
    f.write_bytes(b"hello world")
    h1 = _file_hash(f)
    h2 = _file_hash(f)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_file_hash_differs_for_different_content(tmp_path):
    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    f1.write_bytes(b"hello")
    f2.write_bytes(b"world")
    assert _file_hash(f1) != _file_hash(f2)


def test_save_audio_record(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    prayer_id = _seed_prayer(conn)

    audio_info = {
        "file_path": "/tmp/prayer_1.mp3",
        "voice_id": "abc123",
        "speed": 0.95,
        "file_hash": "deadbeef" * 8,
    }
    audio_id = save_audio_record(conn, prayer_id, audio_info)
    assert audio_id > 0

    row = conn.execute("SELECT * FROM audio_files WHERE id = ?", (audio_id,)).fetchone()
    assert row["prayer_id"] == prayer_id
    assert row["voice_id"] == "abc123"
    assert row["speed"] == 0.95
    assert row["file_path"] == "/tmp/prayer_1.mp3"
    conn.close()


def test_generate_audio_raises_without_api_key(monkeypatch):
    """generate_audio should raise RuntimeError when no API key."""
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)

    from src.media.tts import generate_audio

    try:
        generate_audio(1, "Test prayer text.")
        assert False, "Should have raised"
    except RuntimeError as exc:
        assert "ELEVENLABS_API_KEY" in str(exc) or "elevenlabs" in str(exc).lower()
