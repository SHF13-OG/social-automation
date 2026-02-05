"""CI Status dashboard page - display test run results and build health."""

from __future__ import annotations

import os
import sqlite3

import pandas as pd
import streamlit as st

DEFAULT_DB_PATH = "data/social.db"


def get_db_path() -> str:
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


def load_test_runs(db_path: str) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT
                id, run_id, status, tests_passed, tests_failed,
                tests_skipped, duration_sec, commit_sha, branch,
                started_at, completed_at
            FROM test_runs
            ORDER BY completed_at DESC
            LIMIT 50
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def get_latest_run(db_path: str) -> dict | None:
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM test_runs ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
    except Exception:
        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="CI Status", layout="wide")
st.title("CI / Test Status")
st.caption("View test run history and build health from the test_runs table.")

db_path = get_db_path()

# Latest run summary
latest = get_latest_run(db_path)

if latest is None:
    st.info(
        "No test runs recorded yet. CI results are stored in the `test_runs` table.\n\n"
        "To record a run manually:\n"
        "```sql\n"
        "INSERT INTO test_runs (run_id, status, tests_passed, tests_failed,\n"
        "  tests_skipped, duration_sec, commit_sha, branch, started_at, completed_at)\n"
        "VALUES ('run_001', 'passed', 107, 0, 0, 0.6, 'abc123',\n"
        "  'experiment/aivoice-automation', datetime('now'), datetime('now'));\n"
        "```"
    )
else:
    st.subheader("Latest Run")

    status = latest.get("status", "unknown")
    if status == "passed":
        st.success(f"Latest run: **PASSED** ({latest.get('run_id', '?')})")
    elif status == "failed":
        st.error(f"Latest run: **FAILED** ({latest.get('run_id', '?')})")
    else:
        st.warning(f"Latest run: **{status.upper()}** ({latest.get('run_id', '?')})")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Passed", latest.get("tests_passed", 0))
    col2.metric("Failed", latest.get("tests_failed", 0))
    col3.metric("Skipped", latest.get("tests_skipped", 0))
    col4.metric("Duration", f"{latest.get('duration_sec', 0):.1f}s")

    st.text(f"Branch: {latest.get('branch', '?')}")
    st.text(f"Commit: {latest.get('commit_sha', '?')}")
    st.text(f"Completed: {latest.get('completed_at', '?')}")

st.divider()

# Run history
st.subheader("Run History")
runs_df = load_test_runs(db_path)

if runs_df.empty:
    st.info("No test run history available.")
else:
    # Pass/fail chart
    if "completed_at" in runs_df.columns and "tests_passed" in runs_df.columns:
        chart_df = runs_df.copy()
        chart_df["completed_at"] = pd.to_datetime(chart_df["completed_at"], errors="coerce")
        chart_df = chart_df.dropna(subset=["completed_at"])

        if not chart_df.empty:
            st.line_chart(
                chart_df.set_index("completed_at")[["tests_passed", "tests_failed"]],
            )

    # Table
    display_cols = [
        "run_id", "status", "tests_passed", "tests_failed",
        "tests_skipped", "duration_sec", "branch", "commit_sha", "completed_at",
    ]
    available = [c for c in display_cols if c in runs_df.columns]
    st.dataframe(runs_df[available], hide_index=True, width="stretch")

st.divider()

# Quick test runner info
st.subheader("Run Tests Locally")
st.code("python -m pytest tests/ -v", language="bash")
st.caption(
    "Test results can be recorded to the database via CI pipeline or manually. "
    "The GitHub Actions workflow in `.github/workflows/ci.yml` runs tests on every push."
)
