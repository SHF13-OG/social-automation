from __future__ import annotations

import os
import sqlite3
import subprocess
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

DEFAULT_DB_PATH = "data/social.db"
LOCAL_TZ = ZoneInfo("America/Chicago")

# Bump this key if Streamlit ever caches a bad range again
DATE_RANGE_KEY = "date_range_central_v2"
MIN_VIEWS_KEY = "min_views"
CAPTION_KEY = "caption_search"


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

    # Parse timestamps as UTC, then convert for display and filtering
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df["created_at_local"] = df["created_at_dt"].dt.tz_convert(LOCAL_TZ)

    for col in ["views", "likes", "comments", "shares", "favorites"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["engagement"] = df["likes"] + df["comments"] + df["shares"]

    # Avoid divide-by-zero
    views_nonzero = df["views"].replace({0: pd.NA})
    df["engagement_rate"] = (df["engagement"] / views_nonzero).fillna(0.0)

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
    st.warning(
        "No data found. Run `python -m src.main doctor` and `python -m src.main import data/tiktok_posts.csv` first."
    )
    st.stop()

# Filters
st.sidebar.header("Filters")

min_ts = df["created_at_local"].dropna().min()
max_ts = df["created_at_local"].dropna().max()

if pd.isna(min_ts) or pd.isna(max_ts):
    st.warning("No parsable created_at dates found in DB.")
    st.stop()

min_d = min_ts.date()
max_d = max_ts.date()

# Default to last 30 days of AVAILABLE data (based on max date in DB)
suggested_start = (max_ts.to_pydatetime() - timedelta(days=30)).date()
start_default = max(min_d, suggested_start)
end_default = max_d

# Safety clamp
if start_default > end_default:
    start_default = end_default

# IMPORTANT: Streamlit can keep an old, bad range in session state.
# If it's invalid or reversed, force-reset it BEFORE rendering the widget.
if DATE_RANGE_KEY in st.session_state:
    v = st.session_state[DATE_RANGE_KEY]
    if isinstance(v, (tuple, list)) and len(v) == 2:
        s, e = v
    else:
        s = e = v

    invalid = (
        s is None
        or e is None
        or not (min_d <= s <= max_d)
        or not (min_d <= e <= max_d)
        or s > e
    )
    if invalid:
        st.session_state[DATE_RANGE_KEY] = (start_default, end_default)

date_range = st.sidebar.date_input(
    "Date range (Central Time)",
    value=(start_default, end_default),
    min_value=min_d,
    max_value=max_d,
    key=DATE_RANGE_KEY,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

if start_date > end_date:
    start_date, end_date = end_date, start_date

min_views = st.sidebar.number_input(
    "Min views", min_value=0, value=0, step=100, key=MIN_VIEWS_KEY
)
caption_search = st.sidebar.text_input(
    "Caption contains", value="", key=CAPTION_KEY
).strip()

top_n = st.sidebar.number_input("Top N posts", min_value=1, value=10, step=1)

st.sidebar.divider()
st.sidebar.subheader("Export")

if st.sidebar.button("Export report (Markdown)"):
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "latest.md"

    cmd = [
        "python",
        "-m",
        "src.main",
        "export",
        "--out",
        str(out_path),
        "--last-days",
        str((end_date - start_date).days + 1),
        "--top-n",
        str(int(top_n)),
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        st.sidebar.success(f"Wrote: {out_path}")
        if res.stdout.strip():
            st.sidebar.caption(res.stdout.strip())
    except subprocess.CalledProcessError as e:
        st.sidebar.error("Export failed. See details below.")
        st.sidebar.code((e.stdout or "") + "\n" + (e.stderr or ""))

filtered = df[df["created_at_local"].notna()].copy()
filtered = filtered[
    (filtered["created_at_local"].dt.date >= start_date)
    & (filtered["created_at_local"].dt.date <= end_date)
]
filtered = filtered[filtered["views"] >= int(min_views)]

if caption_search:
    filtered = filtered[
        filtered["caption"].fillna("").str.contains(caption_search, case=False, na=False)
    ]

if filtered.empty:
    st.warning("No posts match the current filters. Widen the date range or reduce min views.")
    st.stop()

# KPI summary
total_posts = len(filtered)
total_views = int(filtered["views"].sum())
total_eng = int(filtered["engagement"].sum())
avg_er = float(filtered["engagement_rate"].mean()) * 100.0
median_views = float(filtered["views"].median())

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
    st.subheader("Views over time (Central Time)")
    chart_df = filtered.copy()
    chart_df["day"] = chart_df["created_at_local"].dt.date
    by_day_views = chart_df.groupby("day", as_index=False)["views"].sum()
    st.line_chart(by_day_views, x="day", y="views")

with right:
    st.subheader("Engagement rate over time (avg per day, Central Time)")
    chart_df = filtered.copy()
    chart_df["day"] = chart_df["created_at_local"].dt.date
    by_day_er = chart_df.groupby("day", as_index=False)["engagement_rate"].mean()
    by_day_er["engagement_rate_pct"] = by_day_er["engagement_rate"] * 100.0
    st.line_chart(by_day_er, x="day", y="engagement_rate_pct")

st.divider()

# Table
st.subheader("Posts")
show = filtered.sort_values("views", ascending=False).copy()
show["created_at_central"] = show["created_at_local"].dt.strftime("%Y-%m-%d %H:%M")
show["engagement_rate_pct"] = (show["engagement_rate"] * 100.0).round(2)

show = show[
    [
        "post_id",
        "created_at_central",
        "views",
        "likes",
        "comments",
        "shares",
        "engagement",
        "engagement_rate_pct",
        "caption",
        "url",
    ]
]
st.dataframe(show, width="stretch", hide_index=True)

# Recommendations
st.subheader("Recommendations (simple heuristics)")
recs: list[str] = []

if avg_er < 2.0:
    recs.append(
        "Engagement rate is low. Tighten the first 1-2 seconds, reduce on-screen text, and make the payoff clearer."
    )
if median_views < 500:
    recs.append(
        "Median views are low. Run a 7-day posting experiment and test two posting times (morning vs evening)."
    )
if int(filtered["shares"].sum()) == 0:
    recs.append("Zero shares in this window. Try a direct prompt: 'Send this to someone who needs it.'")
if total_posts < 5:
    recs.append("Not enough posts in the filtered window to trust patterns. Get 5-10 posts before changing strategy.")

if recs:
    for r in recs:
        st.write(f"- {r}")
else:
    st.write("- Nothing obvious. Keep posting and iterate.")
