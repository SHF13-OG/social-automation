"""Tests for src/media/tts.py - TTS audio generation and storage."""

from pathlib import Path
from unittest.mock import MagicMock

from src.db import connect, init_schema, now_utc
from src.media.tts import (
    AUDIO_DIR,
    OPENAI_TTS_SYSTEM_PROMPT,
    _audio_path,
    _file_hash,
    generate_audio,
    save_audio_record,
)


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
    """generate_audio should raise RuntimeError when no API key (ElevenLabs)."""
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)

    try:
        generate_audio(1, "Test prayer text.")
        assert False, "Should have raised"
    except RuntimeError as exc:
        assert "ELEVENLABS_API_KEY" in str(exc) or "elevenlabs" in str(exc).lower()


# ---------------------------------------------------------------------------
# Provider routing tests
# ---------------------------------------------------------------------------


def test_generate_audio_routes_to_elevenlabs_by_default(monkeypatch):
    """Default provider config routes to ElevenLabs."""
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    # With no API key set, it should still route to ElevenLabs and fail there.
    try:
        generate_audio(1, "Test prayer text.")
    except RuntimeError as exc:
        assert "ELEVENLABS_API_KEY" in str(exc)


def test_generate_audio_routes_to_openai(monkeypatch):
    """Setting voice.provider=openai routes to OpenAI and requires its key."""
    monkeypatch.setattr(
        "src.media.tts.get_config_value",
        lambda key, default=None, db_path=None: "openai" if key == "voice.provider" else default,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    try:
        generate_audio(1, "Test prayer text.")
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)


def test_openai_tts_calls_api_correctly(monkeypatch, tmp_path):
    """Verify OpenAI TTS makes the correct API call and returns expected dict."""
    monkeypatch.setattr(
        "src.media.tts.get_config_value",
        lambda key, default=None, db_path=None: {
            "voice.provider": "openai",
            "voice.openai_voice": "onyx",
            "voice.openai_model": "gpt-4o-mini-tts",
        }.get(key, default),
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

    # Redirect audio output to tmp_path
    monkeypatch.setattr("src.media.tts.AUDIO_DIR", tmp_path)

    # Mock the OpenAI client
    mock_response = MagicMock()
    mock_response.stream_to_file = MagicMock(
        side_effect=lambda path: Path(path).write_bytes(b"fake-mp3-data")
    )

    mock_client = MagicMock()
    mock_client.audio.speech.create.return_value = mock_response

    # Mock the openai module so the lazy import inside _generate_audio_openai works
    import sys
    mock_openai_module = MagicMock()
    mock_openai_module.OpenAI = MagicMock(return_value=mock_client)
    monkeypatch.setitem(sys.modules, "openai", mock_openai_module)

    result = generate_audio(1, "Lord, hear our prayer.")

    # Verify the API was called with correct params
    mock_client.audio.speech.create.assert_called_once_with(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input="Lord, hear our prayer.",
        instructions=OPENAI_TTS_SYSTEM_PROMPT,
        response_format="mp3",
    )

    # Verify return dict shape matches ElevenLabs output
    assert "file_path" in result
    assert "voice_id" in result
    assert "speed" in result
    assert "file_hash" in result
    assert "file_size" in result
    assert result["voice_id"] == "onyx"
    assert result["speed"] == 1.0
    assert result["file_size"] > 0
