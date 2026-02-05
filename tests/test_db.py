"""Tests for src/db.py - database utilities and schema."""

import sqlite3

from src.db import connect, init_schema, now_utc


def test_connect_creates_file(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    assert conn is not None
    conn.close()
    assert (tmp_path / "test.db").exists()


def test_connect_enables_wal(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    cur = conn.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0]
    assert mode == "wal"
    conn.close()


def test_connect_enables_foreign_keys(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    cur = conn.execute("PRAGMA foreign_keys;")
    fk = cur.fetchone()[0]
    assert fk == 1
    conn.close()


def test_connect_sets_row_factory(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    assert conn.row_factory == sqlite3.Row
    conn.close()


def test_init_schema_creates_all_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row["name"] for row in cur.fetchall()}
    conn.close()

    expected = {
        "tiktok_posts",
        "themes",
        "bible_verses",
        "prayers",
        "audio_files",
        "stock_footage",
        "generated_videos",
        "publish_queue",
        "config_overrides",
        "test_runs",
    }
    assert expected.issubset(tables)


def test_init_schema_creates_indexes(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
    )
    indexes = {row["name"] for row in cur.fetchall()}
    conn.close()

    assert "idx_tiktok_posts_created_at" in indexes
    assert "idx_bible_verses_theme" in indexes
    assert "idx_stock_footage_theme" in indexes
    assert "idx_publish_queue_status" in indexes
    assert "idx_publish_queue_scheduled" in indexes


def test_init_schema_is_idempotent(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    init_schema(conn)  # Should not raise
    conn.close()


def test_now_utc_returns_iso_format():
    ts = now_utc()
    assert "T" in ts
    assert "+" in ts or "Z" in ts


def test_themes_table_upsert(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    conn.execute(
        """
        INSERT INTO themes (slug, name, tone, is_active, created_at)
        VALUES ('grief', 'Grief & Loss', 'comforting', 1, '2025-01-01')
        """
    )
    conn.commit()

    cur = conn.execute("SELECT name FROM themes WHERE slug = 'grief'")
    assert cur.fetchone()["name"] == "Grief & Loss"

    # Upsert with ON CONFLICT
    conn.execute(
        """
        INSERT INTO themes (slug, name, tone, is_active, created_at)
        VALUES ('grief', 'Updated Grief', 'comforting', 1, '2025-01-02')
        ON CONFLICT(slug) DO UPDATE SET name = excluded.name
        """
    )
    conn.commit()

    cur = conn.execute("SELECT name FROM themes WHERE slug = 'grief'")
    assert cur.fetchone()["name"] == "Updated Grief"
    conn.close()


def test_bible_verses_foreign_key(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    conn.execute(
        """
        INSERT INTO themes (slug, name, created_at)
        VALUES ('test', 'Test Theme', '2025-01-01')
        """
    )
    conn.commit()

    theme_id = conn.execute(
        "SELECT id FROM themes WHERE slug = 'test'"
    ).fetchone()["id"]

    conn.execute(
        """
        INSERT INTO bible_verses (reference, text, theme_id, created_at)
        VALUES ('John 3:16', 'For God so loved the world...', ?, '2025-01-01')
        """,
        (theme_id,),
    )
    conn.commit()

    cur = conn.execute(
        "SELECT reference FROM bible_verses WHERE theme_id = ?", (theme_id,)
    )
    assert cur.fetchone()["reference"] == "John 3:16"
    conn.close()
