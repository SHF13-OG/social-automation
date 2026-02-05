"""Tests for src/content/themes.py - theme selection and rotation."""

import json

from src.content.themes import get_active_themes, get_theme_by_slug, pick_theme
from src.db import connect, init_schema, now_utc


def _seed_themes(conn, active=True):
    """Insert a couple of themes and return their ids."""
    ids = []
    for slug, name, tone in [
        ("grief", "Grief & Loss", "comforting"),
        ("retirement", "Retirement", "encouraging"),
        ("health", "Health", "hopeful"),
    ]:
        conn.execute(
            """
            INSERT INTO themes (slug, name, keywords, tone, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (slug, name, json.dumps([]), tone, 1 if active else 0, now_utc()),
        )
    conn.commit()
    cur = conn.execute("SELECT id FROM themes ORDER BY slug")
    ids = [row["id"] for row in cur.fetchall()]
    return ids


def test_get_active_themes(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    _seed_themes(conn)

    themes = get_active_themes(conn)
    assert len(themes) == 3
    slugs = {t["slug"] for t in themes}
    assert slugs == {"grief", "retirement", "health"}
    conn.close()


def test_get_active_themes_excludes_inactive(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    _seed_themes(conn)

    # Deactivate one
    conn.execute("UPDATE themes SET is_active = 0 WHERE slug = 'health'")
    conn.commit()

    themes = get_active_themes(conn)
    assert len(themes) == 2
    slugs = {t["slug"] for t in themes}
    assert "health" not in slugs
    conn.close()


def test_get_theme_by_slug(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    _seed_themes(conn)

    theme = get_theme_by_slug(conn, "grief")
    assert theme is not None
    assert theme["name"] == "Grief & Loss"

    missing = get_theme_by_slug(conn, "nonexistent")
    assert missing is None
    conn.close()


def test_pick_theme_by_slug(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    _seed_themes(conn)

    theme = pick_theme(conn, slug="retirement")
    assert theme is not None
    assert theme["slug"] == "retirement"
    conn.close()


def test_pick_theme_by_slug_inactive_returns_none(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    _seed_themes(conn)
    conn.execute("UPDATE themes SET is_active = 0 WHERE slug = 'grief'")
    conn.commit()

    theme = pick_theme(conn, slug="grief")
    assert theme is None
    conn.close()


def test_pick_theme_auto_selects(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    _seed_themes(conn)

    theme = pick_theme(conn)
    assert theme is not None
    assert theme["slug"] in {"grief", "retirement", "health"}
    conn.close()


def test_pick_theme_prefers_unused(tmp_path):
    """Themes with no verse usage should be preferred over used ones."""
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    theme_ids = _seed_themes(conn)

    # Add verses to each theme
    for tid in theme_ids:
        conn.execute(
            "INSERT INTO bible_verses (reference, text, theme_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            ("Test 1:1", "Test text", tid, now_utc()),
        )
    conn.commit()

    # Mark grief and retirement verses as used
    grief_id = conn.execute(
        "SELECT id FROM themes WHERE slug = 'grief'"
    ).fetchone()["id"]
    retirement_id = conn.execute(
        "SELECT id FROM themes WHERE slug = 'retirement'"
    ).fetchone()["id"]

    conn.execute(
        "UPDATE bible_verses SET last_used_at = ? WHERE theme_id = ?",
        (now_utc(), grief_id),
    )
    conn.execute(
        "UPDATE bible_verses SET last_used_at = ? WHERE theme_id = ?",
        (now_utc(), retirement_id),
    )
    conn.commit()

    # Health is the only unused theme → should be picked
    theme = pick_theme(conn)
    assert theme is not None
    assert theme["slug"] == "health"
    conn.close()


def test_pick_theme_empty_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    theme = pick_theme(conn)
    assert theme is None
    conn.close()
