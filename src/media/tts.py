"""Text-to-speech via ElevenLabs or OpenAI API."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Any

from src.config import get_config_value
from src.db import now_utc

AUDIO_DIR = Path("media/audio")

OPENAI_TTS_SYSTEM_PROMPT = (
    "Speak in a warm, reverent, comforting voice as if leading a heartfelt "
    "prayer. Pace yourself slowly and gently."
)


def _audio_path(prayer_id: int, voice_id: str) -> Path:
    """Deterministic file path for a prayer audio file."""
    return AUDIO_DIR / f"prayer_{prayer_id}_{voice_id}.mp3"


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_audio(
    prayer_id: int,
    prayer_text: str,
    db_path: str | None = None,
    voice_id: str | None = None,
    speed: float | None = None,
) -> dict[str, Any]:
    """Generate an MP3 from prayer text using the configured provider.

    Routes to ElevenLabs or OpenAI based on ``voice.provider`` config.
    Returns a dict with file_path, voice_id, speed, file_hash, file_size.
    """
    provider = get_config_value("voice.provider", "elevenlabs", db_path)
    if provider == "openai":
        return _generate_audio_openai(prayer_id, prayer_text, db_path, voice_id)
    return _generate_audio_elevenlabs(prayer_id, prayer_text, db_path, voice_id, speed)


def _generate_audio_elevenlabs(
    prayer_id: int,
    prayer_text: str,
    db_path: str | None = None,
    voice_id: str | None = None,
    speed: float | None = None,
) -> dict[str, Any]:
    """Generate audio via ElevenLabs SDK."""
    try:
        from elevenlabs import ElevenLabs  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "elevenlabs package is not installed. Run: pip install elevenlabs"
        ) from exc

    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. Add it to your .env file."
        )

    voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID") or get_config_value(
        "voice.default_voice_id", "EXAVITQu4vr4xnSDxMaL", db_path
    )
    speed = speed if speed is not None else get_config_value(
        "voice.speed", 0.95, db_path
    )

    client = ElevenLabs(api_key=api_key)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _audio_path(prayer_id, voice_id)

    audio_iterator = client.text_to_speech.convert(
        voice_id=voice_id,
        text=prayer_text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    with open(out_path, "wb") as f:
        for chunk in audio_iterator:
            f.write(chunk)

    file_size = out_path.stat().st_size
    if file_size == 0:
        out_path.unlink(missing_ok=True)
        raise RuntimeError("ElevenLabs returned empty audio.")

    return {
        "file_path": str(out_path),
        "voice_id": voice_id,
        "speed": speed,
        "file_hash": _file_hash(out_path),
        "file_size": file_size,
    }


def _generate_audio_openai(
    prayer_id: int,
    prayer_text: str,
    db_path: str | None = None,
    voice_id: str | None = None,
) -> dict[str, Any]:
    """Generate audio via OpenAI TTS API."""
    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "openai package is not installed. Run: pip install openai"
        ) from exc

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file."
        )

    voice = voice_id or get_config_value("voice.openai_voice", "onyx", db_path)
    model = get_config_value("voice.openai_model", "gpt-4o-mini-tts", db_path)

    client = OpenAI(api_key=api_key)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _audio_path(prayer_id, voice)

    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=prayer_text,
        instructions=OPENAI_TTS_SYSTEM_PROMPT,
        response_format="mp3",
    )
    response.stream_to_file(str(out_path))

    file_size = out_path.stat().st_size
    if file_size == 0:
        out_path.unlink(missing_ok=True)
        raise RuntimeError("OpenAI TTS returned empty audio.")

    return {
        "file_path": str(out_path),
        "voice_id": voice,
        "speed": 1.0,
        "file_hash": _file_hash(out_path),
        "file_size": file_size,
    }


def save_audio_record(
    conn: sqlite3.Connection,
    prayer_id: int,
    audio_info: dict[str, Any],
) -> int:
    """Insert an audio_files row and return its id."""
    cur = conn.execute(
        """
        INSERT INTO audio_files
            (prayer_id, file_path, voice_id, speed, file_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            prayer_id,
            audio_info["file_path"],
            audio_info["voice_id"],
            audio_info.get("speed", 1.0),
            audio_info.get("file_hash"),
            now_utc(),
        ),
    )
    conn.commit()
    return cur.lastrowid
