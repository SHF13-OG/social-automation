"""Theme selection and rotation logic."""

from __future__ import annotations

import random
import sqlite3
from typing import Any


def get_active_themes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return all active themes as dicts."""
    cur = conn.execute(
        "SELECT id, slug, name, description, keywords, tone "
        "FROM themes WHERE is_active = 1 ORDER BY slug"
    )
    return [dict(row) for row in cur.fetchall()]


def get_theme_by_slug(
    conn: sqlite3.Connection, slug: str
) -> dict[str, Any] | None:
    """Fetch a single theme by slug, or None if not found."""
    cur = conn.execute(
        "SELECT id, slug, name, description, keywords, tone, is_active "
        "FROM themes WHERE slug = ?",
        (slug,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def pick_theme(
    conn: sqlite3.Connection,
    slug: str | None = None,
) -> dict[str, Any] | None:
    """Pick a theme for content generation.

    If *slug* is given, return that specific theme (must be active).
    Otherwise pick the active theme whose verses were least recently used,
    breaking ties randomly.  This creates a natural rotation across themes.
    """
    if slug:
        theme = get_theme_by_slug(conn, slug)
        if theme and theme.get("is_active"):
            return theme
        return None

    # Rank active themes by the latest last_used_at of their verses
    # (themes with no usage history sort first → freshest).
    cur = conn.execute(
        """
        SELECT t.id, t.slug, t.name, t.description, t.keywords, t.tone,
               MAX(bv.last_used_at) AS latest_use
        FROM themes t
        LEFT JOIN bible_verses bv ON bv.theme_id = t.id
        WHERE t.is_active = 1
        GROUP BY t.id
        ORDER BY latest_use IS NOT NULL,   -- NULLs (never used) first
                 latest_use ASC            -- then oldest usage
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    if not rows:
        return None

    # Take all themes tied for "least recently used"
    first_use = rows[0].get("latest_use")
    candidates = [r for r in rows if r.get("latest_use") == first_use]
    chosen = random.choice(candidates)
    # Drop the helper column before returning
    chosen.pop("latest_use", None)
    return chosen
