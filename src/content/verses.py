"""Verse selection with rotation to avoid recent repeats."""

from __future__ import annotations

import random
import sqlite3
from typing import Any

from src.db import now_utc


def get_verses_for_theme(
    conn: sqlite3.Connection, theme_id: int
) -> list[dict[str, Any]]:
    """Return all verses belonging to *theme_id*, ordered by used_count ASC."""
    cur = conn.execute(
        "SELECT id, reference, text, translation, tone, used_count, last_used_at "
        "FROM bible_verses WHERE theme_id = ? ORDER BY used_count ASC, last_used_at ASC",
        (theme_id,),
    )
    return [dict(row) for row in cur.fetchall()]


def pick_verse(
    conn: sqlite3.Connection,
    theme_id: int,
) -> dict[str, Any] | None:
    """Pick the least-recently-used verse for a theme.

    Verses with the lowest ``used_count`` are preferred.  Among those,
    we pick randomly to keep things fresh.
    """
    verses = get_verses_for_theme(conn, theme_id)
    if not verses:
        return None

    min_count = verses[0]["used_count"] or 0
    candidates = [v for v in verses if (v["used_count"] or 0) == min_count]
    return random.choice(candidates)


def mark_verse_used(conn: sqlite3.Connection, verse_id: int) -> None:
    """Increment used_count and set last_used_at for a verse."""
    conn.execute(
        """
        UPDATE bible_verses
        SET used_count = COALESCE(used_count, 0) + 1,
            last_used_at = ?
        WHERE id = ?
        """,
        (now_utc(), verse_id),
    )
    conn.commit()
