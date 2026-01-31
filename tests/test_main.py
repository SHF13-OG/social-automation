import sqlite3

import pandas as pd

from src.main import (
    normalize_columns,
    parse_datetime,
    row_to_post,
    init_db,
    to_int,
    upsert_post,
    load_posts,
)


# --- to_int tests ---

def test_to_int_basic():
    assert to_int("123") == 123
    assert to_int(456) == 456


def test_to_int_with_commas():
    assert to_int("1,234") == 1234
    assert to_int("1,234,567") == 1234567


def test_to_int_with_float():
    assert to_int("123.45") == 123
    assert to_int(99.9) == 99


def test_to_int_empty_and_none():
    assert to_int(None) is None
    assert to_int("") is None
    assert to_int("   ") is None


def test_to_int_invalid():
    assert to_int("abc") is None
    assert to_int("twelve") is None


# --- normalize_columns tests ---

def test_normalize_columns_lowercase():
    df = pd.DataFrame({"Views": [1], "LIKES": [2], "Comments": [3]})
    result = normalize_columns(df)
    assert list(result.columns) == ["views", "likes", "comments"]


def test_normalize_columns_spaces_and_dashes():
    df = pd.DataFrame({"Post ID": [1], "created-at": [2], "view count": [3]})
    result = normalize_columns(df)
    assert list(result.columns) == ["post_id", "created_at", "view_count"]


# --- parse_datetime tests ---

def test_parse_datetime_epoch_seconds():
    dt = parse_datetime("1735776000")  # epoch seconds
    assert dt is not None
    assert "T" in dt


def test_parse_datetime_epoch_milliseconds():
    dt = parse_datetime("1735776000000")  # epoch milliseconds
    assert dt is not None
    assert "T" in dt


def test_parse_datetime_iso_format():
    dt = parse_datetime("2025-01-15T10:30:00Z")
    assert dt is not None
    assert "2025-01-15" in dt


def test_parse_datetime_human_readable():
    dt = parse_datetime("January 15, 2025")
    assert dt is not None
    assert "2025-01-15" in dt


def test_parse_datetime_empty_and_none():
    assert parse_datetime(None) is None
    assert parse_datetime("") is None


# --- row_to_post tests ---

def test_row_to_post_requires_post_id():
    post, err = row_to_post({"views": "10", "likes": "1"})
    assert post is None
    assert err is not None


def test_row_to_post_maps_all_fields():
    row = {
        "post_id": "123456",
        "created_at": "2025-01-15T10:00:00Z",
        "views": "1000",
        "likes": "100",
        "comments": "10",
        "shares": "5",
        "favorites": "50",
        "caption": "Test caption",
        "url": "https://tiktok.com/video/123456",
    }
    post, err = row_to_post(row)
    assert err is None
    assert post["post_id"] == "123456"
    assert post["views"] == 1000
    assert post["likes"] == 100
    assert post["comments"] == 10
    assert post["shares"] == 5
    assert post["favorites"] == 50
    assert post["caption"] == "Test caption"
    assert post["url"] == "https://tiktok.com/video/123456"


def test_row_to_post_alternative_keys():
    row = {
        "video_id": "789",
        "play_count": "5000",
        "digg_count": "200",
        "description": "Alt caption",
    }
    post, err = row_to_post(row)
    assert err is None
    assert post["post_id"] == "789"
    assert post["views"] == 5000
    assert post["likes"] == 200
    assert post["caption"] == "Alt caption"


# --- init_db tests ---

def test_db_schema_creates_table(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    init_db(conn)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tiktok_posts';")
    assert cur.fetchone() is not None
    conn.close()


def test_db_schema_creates_index(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    init_db(conn)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_tiktok_posts_created_at';")
    assert cur.fetchone() is not None
    conn.close()


# --- upsert_post tests ---

def test_upsert_post_insert(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    init_db(conn)

    post = {
        "post_id": "test123",
        "created_at": "2025-01-15T10:00:00+00:00",
        "views": 1000,
        "likes": 100,
        "comments": 10,
        "shares": 5,
        "favorites": 50,
        "caption": "Test",
        "url": "https://example.com",
        "raw_json": "{}",
    }

    with conn:
        upsert_post(conn, post)

    cur = conn.execute("SELECT post_id, views FROM tiktok_posts WHERE post_id = 'test123'")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "test123"
    assert row[1] == 1000
    conn.close()


def test_upsert_post_update(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    init_db(conn)

    post = {
        "post_id": "test456",
        "views": 1000,
        "likes": 100,
    }

    with conn:
        upsert_post(conn, post)

    # Update with new views
    post["views"] = 2000
    with conn:
        upsert_post(conn, post)

    cur = conn.execute("SELECT views FROM tiktok_posts WHERE post_id = 'test456'")
    row = cur.fetchone()
    assert row[0] == 2000
    conn.close()


# --- load_posts tests ---

def test_load_posts_calculates_engagement(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    init_db(conn)

    post = {
        "post_id": "eng123",
        "created_at": "2025-01-15T10:00:00+00:00",
        "views": 1000,
        "likes": 100,
        "comments": 20,
        "shares": 10,
        "favorites": 50,
    }

    with conn:
        upsert_post(conn, post)

    df = load_posts(conn)
    conn.close()

    assert len(df) == 1
    assert df.iloc[0]["engagement"] == 130  # likes + comments + shares
    assert df.iloc[0]["engagement_rate"] == 0.13  # 130 / 1000


def test_load_posts_handles_zero_views(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    init_db(conn)

    post = {
        "post_id": "zero123",
        "views": 0,
        "likes": 10,
        "comments": 5,
        "shares": 2,
    }

    with conn:
        upsert_post(conn, post)

    df = load_posts(conn)
    conn.close()

    assert len(df) == 1
    assert df.iloc[0]["engagement_rate"] == 0.0  # no division by zero
