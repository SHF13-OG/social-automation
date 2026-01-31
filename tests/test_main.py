import sqlite3
from datetime import datetime, timezone

import pandas as pd

from src.main import normalize_columns, parse_datetime, row_to_post, init_db


def test_parse_datetime_epoch_seconds():
    dt = parse_datetime("1735776000")  # epoch seconds
    assert dt is not None
    assert "T" in dt


def test_row_to_post_requires_post_id():
    post, err = row_to_post({"views": "10", "likes": "1"})
    assert post is None
    assert err is not None


def test_db_schema_creates_table(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    init_db(conn)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tiktok_posts';")
    assert cur.fetchone() is not None
    conn.close()
