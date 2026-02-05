"""Database utilities and schema management for social-automation."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

DEFAULT_DB_PATH = "data/social.db"


def get_db_path() -> str:
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


def connect(db_path: str | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables if they don't exist."""
    conn.executescript(_SCHEMA_SQL)
    conn.commit()


_SCHEMA_SQL = """
-- Original tiktok_posts table
CREATE TABLE IF NOT EXISTS tiktok_posts (
    post_id     TEXT PRIMARY KEY,
    created_at  TEXT,
    views       INTEGER,
    likes       INTEGER,
    comments    INTEGER,
    shares      INTEGER,
    favorites   INTEGER,
    caption     TEXT,
    url         TEXT,
    raw_json    TEXT,
    updated_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_tiktok_posts_created_at
    ON tiktok_posts(created_at);

-- Content themes
CREATE TABLE IF NOT EXISTS themes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    description TEXT,
    keywords    TEXT,           -- JSON array for stock footage search
    tone        TEXT,
    is_active   INTEGER DEFAULT 1,
    created_at  TEXT,
    updated_at  TEXT
);

-- Bible verses mapped to themes
CREATE TABLE IF NOT EXISTS bible_verses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reference       TEXT NOT NULL,
    text            TEXT NOT NULL,
    translation     TEXT DEFAULT 'ESV',
    theme_id        INTEGER REFERENCES themes(id),
    tone            TEXT,
    used_count      INTEGER DEFAULT 0,
    last_used_at    TEXT,
    created_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_bible_verses_theme
    ON bible_verses(theme_id);

-- Generated prayers
CREATE TABLE IF NOT EXISTS prayers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    verse_id            INTEGER REFERENCES bible_verses(id),
    theme_id            INTEGER REFERENCES themes(id),
    prayer_text         TEXT NOT NULL,
    word_count          INTEGER,
    target_duration_sec INTEGER,
    ai_model            TEXT,
    prompt_template     TEXT,
    created_at          TEXT
);

-- Audio files generated via ElevenLabs
CREATE TABLE IF NOT EXISTS audio_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prayer_id       INTEGER REFERENCES prayers(id),
    file_path       TEXT NOT NULL,
    duration_sec    REAL,
    voice_id        TEXT,
    voice_name      TEXT,
    speed           REAL DEFAULT 1.0,
    elevenlabs_id   TEXT,
    file_hash       TEXT,
    created_at      TEXT
);

-- Stock footage from Pexels/Pixabay
CREATE TABLE IF NOT EXISTS stock_footage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,
    external_id     TEXT NOT NULL,
    url             TEXT NOT NULL,
    download_path   TEXT,
    keywords        TEXT,           -- JSON array
    duration_sec    REAL,
    resolution      TEXT,
    license         TEXT,
    attribution     TEXT,
    theme_id        INTEGER REFERENCES themes(id),
    downloaded_at   TEXT,
    created_at      TEXT,
    UNIQUE(source, external_id)
);
CREATE INDEX IF NOT EXISTS idx_stock_footage_theme
    ON stock_footage(theme_id);

-- Generated videos (final composites)
CREATE TABLE IF NOT EXISTS generated_videos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prayer_id       INTEGER REFERENCES prayers(id),
    audio_id        INTEGER REFERENCES audio_files(id),
    footage_ids     TEXT,           -- JSON array
    file_path       TEXT NOT NULL,
    duration_sec    REAL,
    resolution      TEXT,
    file_size_bytes INTEGER,
    font_style      TEXT,
    font_size       INTEGER,
    text_position   TEXT,
    created_at      TEXT
);

-- Publishing queue and history
CREATE TABLE IF NOT EXISTS publish_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id        INTEGER REFERENCES generated_videos(id),
    platform        TEXT DEFAULT 'tiktok',
    scheduled_at    TEXT,
    status          TEXT DEFAULT 'pending',
    published_at    TEXT,
    external_post_id TEXT,
    error_message   TEXT,
    retry_count     INTEGER DEFAULT 0,
    created_at      TEXT,
    updated_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_publish_queue_status
    ON publish_queue(status);
CREATE INDEX IF NOT EXISTS idx_publish_queue_scheduled
    ON publish_queue(scheduled_at);

-- Configuration overrides from dashboard
CREATE TABLE IF NOT EXISTS config_overrides (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT UNIQUE NOT NULL,
    value       TEXT NOT NULL,
    updated_by  TEXT,
    updated_at  TEXT
);

-- CI/CD test results for dashboard display
CREATE TABLE IF NOT EXISTS test_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT UNIQUE,
    status          TEXT,
    tests_passed    INTEGER,
    tests_failed    INTEGER,
    tests_skipped   INTEGER,
    duration_sec    REAL,
    commit_sha      TEXT,
    branch          TEXT,
    started_at      TEXT,
    completed_at    TEXT
);
"""
