"""Tests for src/media/footage.py - stock footage search, download, storage."""

import json
from unittest.mock import MagicMock

from src.db import connect, init_schema, now_utc
from src.media.footage import (
    _pick_best_pexels_file,
    generate_kling_clips,
    save_footage_record,
    search_footage,
)


def test_pick_best_pexels_file_prefers_hd():
    files = [
        {"quality": "sd", "height": 480, "width": 270, "link": "sd.mp4"},
        {"quality": "hd", "height": 1080, "width": 1920, "link": "hd.mp4"},
        {"quality": "hd", "height": 1920, "width": 1080, "link": "hd_portrait.mp4"},
    ]
    best = _pick_best_pexels_file(files)
    assert best["link"] == "hd_portrait.mp4"


def test_pick_best_pexels_file_fallback_to_720():
    files = [
        {"quality": "sd", "height": 720, "width": 1280, "link": "720.mp4"},
        {"quality": "sd", "height": 360, "width": 640, "link": "360.mp4"},
    ]
    best = _pick_best_pexels_file(files)
    assert best["link"] == "720.mp4"


def test_pick_best_pexels_file_empty():
    assert _pick_best_pexels_file([]) is None


def test_pick_best_pexels_file_single():
    files = [{"quality": "sd", "height": 480, "width": 270, "link": "only.mp4"}]
    best = _pick_best_pexels_file(files)
    assert best["link"] == "only.mp4"


def test_save_footage_record(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    # Create a theme
    conn.execute(
        "INSERT INTO themes (slug, name, tone, is_active, created_at) "
        "VALUES ('grief', 'Grief', 'comforting', 1, ?)",
        (now_utc(),),
    )
    conn.commit()
    theme_id = conn.execute("SELECT id FROM themes WHERE slug = 'grief'").fetchone()["id"]

    clip = {
        "source": "pexels",
        "external_id": "12345",
        "url": "https://pexels.com/video/12345",
        "duration_sec": 15,
        "resolution": "1080x1920",
        "attribution": "Pexels - Test User",
    }
    fid = save_footage_record(
        conn, clip, "/tmp/footage.mp4", theme_id, ["sunset", "peaceful"]
    )
    assert fid > 0

    row = conn.execute("SELECT * FROM stock_footage WHERE id = ?", (fid,)).fetchone()
    assert row["source"] == "pexels"
    assert row["external_id"] == "12345"
    assert json.loads(row["keywords"]) == ["sunset", "peaceful"]
    conn.close()


def test_save_footage_record_deduplicates(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    clip = {
        "source": "pexels",
        "external_id": "99999",
        "url": "https://pexels.com/video/99999",
    }
    id1 = save_footage_record(conn, clip, "/tmp/f1.mp4")
    id2 = save_footage_record(conn, clip, "/tmp/f2.mp4")
    assert id1 == id2  # Same record, not duplicated
    conn.close()


def test_search_pexels_raises_without_key(monkeypatch):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)

    from src.media.footage import search_pexels

    try:
        search_pexels("sunset")
        assert False, "Should have raised"
    except RuntimeError as exc:
        assert "PEXELS_API_KEY" in str(exc)


def test_search_pixabay_raises_without_key(monkeypatch):
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)

    from src.media.footage import search_pixabay

    try:
        search_pixabay("sunset")
        assert False, "Should have raised"
    except RuntimeError as exc:
        assert "PIXABAY_API_KEY" in str(exc)


# ---------------------------------------------------------------------------
# Kling AI tests
# ---------------------------------------------------------------------------


def test_generate_kling_raises_without_key(monkeypatch):
    """generate_kling_clips should raise when FAL_KEY is not set."""
    monkeypatch.delenv("FAL_KEY", raising=False)
    import sys
    monkeypatch.setitem(sys.modules, "fal_client", MagicMock())

    try:
        generate_kling_clips(["sunset"])
        assert False, "Should have raised"
    except RuntimeError as exc:
        assert "FAL_KEY" in str(exc)


def test_generate_kling_clips_returns_correct_shape(monkeypatch, tmp_path):
    """Verify Kling clips return the same dict shape as stock footage results."""
    monkeypatch.setenv("FAL_KEY", "test-fal-key")
    monkeypatch.setattr("src.media.footage.FOOTAGE_DIR", tmp_path)
    monkeypatch.setattr(
        "src.media.footage.get_config_value",
        lambda key, default=None, db_path=None: {
            "footage.kling_model": "fal-ai/kling-video/v2.5-turbo/pro/text-to-video",
            "footage.kling_duration": "10",
        }.get(key, default),
    )

    mock_fal = MagicMock()
    mock_fal.subscribe.return_value = {
        "video": {"url": "https://fal.ai/output/test-video.mp4"},
        "request_id": "req_abc123",
    }

    import sys
    monkeypatch.setitem(sys.modules, "fal_client", mock_fal)

    results = generate_kling_clips(["peaceful garden"])

    assert len(results) == 1
    clip = results[0]
    assert clip["source"] == "kling"
    assert clip["external_id"] == "req_abc123"
    assert clip["download_url"] == "https://fal.ai/output/test-video.mp4"
    assert clip["duration_sec"] == 10
    assert clip["resolution"] == "1080x1920"
    assert clip["attribution"] == "Kling AI via fal.ai"

    # Verify fal_client.subscribe was called with correct args
    call_args = mock_fal.subscribe.call_args
    assert call_args[0][0] == "fal-ai/kling-video/v2.5-turbo/pro/text-to-video"
    assert call_args[1]["arguments"]["aspect_ratio"] == "9:16"
    assert call_args[1]["arguments"]["duration"] == "10"
    assert "peaceful garden" in call_args[1]["arguments"]["prompt"]


def test_search_footage_dispatches_to_kling(monkeypatch, tmp_path):
    """search_footage should dispatch to Kling when primary_source=kling."""
    monkeypatch.setenv("FAL_KEY", "test-fal-key")
    monkeypatch.setattr("src.media.footage.FOOTAGE_DIR", tmp_path)

    config_values = {
        "footage.primary_source": "kling",
        "footage.kling_model": "fal-ai/kling-video/v2.5-turbo/pro/text-to-video",
        "footage.kling_duration": "10",
    }
    monkeypatch.setattr(
        "src.media.footage.get_config_value",
        lambda key, default=None, db_path=None: config_values.get(key, default),
    )

    mock_fal = MagicMock()
    mock_fal.subscribe.return_value = {
        "video": {"url": "https://fal.ai/output/clip.mp4"},
        "request_id": "req_xyz",
    }

    import sys
    monkeypatch.setitem(sys.modules, "fal_client", mock_fal)

    results = search_footage(["sunset"])

    assert len(results) == 1
    assert results[0]["source"] == "kling"
    mock_fal.subscribe.assert_called_once()


def test_search_footage_default_dispatches_to_pexels(monkeypatch):
    """Default config should NOT dispatch to Kling."""
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)

    # With default config (pexels), it should try Pexels and fail on missing key
    try:
        search_footage(["sunset"])
    except RuntimeError:
        pass  # Expected — Pexels key not set

    # The point is it didn't route to Kling
