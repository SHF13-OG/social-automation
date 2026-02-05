"""FFmpeg video compositor: audio + footage + text overlays → final TikTok video."""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from src.config import get_config_value
from src.db import now_utc

VIDEO_DIR = Path("media/videos")


def _check_ffmpeg() -> str:
    """Return the path to ffmpeg or raise."""
    path = shutil.which("ffmpeg")
    if path is None:
        raise RuntimeError(
            "ffmpeg not found on PATH. Install it: brew install ffmpeg (macOS) "
            "or apt install ffmpeg (Linux)."
        )
    return path


def _get_audio_duration(audio_path: str) -> float:
    """Probe audio duration in seconds via ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe not found on PATH.")

    result = subprocess.run(
        [
            ffprobe,
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            f"Could not determine audio duration for {audio_path}"
        ) from exc


def _build_text_filter(
    verse_ref: str,
    verse_text: str,
    duration: float,
    db_path: str | None = None,
) -> str:
    """Build the FFmpeg drawtext filter string for verse + prayer overlays."""
    font = get_config_value("text.font_family", "Georgia", db_path)
    verse_size = get_config_value("text.verse_font_size", 48, db_path)
    color = get_config_value("text.color", "#FFFFFF", db_path)
    shadow_color = get_config_value("text.shadow_color", "#000000", db_path)

    # Escape special characters for FFmpeg drawtext
    safe_ref = verse_ref.replace("'", "\\'").replace(":", "\\:")
    safe_text = verse_text.replace("'", "\\'").replace(":", "\\:")
    # Truncate long verse text for on-screen readability
    if len(safe_text) > 120:
        safe_text = safe_text[:117] + "..."

    # Verse card: first 6 seconds
    verse_filter = (
        f"drawtext=text='{safe_ref}'"
        f":fontfile='':font='{font}'"
        f":fontsize={verse_size}"
        f":fontcolor={color}"
        f":shadowcolor={shadow_color}:shadowx=2:shadowy=2"
        f":x=(w-text_w)/2:y=(h-text_h)/2-40"
        f":enable='between(t,0,6)'"
    )

    verse_body = (
        f"drawtext=text='{safe_text}'"
        f":fontfile='':font='{font}'"
        f":fontsize=32"
        f":fontcolor={color}"
        f":shadowcolor={shadow_color}:shadowx=2:shadowy=2"
        f":x=(w-text_w)/2:y=(h/2)+20"
        f":enable='between(t,0,6)'"
    )

    return f"{verse_filter},{verse_body}"


def compose_video(
    audio_path: str,
    footage_paths: list[str],
    verse_ref: str,
    verse_text: str,
    prayer_id: int,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Assemble the final TikTok video.

    Returns a dict with file_path, duration_sec, resolution, file_size_bytes.
    """
    ffmpeg = _check_ffmpeg()

    duration = _get_audio_duration(audio_path)
    resolution = get_config_value("video.resolution", "1080x1920", db_path)
    width, height = resolution.split("x")
    fps = get_config_value("video.fps", 30, db_path)
    bitrate = get_config_value("video.bitrate", "8M", db_path)

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = VIDEO_DIR / f"video_{prayer_id}.mp4"

    # Build the FFmpeg command
    # Strategy: loop the first footage clip to match audio duration,
    # scale to 1080x1920, overlay text, mux with audio.
    if not footage_paths:
        raise RuntimeError("No footage clips provided.")

    footage_input = footage_paths[0]  # Primary clip

    text_filter = _build_text_filter(verse_ref, verse_text, duration, db_path)

    # Build filter complex:
    # 1. Loop/trim footage to match audio duration
    # 2. Scale + crop to portrait (1080x1920)
    # 3. Add text overlays
    filter_complex = (
        f"[0:v]loop=loop=-1:size=1000:start=0,"
        f"trim=duration={duration},"
        f"setpts=PTS-STARTPTS,"
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"{text_filter}"
        f"[outv]"
    )

    cmd = [
        ffmpeg,
        "-y",
        "-i", footage_input,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-b:v", bitrate,
        "-r", str(fps),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(out_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed (exit {result.returncode}):\n{result.stderr[-500:]}"
        )

    file_size = out_path.stat().st_size
    return {
        "file_path": str(out_path),
        "duration_sec": duration,
        "resolution": resolution,
        "file_size_bytes": file_size,
    }


def save_video_record(
    conn: sqlite3.Connection,
    prayer_id: int,
    audio_id: int,
    footage_ids: list[int],
    video_info: dict[str, Any],
    db_path: str | None = None,
) -> int:
    """Insert a generated_videos row and return its id."""
    font_style = get_config_value("text.font_family", "Georgia", db_path)
    font_size = get_config_value("text.verse_font_size", 48, db_path)
    text_position = get_config_value("text.position", "bottom", db_path)

    cur = conn.execute(
        """
        INSERT INTO generated_videos
            (prayer_id, audio_id, footage_ids, file_path, duration_sec,
             resolution, file_size_bytes, font_style, font_size,
             text_position, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prayer_id,
            audio_id,
            json.dumps(footage_ids),
            video_info["file_path"],
            video_info["duration_sec"],
            video_info["resolution"],
            video_info["file_size_bytes"],
            font_style,
            font_size,
            text_position,
            now_utc(),
        ),
    )
    conn.commit()
    return cur.lastrowid
