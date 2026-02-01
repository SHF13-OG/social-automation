from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st


DEFAULT_DB_PATH = "data/social.db"


def get_db_path() -> str:
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


def load_posts(db_path: str) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT
                post_id,
                created_at,
                views,
                likes,
                comments,
                shares,
                favorites,
                caption,
                url
            FROM tiktok_posts
            """,
            conn,
        )
    finally:
        conn.close()

    if df.empty:
        return df

    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)

    for col in ["views", "likes", "comments", "shares", "favorites"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["engagement"] = df["likes"] + df["comments"] + df["shares"]
    df["engagement_rate"] = df.apply(
        lambda x: (x["engagement"] / x["views"]) if x["views"] > 0 else 0.0, axis=1
    )
    return df


def fmt_int(n: int) -> str:
    return f"{n:,}"


st.set_page_config(page_title="Social Automation Dashboard", layout="wide")
st.title("Social Automation Dashboard")
st.caption("Local dashboard reading from SQLite. No cloud. No drama.")

db_path = get_db_path()
st.sidebar.header("Data")
st.sidebar.code(db_path)

df = load_posts(db_path)

if df.empty:
    st.warning("No data found. Run `python -m src.main doctor` and `python -m src.main import data/tiktok_posts.csv` first.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

now = datetime.now(timezone.utc)
default_start = now - timedelta(days=30)

min_date = df["created_at_dt"].dropna().min()
max_date = df["created_at_dt"].dropna().max()

if pd.isna(min_date) or pd.isna(max_date):
    st.warning("No parsable created_at dates found in DB.")
    st.stop()

start_date, end_date = st.sidebar.date_input(
    "Date range (UTC)",
    value=(max(default_start.date(), min_date.date()), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

min_views = st.sidebar.number_input("Min views", min_value=0, value=0, step=100)
caption_search = st.sidebar.text_input("Caption contains", value="").strip()

filtered = df.copy()
filtered = filtered[filtered["created_at_dt"].notna()]
filtered = filtered[
    (filtered["created_at_dt"].dt.date >= start_date) & (filtered["created_at_dt"].dt.date <= end_date)
]
filtered = filtered[filtered["views"] >= int(min_views)]

if caption_search:
    filtered = filtered[filtered["caption"].fillna("").str.contains(caption_search, case=False, na=False)]

# KPI summary
total_posts = len(filtered)
total_views = int(filtered["views"].sum()) if total_posts else 0
total_eng = int(filtered["engagement"].sum()) if total_posts else 0
avg_er = float(filtered["engagement_rate"].mean()) * 100.0 if total_posts else 0.0
median_views = float(filtered["views"].median()) if total_posts else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Posts", fmt_int(total_posts))
c2.metric("Total views", fmt_int(total_views))
c3.metric("Total engagement", fmt_int(total_eng))
c4.metric("Avg engagement rate", f"{avg_er:.2f}%")
c5.metric("Median views", f"{median_views:.1f}")

st.divider()

# Charts
left, right = st.columns(2)

with left:
    st.subheader("Views over time")
    chart_df = filtered.copy()
    chart_df["day"] = chart_df["created_at_dt"].dt.date
    by_day = chart_df.groupby("day", as_index=False)["views"].sum()
    st.line_chart(by_day, x="day", y="views")

with right:
    st.subheader("Engagement rate over time (avg per day)")
    chart_df = filtered.copy()
    chart_df["day"] = chart_df["created_at_dt"].dt.date
    by_day = chart_df.groupby("day", as_index=False)["engagement_rate"].mean()
    by_day["engagement_rate_pct"] = by_day["engagement_rate"] * 100.0
    st.line_chart(by_day, x="day", y="engagement_rate_pct")

st.divider()

# Table
st.subheader("Posts")
show = filtered.sort_values("views", ascending=False).copy()
show["engagement_rate_pct"] = (show["engagement_rate"] * 100.0).round(2)
show = show[
    ["post_id", "created_at", "views", "likes", "comments", "shares", "engagement", "engagement_rate_pct", "caption", "url"]
]
st.dataframe(show, use_container_width=True, hide_index=True)

# Recommendations
st.subheader("Recommendations (simple heuristics)")
recs = []
if avg_er < 2.0:
    recs.append("Engagement rate is low. Tighten the first 1-2 seconds, reduce on-screen text, and make the payoff clearer.")
if median_views < 500:
    recs.append("Median views are low. Run a 7-day posting experiment and test two posting times (morning vs evening).")
if int(filtered["shares"].sum()) == 0:
    recs.append("Zero shares in this window. Try a direct prompt: 'Send this to someone who needs it.'")
if total_posts < 5:
    recs.append("Not enough posts in the filtered window to trust patterns. Get 5-10 posts before changing strategy.")

if recs:
    for r in recs:
        st.write(f"- {r}")
else:
    st.write("- Nothing obvious. Keep posting and iterate.")

