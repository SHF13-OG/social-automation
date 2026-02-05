"""Configuration dashboard page - view and edit settings with DB overrides."""

from __future__ import annotations

import json
import os

import streamlit as st
from src.config import (
    delete_config_override,
    flatten_config,
    load_config,
    load_db_overrides,
    set_config_override,
)

DEFAULT_DB_PATH = "data/social.db"


def get_db_path() -> str:
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Configuration", layout="wide")
st.title("Configuration")
st.caption("View YAML defaults, manage dashboard overrides stored in SQLite.")

db_path = get_db_path()

# Load current merged config
config = load_config(db_path)
flat = flatten_config(config)
overrides = load_db_overrides(db_path)

# ---------------------------------------------------------------------------
# Current config table
# ---------------------------------------------------------------------------

st.subheader("Current Configuration (YAML + Overrides)")
st.caption("Values with a database override are highlighted.")

for key, value in flat:
    is_override = key in overrides
    prefix = "**[override]** " if is_override else ""
    st.text(f"{prefix}{key} = {value}")

st.divider()

# ---------------------------------------------------------------------------
# Active overrides
# ---------------------------------------------------------------------------

st.subheader("Active Overrides")

if not overrides:
    st.info("No overrides set. All values come from config/default.yaml.")
else:
    for key, value in overrides.items():
        col1, col2, col3 = st.columns([3, 4, 1])
        col1.code(key)
        col2.code(json.dumps(value))
        if col3.button("Delete", key=f"del_{key}"):
            delete_config_override(key, db_path)
            st.success(f"Deleted override: {key}")
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Edit / add override
# ---------------------------------------------------------------------------

st.subheader("Set Override")
st.caption(
    "Override any config value. Use dotted keys like `voice.speed`. "
    "Values are stored in the `config_overrides` table."
)

with st.form("override_form"):
    col_key, col_val = st.columns(2)
    with col_key:
        new_key = st.text_input("Key (dotted)", placeholder="voice.speed")
    with col_val:
        new_value_str = st.text_input("Value (JSON)", placeholder="0.85")

    submitted = st.form_submit_button("Save Override")

    if submitted:
        if not new_key.strip():
            st.error("Key cannot be empty.")
        elif not new_value_str.strip():
            st.error("Value cannot be empty.")
        else:
            try:
                parsed = json.loads(new_value_str)
            except json.JSONDecodeError:
                # Treat as raw string if not valid JSON
                parsed = new_value_str.strip()

            set_config_override(new_key.strip(), parsed, db_path)
            st.success(f"Override saved: {new_key.strip()} = {parsed}")
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Quick settings
# ---------------------------------------------------------------------------

st.subheader("Quick Settings")
st.caption("Common settings with friendly controls.")

# Voice speed
current_speed = config.get("voice", {}).get("speed", 0.95)
new_speed = st.slider(
    "Voice speed", min_value=0.5, max_value=1.5, value=float(current_speed), step=0.05
)
if new_speed != current_speed:
    if st.button("Save voice speed"):
        set_config_override("voice.speed", new_speed, db_path)
        st.success(f"Voice speed set to {new_speed}")
        st.rerun()

# Prayer font size
current_font = config.get("text", {}).get("prayer_font_size", 36)
new_font = st.slider(
    "Prayer font size", min_value=20, max_value=72, value=int(current_font), step=2
)
if new_font != current_font:
    if st.button("Save prayer font size"):
        set_config_override("text.prayer_font_size", new_font, db_path)
        st.success(f"Prayer font size set to {new_font}")
        st.rerun()

# Min hours between posts
current_interval = config.get("publishing", {}).get("min_hours_between_posts", 4)
new_interval = st.number_input(
    "Min hours between posts",
    min_value=1,
    max_value=24,
    value=int(current_interval),
    step=1,
)
if new_interval != current_interval:
    if st.button("Save post interval"):
        set_config_override("publishing.min_hours_between_posts", new_interval, db_path)
        st.success(f"Min hours between posts set to {new_interval}")
        st.rerun()

# Theme activation toggles
st.divider()
st.subheader("Theme Activation")

if os.path.exists(db_path):
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        themes = conn.execute(
            "SELECT id, slug, name, is_active FROM themes ORDER BY slug"
        ).fetchall()

        if themes:
            for theme in themes:
                active = bool(theme["is_active"])
                new_active = st.checkbox(
                    f"{theme['name']} ({theme['slug']})",
                    value=active,
                    key=f"theme_active_{theme['id']}",
                )
                if new_active != active:
                    conn.execute(
                        "UPDATE themes SET is_active = ? WHERE id = ?",
                        (1 if new_active else 0, theme["id"]),
                    )
                    conn.commit()
                    st.rerun()
        else:
            st.info("No themes in database.")
    finally:
        conn.close()
