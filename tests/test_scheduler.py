"""Tests for src/publishing/scheduler.py - queue management and safety checks."""

from datetime import datetime, timedelta, timezone

from src.db import connect, init_schema, now_utc
from src.publishing.scheduler import (
    HUMAN_APPROVAL_THRESHOLD,
    MAX_CONSECUTIVE_FAILURES,
    add_to_queue,
    approve_item,
    can_publish,
    check_consecutive_failures,
    check_min_interval,
    get_due_items,
    get_queue,
    needs_human_approval,
)


def _seed_video(conn, n=1):
    """Create minimal chain: theme → verse → prayer → video(s). Return video ids."""
    conn.execute(
        "INSERT INTO themes (slug, name, tone, is_active, created_at) "
        "VALUES ('t', 'T', 'c', 1, ?)",
        (now_utc(),),
    )
    conn.commit()
    tid = conn.execute("SELECT id FROM themes").fetchone()["id"]
    conn.execute(
        "INSERT INTO bible_verses (reference, text, theme_id, created_at) "
        "VALUES ('T 1:1', 'text', ?, ?)",
        (tid, now_utc()),
    )
    conn.commit()
    vid = conn.execute("SELECT id FROM bible_verses").fetchone()["id"]
    conn.execute(
        "INSERT INTO prayers (verse_id, theme_id, prayer_text, word_count, created_at) "
        "VALUES (?, ?, 'prayer', 1, ?)",
        (vid, tid, now_utc()),
    )
    conn.commit()
    pid = conn.execute("SELECT id FROM prayers").fetchone()["id"]

    video_ids = []
    for i in range(n):
        conn.execute(
            "INSERT INTO generated_videos (prayer_id, file_path, duration_sec, resolution, "
            "file_size_bytes, created_at) VALUES (?, ?, 65, '1080x1920', 1000, ?)",
            (pid, f"/tmp/v{i}.mp4", now_utc()),
        )
        conn.commit()
        video_ids.append(
            conn.execute(
                "SELECT id FROM generated_videos ORDER BY id DESC LIMIT 1"
            ).fetchone()["id"]
        )
    return video_ids


def test_add_to_queue(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn)

    qid = add_to_queue(conn, video_id=vids[0], scheduled_at="2025-03-01T07:00:00")
    assert qid > 0

    row = conn.execute("SELECT * FROM publish_queue WHERE id = ?", (qid,)).fetchone()
    assert row["video_id"] == vids[0]
    assert row["status"] == "pending"
    assert row["scheduled_at"] == "2025-03-01T07:00:00"
    conn.close()


def test_get_queue_all(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn, 2)

    add_to_queue(conn, vids[0], "2025-03-01T07:00:00")
    add_to_queue(conn, vids[1], "2025-03-02T07:00:00")

    items = get_queue(conn)
    assert len(items) == 2
    conn.close()


def test_get_queue_filtered(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn, 2)

    add_to_queue(conn, vids[0], "2025-03-01T07:00:00")
    qid2 = add_to_queue(conn, vids[1], "2025-03-02T07:00:00")
    approve_item(conn, qid2)

    pending = get_queue(conn, status="pending")
    approved = get_queue(conn, status="approved")
    assert len(pending) == 1
    assert len(approved) == 1
    conn.close()


def test_get_due_items(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn, 2)

    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    qid1 = add_to_queue(conn, vids[0], past)
    qid2 = add_to_queue(conn, vids[1], future)
    approve_item(conn, qid1)
    approve_item(conn, qid2)

    due = get_due_items(conn)
    assert len(due) == 1
    assert due[0]["id"] == qid1
    conn.close()


def test_check_min_interval_first_post(tmp_path):
    """First post ever should always be allowed."""
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    assert check_min_interval(conn) is True
    conn.close()


def test_check_min_interval_too_soon(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn)

    recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    conn.execute(
        "INSERT INTO publish_queue (video_id, status, published_at, created_at, updated_at) "
        "VALUES (?, 'published', ?, ?, ?)",
        (vids[0], recent, now_utc(), now_utc()),
    )
    conn.commit()

    assert check_min_interval(conn) is False
    conn.close()


def test_check_min_interval_enough_time(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn)

    old = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    conn.execute(
        "INSERT INTO publish_queue (video_id, status, published_at, created_at, updated_at) "
        "VALUES (?, 'published', ?, ?, ?)",
        (vids[0], old, now_utc(), now_utc()),
    )
    conn.commit()

    assert check_min_interval(conn) is True
    conn.close()


def test_check_consecutive_failures_ok(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn, 2)

    conn.execute(
        "INSERT INTO publish_queue (video_id, status, created_at, updated_at) "
        "VALUES (?, 'failed', ?, ?)",
        (vids[0], now_utc(), now_utc()),
    )
    conn.execute(
        "INSERT INTO publish_queue (video_id, status, created_at, updated_at) "
        "VALUES (?, 'published', ?, ?)",
        (vids[1], now_utc(), now_utc()),
    )
    conn.commit()

    assert check_consecutive_failures(conn) is True
    conn.close()


def test_check_consecutive_failures_paused(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn, MAX_CONSECUTIVE_FAILURES)

    for i in range(MAX_CONSECUTIVE_FAILURES):
        conn.execute(
            "INSERT INTO publish_queue (video_id, status, created_at, updated_at) "
            "VALUES (?, 'failed', ?, ?)",
            (vids[i], now_utc(), now_utc()),
        )
    conn.commit()

    assert check_consecutive_failures(conn) is False
    conn.close()


def test_needs_human_approval_first_posts(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    assert needs_human_approval(conn) is True
    conn.close()


def test_needs_human_approval_after_threshold(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn, HUMAN_APPROVAL_THRESHOLD)

    for i in range(HUMAN_APPROVAL_THRESHOLD):
        conn.execute(
            "INSERT INTO publish_queue (video_id, status, published_at, created_at, updated_at) "
            "VALUES (?, 'published', ?, ?, ?)",
            (vids[i], now_utc(), now_utc(), now_utc()),
        )
    conn.commit()

    assert needs_human_approval(conn) is False
    conn.close()


def test_approve_item(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn)

    qid = add_to_queue(conn, vids[0], "2025-03-01T07:00:00")
    assert approve_item(conn, qid) is True

    row = conn.execute("SELECT status FROM publish_queue WHERE id = ?", (qid,)).fetchone()
    assert row["status"] == "approved"
    conn.close()


def test_approve_item_already_approved(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn)

    qid = add_to_queue(conn, vids[0], "2025-03-01T07:00:00")
    approve_item(conn, qid)

    assert approve_item(conn, qid) is False
    conn.close()


def test_approve_nonexistent(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    assert approve_item(conn, 999) is False
    conn.close()


def test_can_publish_all_clear(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    ok, reason = can_publish(conn)
    assert ok is True
    assert reason == "OK"
    conn.close()


def test_can_publish_blocked_by_failures(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn, MAX_CONSECUTIVE_FAILURES)

    for i in range(MAX_CONSECUTIVE_FAILURES):
        conn.execute(
            "INSERT INTO publish_queue (video_id, status, created_at, updated_at) "
            "VALUES (?, 'failed', ?, ?)",
            (vids[i], now_utc(), now_utc()),
        )
    conn.commit()

    ok, reason = can_publish(conn)
    assert ok is False
    assert "consecutive failures" in reason.lower()
    conn.close()


def test_can_publish_blocked_by_interval(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    vids = _seed_video(conn)

    recent = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    conn.execute(
        "INSERT INTO publish_queue (video_id, status, published_at, created_at, updated_at) "
        "VALUES (?, 'published', ?, ?, ?)",
        (vids[0], recent, now_utc(), now_utc()),
    )
    conn.commit()

    ok, reason = can_publish(conn)
    assert ok is False
    assert "wait" in reason.lower()
    conn.close()


def test_process_queue_empty(tmp_path):
    """process_queue with no due items returns 'empty'."""
    from src.publishing.scheduler import process_queue

    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)

    results = process_queue(conn, db_path)
    assert len(results) == 1
    assert results[0]["status"] == "empty"
    conn.close()
