"""Stock footage search & download from Pexels and Pixabay."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

import httpx

from src.config import get_config_value
from src.db import now_utc

FOOTAGE_DIR = Path("media/footage")

# ---------------------------------------------------------------------------
# Pexels
# ---------------------------------------------------------------------------

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"


def search_pexels(
    query: str,
    orientation: str = "portrait",
    per_page: int = 5,
) -> list[dict[str, Any]]:
    """Search Pexels for videos. Returns a list of simplified result dicts."""
    api_key = os.getenv("PEXELS_API_KEY", "")
    if not api_key:
        raise RuntimeError("PEXELS_API_KEY is not set.")

    resp = httpx.get(
        PEXELS_SEARCH_URL,
        headers={"Authorization": api_key},
        params={
            "query": query,
            "orientation": orientation,
            "per_page": per_page,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    results: list[dict[str, Any]] = []
    for video in data.get("videos", []):
        # Pick the best HD file
        best_file = _pick_best_pexels_file(video.get("video_files", []))
        if not best_file:
            continue
        results.append({
            "source": "pexels",
            "external_id": str(video["id"]),
            "url": video.get("url", ""),
            "download_url": best_file["link"],
            "duration_sec": video.get("duration", 0),
            "resolution": f"{best_file.get('width', 0)}x{best_file.get('height', 0)}",
            "attribution": f"Pexels - {video.get('user', {}).get('name', 'Unknown')}",
        })
    return results


def _pick_best_pexels_file(
    files: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Pick the highest-quality HD video file from Pexels results."""
    hd_files = [
        f for f in files
        if f.get("quality") == "hd" and f.get("height", 0) >= 1080
    ]
    if hd_files:
        return max(hd_files, key=lambda f: f.get("height", 0))
    # Fallback to any file with >= 720 height
    ok_files = [f for f in files if f.get("height", 0) >= 720]
    if ok_files:
        return max(ok_files, key=lambda f: f.get("height", 0))
    return files[0] if files else None


# ---------------------------------------------------------------------------
# Pixabay
# ---------------------------------------------------------------------------

PIXABAY_SEARCH_URL = "https://pixabay.com/api/videos/"


def search_pixabay(
    query: str,
    per_page: int = 5,
) -> list[dict[str, Any]]:
    """Search Pixabay for videos. Returns a list of simplified result dicts."""
    api_key = os.getenv("PIXABAY_API_KEY", "")
    if not api_key:
        raise RuntimeError("PIXABAY_API_KEY is not set.")

    resp = httpx.get(
        PIXABAY_SEARCH_URL,
        params={
            "key": api_key,
            "q": query,
            "per_page": per_page,
            "video_type": "film",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    results: list[dict[str, Any]] = []
    for hit in data.get("hits", []):
        videos = hit.get("videos", {})
        # Prefer "large" then "medium"
        best = videos.get("large") or videos.get("medium") or {}
        if not best.get("url"):
            continue
        results.append({
            "source": "pixabay",
            "external_id": str(hit["id"]),
            "url": hit.get("pageURL", ""),
            "download_url": best["url"],
            "duration_sec": hit.get("duration", 0),
            "resolution": f"{best.get('width', 0)}x{best.get('height', 0)}",
            "attribution": f"Pixabay - {hit.get('user', 'Unknown')}",
        })
    return results


# ---------------------------------------------------------------------------
# Unified search + download
# ---------------------------------------------------------------------------


def search_footage(
    keywords: list[str],
    db_path: str | None = None,
    max_results: int = 3,
) -> list[dict[str, Any]]:
    """Search for stock footage using configured primary + fallback sources.

    *keywords* is a list of search queries (from the theme).  We try each
    query on the primary source first, then fall back.
    """
    primary = get_config_value("footage.primary_source", "pexels", db_path)
    fallback = get_config_value("footage.fallback_source", "pixabay", db_path)
    orientation = get_config_value(
        "footage.search_filters.orientation", "portrait", db_path
    )

    all_results: list[dict[str, Any]] = []

    for query in keywords:
        if len(all_results) >= max_results:
            break

        # Try primary source
        try:
            if primary == "pexels":
                results = search_pexels(query, orientation=orientation, per_page=3)
            else:
                results = search_pixabay(query, per_page=3)
            all_results.extend(results)
        except (RuntimeError, httpx.HTTPError):
            # Try fallback
            try:
                if fallback == "pixabay":
                    results = search_pixabay(query, per_page=3)
                else:
                    results = search_pexels(query, orientation=orientation, per_page=3)
                all_results.extend(results)
            except (RuntimeError, httpx.HTTPError):
                continue

    # Deduplicate by (source, external_id)
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for r in all_results:
        key = (r["source"], r["external_id"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique[:max_results]


def download_clip(
    clip: dict[str, Any],
    theme_slug: str = "general",
) -> Path:
    """Download a single video clip to media/footage/ and return the path."""
    FOOTAGE_DIR.mkdir(parents=True, exist_ok=True)

    ext = "mp4"
    filename = f"{clip['source']}_{clip['external_id']}_{theme_slug}.{ext}"
    out_path = FOOTAGE_DIR / filename

    if out_path.exists():
        return out_path

    resp = httpx.get(clip["download_url"], timeout=120, follow_redirects=True)
    resp.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(resp.content)

    return out_path


def save_footage_record(
    conn: sqlite3.Connection,
    clip: dict[str, Any],
    download_path: str,
    theme_id: int | None = None,
    keywords: list[str] | None = None,
) -> int:
    """Insert a stock_footage row (skip if source+external_id exists). Return id."""
    existing = conn.execute(
        "SELECT id FROM stock_footage WHERE source = ? AND external_id = ?",
        (clip["source"], clip["external_id"]),
    ).fetchone()
    if existing:
        return existing["id"]

    cur = conn.execute(
        """
        INSERT INTO stock_footage
            (source, external_id, url, download_path, keywords,
             duration_sec, resolution, attribution, theme_id, downloaded_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            clip["source"],
            clip["external_id"],
            clip.get("url", ""),
            download_path,
            json.dumps(keywords or []),
            clip.get("duration_sec"),
            clip.get("resolution"),
            clip.get("attribution"),
            theme_id,
            now_utc(),
            now_utc(),
        ),
    )
    conn.commit()
    return cur.lastrowid
