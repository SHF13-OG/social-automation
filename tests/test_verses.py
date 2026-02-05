"""Tests for src/content/verses.py - verse selection and rotation."""

from src.content.verses import get_verses_for_theme, mark_verse_used, pick_verse
from src.db import connect, init_schema, now_utc


def _seed_theme_and_verses(conn, num_verses=3):
    """Insert one theme with N verses and return (theme_id, verse_ids)."""
    conn.execute(
        "INSERT INTO themes (slug, name, tone, is_active, created_at) "
        "VALUES ('test', 'Test Theme', 'comforting', 1, ?)",
        (now_utc(),),
    )
    conn.commit()
    theme_id = conn.execute(
        "SELECT id FROM themes WHERE slug = 'test'"
    ).fetchone()["id"]

    verse_ids = []
    for i in range(num_verses):
        conn.execute(
            "INSERT INTO bible_verses (reference, text, theme_id, used_count, created_at) "
            "VALUES (?, ?, ?, 0, ?)",
            (f"Test {i+1}:1", f"Verse text {i+1}", theme_id, now_utc()),
        )
    conn.commit()
    cur = conn.execute(
        "SELECT id FROM bible_verses WHERE theme_id = ? ORDER BY id", (theme_id,)
    )
    verse_ids = [row["id"] for row in cur.fetchall()]
    return theme_id, verse_ids


def test_get_verses_for_theme(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    theme_id, verse_ids = _seed_theme_and_verses(conn, 3)

    verses = get_verses_for_theme(conn, theme_id)
    assert len(verses) == 3
    refs = [v["reference"] for v in verses]
    assert "Test 1:1" in refs
    conn.close()


def test_get_verses_empty_theme(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    verses = get_verses_for_theme(conn, 999)
    assert verses == []
    conn.close()


def test_pick_verse_returns_one(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    theme_id, _ = _seed_theme_and_verses(conn, 3)

    verse = pick_verse(conn, theme_id)
    assert verse is not None
    assert verse["reference"].startswith("Test")
    conn.close()


def test_pick_verse_empty_returns_none(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    verse = pick_verse(conn, 999)
    assert verse is None
    conn.close()


def test_pick_verse_prefers_least_used(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    theme_id, verse_ids = _seed_theme_and_verses(conn, 3)

    # Mark first two as used
    conn.execute("UPDATE bible_verses SET used_count = 5 WHERE id = ?", (verse_ids[0],))
    conn.execute("UPDATE bible_verses SET used_count = 3 WHERE id = ?", (verse_ids[1],))
    conn.commit()

    # Third verse (used_count=0) should always be picked
    verse = pick_verse(conn, theme_id)
    assert verse is not None
    assert verse["id"] == verse_ids[2]
    conn.close()


def test_mark_verse_used(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    theme_id, verse_ids = _seed_theme_and_verses(conn, 1)

    vid = verse_ids[0]

    # Initially used_count = 0
    row = conn.execute("SELECT used_count FROM bible_verses WHERE id = ?", (vid,)).fetchone()
    assert row["used_count"] == 0

    mark_verse_used(conn, vid)

    row = conn.execute(
        "SELECT used_count, last_used_at FROM bible_verses WHERE id = ?", (vid,)
    ).fetchone()
    assert row["used_count"] == 1
    assert row["last_used_at"] is not None

    mark_verse_used(conn, vid)
    row = conn.execute("SELECT used_count FROM bible_verses WHERE id = ?", (vid,)).fetchone()
    assert row["used_count"] == 2
    conn.close()
