"""Content Pipeline dashboard page - view generated prayers and preview content."""

from __future__ import annotations

import os
import sqlite3

import pandas as pd
import streamlit as st

DEFAULT_DB_PATH = "data/social.db"


def get_db_path() -> str:
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


def load_prayers(db_path: str) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        df = pd.read_sql_query(
            """
            SELECT
                p.id AS prayer_id,
                p.prayer_text,
                p.word_count,
                p.ai_model,
                p.created_at,
                bv.reference AS verse_ref,
                bv.text AS verse_text,
                t.slug AS theme_slug,
                t.name AS theme_name,
                t.tone
            FROM prayers p
            LEFT JOIN bible_verses bv ON bv.id = p.verse_id
            LEFT JOIN themes t ON t.id = p.theme_id
            ORDER BY p.created_at DESC
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def load_videos(db_path: str) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT
                gv.id AS video_id,
                gv.prayer_id,
                gv.file_path,
                gv.duration_sec,
                gv.resolution,
                gv.file_size_bytes,
                gv.created_at,
                p.word_count,
                bv.reference AS verse_ref,
                t.name AS theme_name
            FROM generated_videos gv
            LEFT JOIN prayers p ON p.id = gv.prayer_id
            LEFT JOIN bible_verses bv ON bv.id = p.verse_id
            LEFT JOIN themes t ON t.id = p.theme_id
            ORDER BY gv.created_at DESC
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def load_themes_summary(db_path: str) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT
                t.slug,
                t.name,
                t.tone,
                t.is_active,
                COUNT(DISTINCT bv.id) AS verse_count,
                COUNT(DISTINCT p.id) AS prayer_count,
                COUNT(DISTINCT gv.id) AS video_count
            FROM themes t
            LEFT JOIN bible_verses bv ON bv.theme_id = t.id
            LEFT JOIN prayers p ON p.theme_id = t.id
            LEFT JOIN generated_videos gv ON gv.prayer_id = p.id
            GROUP BY t.id
            ORDER BY t.slug
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Content Pipeline", layout="wide")
st.title("Content Pipeline")
st.caption("View generated prayers, videos, and theme coverage.")

db_path = get_db_path()

# Theme overview
st.subheader("Theme Coverage")
themes_df = load_themes_summary(db_path)

if themes_df.empty:
    st.info("No themes found. Run `python -m src.main init-themes` first.")
else:
    themes_df["active"] = themes_df["is_active"].apply(lambda x: "Yes" if x else "No")
    st.dataframe(
        themes_df[["slug", "name", "tone", "active", "verse_count", "prayer_count", "video_count"]],
        hide_index=True,
        width="stretch",
    )

st.divider()

# Recent prayers
st.subheader("Generated Prayers")
prayers_df = load_prayers(db_path)

if prayers_df.empty:
    st.info("No prayers generated yet. Run `python -m src.main generate --theme grief`.")
else:
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        theme_filter = st.selectbox(
            "Filter by theme",
            ["All"] + sorted(prayers_df["theme_slug"].dropna().unique().tolist()),
        )
    with col2:
        model_filter = st.selectbox(
            "Filter by model",
            ["All"] + sorted(prayers_df["ai_model"].dropna().unique().tolist()),
        )

    filtered = prayers_df.copy()
    if theme_filter != "All":
        filtered = filtered[filtered["theme_slug"] == theme_filter]
    if model_filter != "All":
        filtered = filtered[filtered["ai_model"] == model_filter]

    st.metric("Prayers shown", len(filtered))

    for _, row in filtered.head(20).iterrows():
        with st.expander(
            f"Prayer #{row['prayer_id']} — {row['verse_ref']} ({row['theme_name']}) "
            f"[{row['word_count']} words]"
        ):
            st.markdown(f"**Verse:** {row['verse_ref']}")
            st.markdown(f"> {row['verse_text']}")
            st.markdown(f"**Theme:** {row['theme_name']} | **Tone:** {row['tone']}")
            st.markdown(f"**Model:** {row['ai_model']} | **Created:** {row['created_at']}")
            st.markdown("---")
            st.markdown(row["prayer_text"])

st.divider()

# Generated videos
st.subheader("Generated Videos")
videos_df = load_videos(db_path)

if videos_df.empty:
    st.info("No videos generated yet. Run `python -m src.main compose <prayer_id>`.")
else:
    st.dataframe(
        videos_df[
            ["video_id", "verse_ref", "theme_name", "duration_sec", "resolution",
             "file_size_bytes", "file_path", "created_at"]
        ],
        hide_index=True,
        width="stretch",
    )
