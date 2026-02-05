"""Publish Queue dashboard page - view, approve, and manage scheduled posts."""

from __future__ import annotations

import os
import sqlite3

import pandas as pd
import streamlit as st

DEFAULT_DB_PATH = "data/social.db"


def get_db_path() -> str:
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


def load_queue(db_path: str) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT
                pq.id AS queue_id,
                pq.video_id,
                pq.platform,
                pq.scheduled_at,
                pq.status,
                pq.published_at,
                pq.external_post_id,
                pq.error_message,
                pq.retry_count,
                pq.created_at,
                bv.reference AS verse_ref,
                t.name AS theme_name
            FROM publish_queue pq
            LEFT JOIN generated_videos gv ON gv.id = pq.video_id
            LEFT JOIN prayers p ON p.id = gv.prayer_id
            LEFT JOIN bible_verses bv ON bv.id = p.verse_id
            LEFT JOIN themes t ON t.id = p.theme_id
            ORDER BY pq.scheduled_at DESC
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def approve_item(db_path: str, queue_id: int) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        from src.db import now_utc

        cur = conn.execute(
            "UPDATE publish_queue SET status = 'approved', updated_at = ? "
            "WHERE id = ? AND status = 'pending'",
            (now_utc(), queue_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_safety_status(db_path: str) -> dict:
    """Check current safety status."""
    if not os.path.exists(db_path):
        return {"published_count": 0, "needs_approval": True, "can_publish": True, "reason": "OK"}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        published = conn.execute(
            "SELECT COUNT(*) as cnt FROM publish_queue WHERE status = 'published'"
        ).fetchone()["cnt"]

        pending = conn.execute(
            "SELECT COUNT(*) as cnt FROM publish_queue WHERE status = 'pending'"
        ).fetchone()["cnt"]

        approved = conn.execute(
            "SELECT COUNT(*) as cnt FROM publish_queue WHERE status = 'approved'"
        ).fetchone()["cnt"]

        failed = conn.execute(
            "SELECT COUNT(*) as cnt FROM publish_queue WHERE status = 'failed'"
        ).fetchone()["cnt"]

        # Check consecutive failures
        recent = conn.execute(
            "SELECT status FROM publish_queue ORDER BY updated_at DESC LIMIT 3"
        ).fetchall()
        consecutive_fails = (
            len(recent) >= 3 and all(r["status"] == "failed" for r in recent)
        )

        return {
            "published_count": published,
            "pending_count": pending,
            "approved_count": approved,
            "failed_count": failed,
            "needs_approval": published < 10,
            "consecutive_fails": consecutive_fails,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Publish Queue", layout="wide")
st.title("Publish Queue")
st.caption("Manage scheduled posts, approvals, and publishing status.")

db_path = get_db_path()

# Safety status
st.subheader("Safety Status")
safety = get_safety_status(db_path)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Published", safety.get("published_count", 0))
col2.metric("Pending", safety.get("pending_count", 0))
col3.metric("Approved", safety.get("approved_count", 0))
col4.metric("Failed", safety.get("failed_count", 0))

if safety.get("consecutive_fails"):
    st.error(
        "Publishing is PAUSED due to 3 consecutive failures. "
        "Review errors below before continuing."
    )
elif safety.get("needs_approval"):
    remaining = 10 - safety.get("published_count", 0)
    st.warning(
        f"Human approval mode: {remaining} more posts require manual approval "
        "before auto-publishing is enabled."
    )
else:
    st.success("Auto-publishing enabled. All safety checks passing.")

st.divider()

# Queue table
st.subheader("Queue Items")
queue_df = load_queue(db_path)

if queue_df.empty:
    st.info(
        "Queue is empty. Schedule a video: "
        "`python -m src.main schedule <video_id> <datetime>`"
    )
else:
    # Status filter
    status_options = ["All"] + sorted(queue_df["status"].dropna().unique().tolist())
    status_filter = st.selectbox("Filter by status", status_options)

    filtered = queue_df.copy()
    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]

    # Display columns
    display_cols = [
        "queue_id", "verse_ref", "theme_name", "platform",
        "scheduled_at", "status", "published_at", "retry_count", "error_message",
    ]
    available = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[available], hide_index=True, width="stretch")

    # Approve pending items
    pending_items = filtered[filtered["status"] == "pending"]
    if not pending_items.empty:
        st.subheader("Approve Pending Items")
        for _, row in pending_items.iterrows():
            qid = row["queue_id"]
            label = f"#{qid} — {row.get('verse_ref', '?')} ({row.get('theme_name', '?')})"
            if st.button(f"Approve {label}", key=f"approve_{qid}"):
                if approve_item(db_path, qid):
                    st.success(f"Approved queue item #{qid}")
                    st.rerun()
                else:
                    st.error(f"Could not approve #{qid} (may already be approved)")

    # Show errors for failed items
    failed_items = filtered[filtered["status"] == "failed"]
    if not failed_items.empty:
        st.subheader("Failed Items")
        for _, row in failed_items.iterrows():
            with st.expander(
                f"#{row['queue_id']} — {row.get('verse_ref', '?')} "
                f"(retries: {row.get('retry_count', 0)})"
            ):
                st.code(row.get("error_message", "No error message"))
