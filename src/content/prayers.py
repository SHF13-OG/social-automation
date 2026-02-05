"""Prayer text generation using LLM (OpenAI) or a fallback template."""

from __future__ import annotations

import os
import sqlite3
from typing import Any

from src.db import now_utc

# Target word-count range for ~62-70s at 140 WPM
MIN_WORDS = 140  # ~60s floor
MAX_WORDS = 165  # ~70s ceiling
TARGET_WORDS = 150  # sweet spot ≈65s


def _build_system_prompt(theme_name: str, tone: str) -> str:
    return (
        "You are a prayer writer for a daily TikTok series aimed at Christians "
        "aged 45 and older. Your prayers should feel personal, conversational, "
        "and spoken directly to God.\n\n"
        "RULES:\n"
        f"- Write exactly {TARGET_WORDS} words (hard limit: {MIN_WORDS}-{MAX_WORDS}).\n"
        "- Use second-person address to God (\"Father\", \"Lord\", \"God\").\n"
        "- Match the theme and tone provided.\n"
        "- Never use prosperity-gospel language (\"claim your blessing\", "
        "\"name it and claim it\", etc.).\n"
        "- Never promise physical healing or financial gain.\n"
        "- Be honest about struggle while pointing to hope.\n"
        "- End with a brief, humble closing (\"In Jesus' name, Amen\" or similar).\n"
        "- Do NOT include the Bible verse text in your prayer. The verse will be "
        "shown separately in the video.\n"
        "- Output ONLY the prayer text, no titles or labels."
    )


def _build_user_prompt(
    verse_reference: str, verse_text: str, theme_name: str, tone: str
) -> str:
    return (
        f"Theme: {theme_name}\n"
        f"Tone: {tone}\n"
        f"Verse: {verse_reference} — \"{verse_text}\"\n\n"
        f"Write a {TARGET_WORDS}-word prayer inspired by this verse for the theme above."
    )


def generate_prayer_text(
    verse: dict[str, Any],
    theme: dict[str, Any],
    model: str = "gpt-4o-mini",
) -> str:
    """Generate prayer text via OpenAI. Raises if no API key is set."""
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

    client = OpenAI(api_key=api_key)

    theme_name = theme.get("name", "")
    tone = theme.get("tone", "")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _build_system_prompt(theme_name, tone)},
            {
                "role": "user",
                "content": _build_user_prompt(
                    verse["reference"], verse["text"], theme_name, tone
                ),
            },
        ],
        temperature=0.8,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


def generate_prayer_text_fallback(
    verse: dict[str, Any],
    theme: dict[str, Any],
) -> str:
    """Simple template-based fallback when no LLM API key is available."""
    tone = theme.get("tone", "comforting")
    name = theme.get("name", "faith")
    ref = verse["reference"]

    return (
        f"Heavenly Father, we come before You today with hearts open to Your word. "
        f"As we reflect on {ref}, we are reminded of Your faithfulness. "
        f"Lord, in this season of {name.lower()}, grant us a spirit that is {tone}. "
        f"Help us to trust in Your plan even when the path is unclear. "
        f"We know that You hold every moment of our lives in Your hands. "
        f"Strengthen us, Lord, to face each day with courage and grace. "
        f"Remind us that we are never alone, for You walk beside us always. "
        f"Fill our hearts with peace that surpasses all understanding. "
        f"May our words and actions reflect Your love to those around us. "
        f"Guide us to be a light in the lives of our families and communities. "
        f"We surrender our worries, our fears, and our doubts to You. "
        f"Replace them with hope, with faith, and with the assurance of Your promises. "
        f"Thank You, Father, for never giving up on us. "
        f"Thank You for Your mercy that is new every morning. "
        f"We love You, and we trust You with all that lies ahead. "
        f"In Jesus' name, Amen."
    )


def save_prayer(
    conn: sqlite3.Connection,
    verse_id: int,
    theme_id: int,
    prayer_text: str,
    ai_model: str | None = None,
) -> int:
    """Insert a prayer into the database and return its id."""
    word_count = len(prayer_text.split())
    cur = conn.execute(
        """
        INSERT INTO prayers (verse_id, theme_id, prayer_text, word_count,
                             ai_model, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (verse_id, theme_id, prayer_text, word_count, ai_model, now_utc()),
    )
    conn.commit()
    return cur.lastrowid
