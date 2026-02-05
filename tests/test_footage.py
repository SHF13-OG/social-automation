"""Tests for src/media/footage.py - stock footage search, download, storage."""

import json

from src.db import connect, init_schema, now_utc
from src.media.footage import (
    _pick_best_pexels_file,
    save_footage_record,
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
