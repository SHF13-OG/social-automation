"""Tests for src/content/prayers.py - prayer generation and storage."""

from src.content.prayers import (
    TARGET_WORDS,
    _build_system_prompt,
    _build_user_prompt,
    generate_prayer_text_fallback,
    save_prayer,
)
from src.db import connect, init_schema, now_utc


def _seed_theme_and_verse(conn):
    """Insert one theme + one verse, return (theme dict, verse dict)."""
    conn.execute(
        "INSERT INTO themes (slug, name, tone, is_active, created_at) "
        "VALUES ('grief', 'Grief & Loss', 'comforting', 1, ?)",
        (now_utc(),),
    )
    conn.commit()
    theme_id = conn.execute(
        "SELECT id FROM themes WHERE slug = 'grief'"
    ).fetchone()["id"]

    conn.execute(
        "INSERT INTO bible_verses (reference, text, theme_id, created_at) "
        "VALUES ('Psalm 23:4', 'Even though I walk through the valley...', ?, ?)",
        (theme_id, now_utc()),
    )
    conn.commit()
    verse_row = conn.execute(
        "SELECT id, reference, text FROM bible_verses WHERE theme_id = ?",
        (theme_id,),
    ).fetchone()

    theme = {"id": theme_id, "slug": "grief", "name": "Grief & Loss", "tone": "comforting"}
    verse = {"id": verse_row["id"], "reference": verse_row["reference"], "text": verse_row["text"]}
    return theme, verse


def test_build_system_prompt_contains_rules():
    prompt = _build_system_prompt("Grief & Loss", "comforting")
    assert "prosperity-gospel" in prompt.lower() or "prosperity" in prompt.lower()
    assert str(TARGET_WORDS) in prompt
    assert "prayer" in prompt.lower()
    # Verse should be woven in, not excluded
    assert "weave" in prompt.lower()
    assert "shown separately" not in prompt.lower()


def test_build_user_prompt_contains_verse():
    prompt = _build_user_prompt("Psalm 23:4", "Valley of shadow...", "Grief", "comforting")
    assert "Psalm 23:4" in prompt
    assert "Grief" in prompt
    assert "comforting" in prompt


def test_build_user_prompt_with_hook():
    prompt = _build_user_prompt(
        "Psalm 23:4", "Valley of shadow...", "Grief", "comforting",
        hook="Have you lost someone you deeply love?",
    )
    assert "Have you lost someone you deeply love?" in prompt
    assert "Hook question" in prompt


def test_build_user_prompt_without_hook():
    prompt = _build_user_prompt("Psalm 23:4", "Valley of shadow...", "Grief", "comforting")
    assert "Hook question" not in prompt


def test_fallback_produces_reasonable_text():
    theme = {"name": "Grief & Loss", "tone": "comforting"}
    verse = {"reference": "Psalm 23:4", "text": "Valley of shadow..."}

    text = generate_prayer_text_fallback(verse, theme)

    # Should be a reasonable prayer
    assert "Father" in text or "Lord" in text
    assert "Amen" in text
    assert "Psalm" in text and "23" in text
    assert "grief" in text.lower()

    # Word count should be in a reasonable range
    word_count = len(text.split())
    assert word_count >= 80  # fallback is shorter than LLM but still substantial


def test_fallback_adapts_to_theme():
    theme1 = {"name": "Health Challenges", "tone": "hopeful"}
    theme2 = {"name": "Legacy & Purpose", "tone": "inspiring"}
    verse = {"reference": "Isaiah 41:10", "text": "Fear not..."}

    text1 = generate_prayer_text_fallback(verse, theme1)
    text2 = generate_prayer_text_fallback(verse, theme2)

    assert "health challenges" in text1.lower()
    assert "legacy" in text2.lower()


def test_save_prayer(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    theme, verse = _seed_theme_and_verse(conn)

    prayer_text = "Heavenly Father, we come before You today..."
    prayer_id = save_prayer(
        conn, verse["id"], theme["id"], prayer_text, ai_model="gpt-4o-mini"
    )
    assert prayer_id is not None
    assert prayer_id > 0

    row = conn.execute("SELECT * FROM prayers WHERE id = ?", (prayer_id,)).fetchone()
    assert row["prayer_text"] == prayer_text
    assert row["verse_id"] == verse["id"]
    assert row["theme_id"] == theme["id"]
    assert row["ai_model"] == "gpt-4o-mini"
    assert row["word_count"] == len(prayer_text.split())
    conn.close()


def test_save_prayer_without_model(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    theme, verse = _seed_theme_and_verse(conn)

    prayer_id = save_prayer(conn, verse["id"], theme["id"], "Lord, hear our prayer.")
    row = conn.execute("SELECT ai_model FROM prayers WHERE id = ?", (prayer_id,)).fetchone()
    assert row["ai_model"] is None
    conn.close()


def test_generate_prayer_text_raises_without_openai(tmp_path, monkeypatch):
    """generate_prayer_text should raise RuntimeError when openai missing or no key."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from src.content.prayers import generate_prayer_text

    theme = {"name": "Grief & Loss", "tone": "comforting"}
    verse = {"reference": "Psalm 23:4", "text": "Valley..."}

    try:
        generate_prayer_text(verse, theme)
        assert False, "Should have raised RuntimeError"
    except RuntimeError:
        pass  # Either "openai not installed" or "OPENAI_API_KEY not set"
