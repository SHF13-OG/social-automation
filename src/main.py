from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # If python-dotenv is not installed, .env won't be auto-loaded.
    pass

from dateutil import parser as dateparser  # type: ignore

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

DEFAULT_DB_PATH = "data/social.db"

POST_ID_KEYS = ["post_id", "id", "video_id", "item_id", "tiktok_id"]
CREATED_AT_KEYS = ["create_time", "created_at", "created", "posted_at", "date", "timestamp"]
VIEWS_KEYS = ["views", "view_count", "play_count", "video_views", "plays"]
LIKES_KEYS = ["likes", "like_count", "digg_count", "hearts"]
COMMENTS_KEYS = ["comments", "comment_count"]
SHARES_KEYS = ["shares", "share_count"]
FAVORITES_KEYS = ["favorites", "favorite_count"]
CAPTION_KEYS = ["caption", "description", "text"]
URL_KEYS = ["url", "share_url", "link"]


def get_db_path() -> str:
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


def connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tiktok_posts (
            post_id     TEXT PRIMARY KEY,
            created_at  TEXT,
            views       INTEGER,
            likes       INTEGER,
            comments    INTEGER,
            shares      INTEGER,
            favorites   INTEGER,
            caption     TEXT,
            url         TEXT,
            raw_json    TEXT,
            updated_at  TEXT
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tiktok_posts_created_at ON tiktok_posts(created_at);")
    conn.commit()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_")
        for c in df.columns
    ]
    return df


def pick_first(row: Dict[str, Any], keys: list[str]) -> Optional[Any]:
    for k in keys:
        if k in row and row[k] not in (None, "", "nan", "NaN"):
            return row[k]
    return None


def to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    s = s.replace(",", "")
    try:
        return int(float(s))
    except Exception:
        return None


def parse_datetime(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None

    if s.isdigit():
        try:
            n = int(s)
            if n > 10_000_000_000:
                dt = datetime.fromtimestamp(n / 1000, tz=timezone.utc)
            else:
                dt = datetime.fromtimestamp(n, tz=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass

    try:
        dt = dateparser.parse(s)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


def upsert_post(conn: sqlite3.Connection, post: Dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO tiktok_posts (
            post_id, created_at, views, likes, comments, shares, favorites,
            caption, url, raw_json, updated_at
        ) VALUES (
            :post_id, :created_at, :views, :likes, :comments, :shares, :favorites,
            :caption, :url, :raw_json, :updated_at
        )
        ON CONFLICT(post_id) DO UPDATE SET
            created_at = excluded.created_at,
            views      = excluded.views,
            likes      = excluded.likes,
            comments   = excluded.comments,
            shares     = excluded.shares,
            favorites  = excluded.favorites,
            caption    = excluded.caption,
            url        = excluded.url,
            raw_json   = excluded.raw_json,
            updated_at = excluded.updated_at
        ;
        """,
        {
            "post_id": post["post_id"],
            "created_at": post.get("created_at"),
            "views": post.get("views"),
            "likes": post.get("likes"),
            "comments": post.get("comments"),
            "shares": post.get("shares"),
            "favorites": post.get("favorites"),
            "caption": post.get("caption"),
            "url": post.get("url"),
            "raw_json": post.get("raw_json"),
            "updated_at": now,
        },
    )


def row_to_post(row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    post_id = pick_first(row, POST_ID_KEYS)
    if post_id is None:
        return None, "Missing post_id (expected one of: post_id, id, video_id, item_id)."

    created_raw = pick_first(row, CREATED_AT_KEYS)
    created_at = parse_datetime(created_raw)

    post = {
        "post_id": str(post_id).strip(),
        "created_at": created_at,
        "views": to_int(pick_first(row, VIEWS_KEYS)),
        "likes": to_int(pick_first(row, LIKES_KEYS)),
        "comments": to_int(pick_first(row, COMMENTS_KEYS)),
        "shares": to_int(pick_first(row, SHARES_KEYS)),
        "favorites": to_int(pick_first(row, FAVORITES_KEYS)),
        "caption": pick_first(row, CAPTION_KEYS),
        "url": pick_first(row, URL_KEYS),
        "raw_json": json.dumps(row, ensure_ascii=False),
    }
    return post, None


@app.command()
def doctor() -> None:
    """Sanity check: shows python path, DB path, and row count."""
    db_path = get_db_path()
    console.print(f"[bold]Python:[/bold] {os.sys.executable}")
    console.print(f"[bold]DB_PATH:[/bold] {db_path}")

    conn = connect(db_path)
    init_db(conn)

    try:
        cur = conn.execute("SELECT COUNT(*) FROM tiktok_posts;")
        count = cur.fetchone()[0]
        console.print(f"[bold]Rows in tiktok_posts:[/bold] {count}")
    finally:
        conn.close()


@app.command("import")
def import_csv(
    csv_path: str = typer.Argument(..., help="Path to TikTok export CSV, e.g. data/tiktok_posts.csv"),
) -> None:
    """Import TikTok posts CSV into SQLite with upsert on post_id."""
    db_path = get_db_path()
    conn = connect(db_path)
    init_db(conn)

    if not os.path.exists(csv_path):
        raise typer.BadParameter(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, keep_default_na=False)
    df = normalize_columns(df)

    imported = 0
    skipped = 0
    warnings = 0

    with conn:
        for _, r in df.iterrows():
            row = {k: r[k] for k in df.columns}
            post, err = row_to_post(row)
            if err:
                skipped += 1
                warnings += 1
                continue
            upsert_post(conn, post)
            imported += 1

    console.print(f"[bold]Imported/upserted:[/bold] {imported}")
    console.print(f"[bold]Skipped:[/bold] {skipped}")
    if warnings:
        console.print("[yellow]Note:[/yellow] Some rows were skipped, likely missing post_id. Fix your CSV export or column names.")


def load_posts(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql_query(
        """
        SELECT
            post_id, created_at, views, likes, comments, shares, favorites, caption, url
        FROM tiktok_posts
        """,
        conn,
    )
    if "created_at" in df.columns:
        df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    else:
        df["created_at_dt"] = pd.NaT
    for col in ["views", "likes", "comments", "shares", "favorites"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["engagement"] = df["likes"] + df["comments"] + df["shares"]
    df["engagement_rate"] = df.apply(lambda x: (x["engagement"] / x["views"]) if x["views"] > 0 else 0.0, axis=1)
    return df


def print_top_posts(df: pd.DataFrame, title: str, n: int = 5) -> None:
    table = Table(title=title)
    table.add_column("post_id", overflow="fold")
    table.add_column("created_at", overflow="fold")
    table.add_column("views", justify="right")
    table.add_column("eng", justify="right")
    table.add_column("eng_rate", justify="right")
    table.add_column("caption", overflow="fold")

    show = df.sort_values("views", ascending=False).head(n)
    for _, r in show.iterrows():
        caption = str(r.get("caption") or "")[:60]
        table.add_row(
            str(r["post_id"]),
            str(r.get("created_at") or ""),
            str(int(r.get("views", 0))),
            str(int(r.get("engagement", 0))),
            f"{float(r.get('engagement_rate', 0.0))*100:.2f}%",
            caption,
        )
    console.print(table)


@app.command()
def report(
    last_days: int = typer.Option(7, help="Report window size in days"),
    top_n: int = typer.Option(5, help="How many top posts to show"),
) -> None:
    """Generate a simple performance report from SQLite."""
    db_path = get_db_path()
    conn = connect(db_path)
    init_db(conn)

    try:
        df = load_posts(conn)
    finally:
        conn.close()

    total_posts = len(df)
    console.print(f"[bold]Total posts in DB:[/bold] {total_posts}")

def _markdown_escape(s: str) -> str:
    return s.replace("|", r"\|").replace("\n", " ").strip()


def _df_to_markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_No rows to display._\n"

    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for _, r in df.iterrows():
        vals = []
        for c in columns:
            v = r.get(c, "")
            if pd.isna(v):
                v = ""
            if isinstance(v, float):
                vals.append(f"{v:.4f}" if c == "engagement_rate" else f"{v:.2f}")
            else:
                vals.append(_markdown_escape(str(v)))
        rows.append("| " + " | ".join(vals) + " |")

    return "\n".join([header, sep] + rows) + "\n"


@app.command()
def export(
    out: str = typer.Option(..., "--out", help="Output markdown path, e.g. reports/latest.md"),
    last_days: int = typer.Option(7, help="Report window size in days"),
    top_n: int = typer.Option(5, help="How many top posts to include"),
) -> None:
    """Export the performance report to a markdown file."""
    db_path = get_db_path()
    conn = connect(db_path)
    init_db(conn)

    try:
        df = load_posts(conn)
    finally:
        conn.close()

    total_posts = len(df)
    now = datetime.now(timezone.utc)

    if total_posts == 0:
        md = "\n".join(
            [
                "# TikTok Report",
                f"Generated: {now.isoformat()}",
                f"DB_PATH: `{db_path}`",
                "",
                "No data yet. Import your CSV first:",
                "",
                "```bash",
                "python -m src.main import data/tiktok_posts.csv",
                "```",
                "",
            ]
        )
    else:
        cutoff = now - timedelta(days=last_days)
        recent = df[df["created_at_dt"].notna() & (df["created_at_dt"] >= cutoff)].copy()

        def summarize(frame: pd.DataFrame) -> dict[str, float]:
            if frame.empty:
                return {
                    "posts": 0,
                    "total_views": 0,
                    "total_engagement": 0,
                    "avg_views": 0,
                    "median_views": 0,
                    "avg_engagement_rate": 0,
                }
            return {
                "posts": float(len(frame)),
                "total_views": float(frame["views"].sum()),
                "total_engagement": float(frame["engagement"].sum()),
                "avg_views": float(frame["views"].mean()),
                "median_views": float(frame["views"].median()),
                "avg_engagement_rate": float(frame["engagement_rate"].mean()) * 100.0,
            }

        s_all = summarize(df)
        s_recent = summarize(recent)

        def top_posts(frame: pd.DataFrame) -> pd.DataFrame:
            if frame.empty:
                return frame
            out_df = frame.sort_values("views", ascending=False).head(top_n).copy()
            out_df["engagement_rate"] = out_df["engagement_rate"].apply(lambda x: x * 100.0)
            out_df["caption"] = out_df["caption"].fillna("").astype(str).str.slice(0, 80)
            return out_df[
                ["post_id", "created_at", "views", "engagement", "engagement_rate", "caption", "url"]
            ]

        top_df = top_posts(recent if len(recent) else df)

        md_lines = [
            "# TikTok Report",
            f"Generated: {now.isoformat()}",
            f"DB_PATH: `{db_path}`",
            "",
            "## Summary",
            f"- Total posts in DB: {total_posts}",
            "",
            "### All time",
            f"- Posts: {int(s_all['posts'])}",
            f"- Total views: {int(s_all['total_views'])}",
            f"- Total engagement: {int(s_all['total_engagement'])}",
            f"- Avg views: {s_all['avg_views']:.1f}",
            f"- Median views: {s_all['median_views']:.1f}",
            f"- Avg engagement rate: {s_all['avg_engagement_rate']:.2f}%",
            "",
            f"### Last {last_days} days",
            f"- Posts: {int(s_recent['posts'])}",
            f"- Total views: {int(s_recent['total_views'])}",
            f"- Total engagement: {int(s_recent['total_engagement'])}",
            f"- Avg views: {s_recent['avg_views']:.1f}",
            f"- Median views: {s_recent['median_views']:.1f}",
            f"- Avg engagement rate: {s_recent['avg_engagement_rate']:.2f}%",
            "",
            "## Top posts by views",
            _df_to_markdown_table(
                top_df,
                ["post_id", "created_at", "views", "engagement", "engagement_rate", "caption", "url"],
            ),
        ]

        md = "\n".join(md_lines)

    out_path = os.path.abspath(out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    console.print(f"[bold]Wrote report:[/bold] {out_path}")


    if total_posts == 0:
        console.print("[yellow]No data yet.[/yellow] Import your CSV first.")
        console.print("Example: python -m src.main import data/tiktok_posts.csv")
        raise typer.Exit(code=0)

    cutoff = datetime.now(timezone.utc) - timedelta(days=last_days)
    recent = df[df["created_at_dt"].notna() & (df["created_at_dt"] >= cutoff)]

    console.print(f"[bold]Posts in last {last_days} days:[/bold] {len(recent)}")

    def summary_block(frame: pd.DataFrame, label: str) -> None:
        if len(frame) == 0:
            console.print(f"[yellow]{label}:[/yellow] No parsable created_at dates found in this window.")
            return
        total_views = int(frame["views"].sum())
        total_eng = int(frame["engagement"].sum())
        avg_views = float(frame["views"].mean())
        med_views = float(frame["views"].median())
        avg_er = float(frame["engagement_rate"].mean()) * 100.0

        table = Table(title=f"{label} summary")
        table.add_column("metric")
        table.add_column("value", justify="right")
        table.add_row("total_views", str(total_views))
        table.add_row("total_engagement", str(total_eng))
        table.add_row("avg_views", f"{avg_views:.1f}")
        table.add_row("median_views", f"{med_views:.1f}")
        table.add_row("avg_engagement_rate", f"{avg_er:.2f}%")
        console.print(table)

        recs = []
        if avg_er < 2.0:
            recs.append("Engagement rate is low. Try stronger first 1-2 seconds, fewer words on screen, and a clearer payoff.")
        if med_views < 500:
            recs.append("Median views are low. Post more frequently for 7 days and test 2 posting times (morning vs evening).")
        if frame["shares"].sum() == 0:
            recs.append("No shares recorded. Add a prompt like 'Send this to someone who needs it' on a few posts.")
        if len(frame) < 3:
            recs.append("Not enough recent samples to trust patterns yet. Get 5-10 posts in before making big changes.")

        if recs:
            console.print("[bold]Recommendations:[/bold]")
            for r in recs[:4]:
                console.print(f"- {r}")

    summary_block(recent, f"Last {last_days} days")
    print_top_posts(recent if len(recent) else df, "Top posts (by views)", n=top_n)


# ---------------------------------------------------------------------------
# Phase 1 commands: foundation for AI voice content pipeline
# ---------------------------------------------------------------------------

@app.command("init-db")
def init_db_cmd() -> None:
    """Initialize / migrate the full database schema (all tables)."""
    from src.db import connect as db_connect, init_schema

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)
    conn.close()
    console.print(f"[bold]Schema initialized:[/bold] {db_path}")


@app.command("config-show")
def config_show() -> None:
    """Display current configuration (YAML defaults + DB overrides)."""
    from src.config import load_config, flatten_config

    config = load_config()
    table = Table(title="Current Configuration")
    table.add_column("key", overflow="fold")
    table.add_column("value", overflow="fold")

    for key, value in flatten_config(config):
        table.add_row(str(key), str(value))

    console.print(table)


@app.command("list-themes")
def list_themes() -> None:
    """List all available content themes from the database."""
    from src.db import connect as db_connect, init_schema

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    cur = conn.execute(
        "SELECT slug, name, tone, is_active FROM themes ORDER BY slug"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        console.print(
            "[yellow]No themes in database.[/yellow] "
            "Run: python -m src.main init-themes"
        )
        return

    table = Table(title="Content Themes")
    table.add_column("slug")
    table.add_column("name")
    table.add_column("tone")
    table.add_column("active", justify="center")

    for row in rows:
        active = "Y" if row["is_active"] else "-"
        table.add_row(row["slug"], row["name"], row["tone"] or "", active)

    console.print(table)


@app.command("init-themes")
def init_themes_cmd(
    yaml_path: str = typer.Argument(
        "config/themes.yaml", help="Path to themes YAML file"
    ),
) -> None:
    """Load themes from YAML into the database (upsert on slug)."""
    import yaml as _yaml

    from src.db import connect as db_connect, init_schema, now_utc

    if not os.path.exists(yaml_path):
        raise typer.BadParameter(f"File not found: {yaml_path}")

    with open(yaml_path) as f:
        data = _yaml.safe_load(f)

    themes = data.get("themes", [])
    if not themes:
        console.print("[yellow]No themes found in YAML.[/yellow]")
        return

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    imported = 0
    now = now_utc()
    with conn:
        for t in themes:
            conn.execute(
                """
                INSERT INTO themes (slug, name, description, keywords, tone, is_active, created_at, updated_at)
                VALUES (:slug, :name, :description, :keywords, :tone, :is_active, :created_at, :updated_at)
                ON CONFLICT(slug) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    keywords = excluded.keywords,
                    tone = excluded.tone,
                    is_active = excluded.is_active,
                    updated_at = excluded.updated_at
                """,
                {
                    "slug": t["slug"],
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "keywords": json.dumps(t.get("keywords", [])),
                    "tone": t.get("tone", ""),
                    "is_active": 1 if t.get("is_active", True) else 0,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            imported += 1

    conn.close()
    console.print(f"[bold]Themes upserted:[/bold] {imported}")


@app.command("import-verses")
def import_verses_cmd(
    yaml_path: str = typer.Argument(
        "config/verses.yaml", help="Path to verses YAML file"
    ),
) -> None:
    """Import Bible verses from YAML into the database."""
    import yaml as _yaml

    from src.db import connect as db_connect, init_schema, now_utc

    if not os.path.exists(yaml_path):
        raise typer.BadParameter(f"File not found: {yaml_path}")

    with open(yaml_path) as f:
        data = _yaml.safe_load(f)

    verses = data.get("verses", [])
    if not verses:
        console.print("[yellow]No verses found in YAML.[/yellow]")
        return

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    # Build slug -> id mapping for themes
    cur = conn.execute("SELECT id, slug FROM themes")
    theme_map = {row["slug"]: row["id"] for row in cur.fetchall()}

    imported = 0
    skipped = 0
    now = now_utc()

    with conn:
        for v in verses:
            theme_slug = v.get("theme", "")
            theme_id = theme_map.get(theme_slug)
            if theme_id is None:
                console.print(
                    f"[yellow]Skipping verse {v['reference']}: "
                    f"theme '{theme_slug}' not in DB.[/yellow]"
                )
                skipped += 1
                continue

            # Check if verse already exists (by reference + theme)
            existing = conn.execute(
                "SELECT id FROM bible_verses WHERE reference = ? AND theme_id = ?",
                (v["reference"], theme_id),
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE bible_verses
                    SET text = ?, translation = ?, tone = ?
                    WHERE id = ?
                    """,
                    (v["text"], v.get("translation", "ESV"), v.get("tone", ""), existing["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO bible_verses (reference, text, translation, theme_id, tone, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        v["reference"],
                        v["text"],
                        v.get("translation", "ESV"),
                        theme_id,
                        v.get("tone", ""),
                        now,
                    ),
                )
            imported += 1

    conn.close()
    console.print(f"[bold]Verses imported/updated:[/bold] {imported}")
    if skipped:
        console.print(f"[yellow]Skipped:[/yellow] {skipped} (missing theme)")


# ---------------------------------------------------------------------------
# Phase 2 commands: content generation
# ---------------------------------------------------------------------------

@app.command("generate")
def generate_cmd(
    theme: str = typer.Option(
        None, "--theme", "-t", help="Theme slug (e.g. grief). Auto-picks if omitted."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview only; don't save to database."
    ),
    model: str = typer.Option(
        "gpt-4o-mini", "--model", help="OpenAI model to use for prayer generation."
    ),
) -> None:
    """Generate content: pick theme + verse, generate prayer text."""
    from src.content.prayers import (
        generate_prayer_text,
        generate_prayer_text_fallback,
        save_prayer,
    )
    from src.content.themes import pick_theme
    from src.content.verses import mark_verse_used, pick_verse
    from src.db import connect as db_connect, init_schema

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    # 1. Pick theme
    chosen_theme = pick_theme(conn, slug=theme)
    if chosen_theme is None:
        conn.close()
        if theme:
            console.print(f"[red]Theme '{theme}' not found or inactive.[/red]")
        else:
            console.print("[red]No active themes available.[/red]")
        raise typer.Exit(code=1)

    console.print(
        f"[bold]Theme:[/bold] {chosen_theme['name']} ({chosen_theme['slug']})"
    )

    # 2. Pick verse
    verse = pick_verse(conn, chosen_theme["id"])
    if verse is None:
        conn.close()
        console.print(
            f"[red]No verses found for theme '{chosen_theme['slug']}'.[/red] "
            "Run: python -m src.main import-verses"
        )
        raise typer.Exit(code=1)

    console.print(f"[bold]Verse:[/bold] {verse['reference']}")
    console.print(f"  {verse['text']}")

    # 3. Generate prayer
    console.print("\n[bold]Generating prayer...[/bold]")
    ai_model_used: str | None = None
    try:
        prayer_text = generate_prayer_text(verse, chosen_theme, model=model)
        ai_model_used = model
        console.print(f"  (via OpenAI {model})")
    except RuntimeError as exc:
        console.print(f"  [yellow]{exc}[/yellow]")
        console.print("  Using template fallback.")
        prayer_text = generate_prayer_text_fallback(verse, chosen_theme)
        ai_model_used = "fallback-template"

    word_count = len(prayer_text.split())
    console.print(f"\n[bold]Prayer ({word_count} words):[/bold]")
    console.print(prayer_text)

    # 4. Save unless dry-run
    if dry_run:
        console.print("\n[yellow]--dry-run: nothing saved.[/yellow]")
    else:
        prayer_id = save_prayer(
            conn, verse["id"], chosen_theme["id"], prayer_text, ai_model_used
        )
        mark_verse_used(conn, verse["id"])
        console.print(f"\n[bold]Saved:[/bold] prayer_id={prayer_id}")

    conn.close()


# ---------------------------------------------------------------------------
# Phase 3 commands: media pipeline
# ---------------------------------------------------------------------------

@app.command("compose")
def compose_cmd(
    prayer_id: int = typer.Argument(..., help="ID of the prayer to compose into a video."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview steps without generating media files."
    ),
) -> None:
    """Generate audio, fetch footage, and compose a TikTok video for a prayer."""
    from src.db import connect as db_connect, init_schema

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    # 1. Load prayer + verse + theme
    prayer_row = conn.execute(
        "SELECT * FROM prayers WHERE id = ?", (prayer_id,)
    ).fetchone()
    if not prayer_row:
        conn.close()
        console.print(f"[red]Prayer id={prayer_id} not found.[/red]")
        raise typer.Exit(code=1)

    verse_row = conn.execute(
        "SELECT * FROM bible_verses WHERE id = ?", (prayer_row["verse_id"],)
    ).fetchone()
    theme_row = conn.execute(
        "SELECT * FROM themes WHERE id = ?", (prayer_row["theme_id"],)
    ).fetchone()

    console.print(f"[bold]Prayer:[/bold] id={prayer_id} ({prayer_row['word_count']} words)")
    console.print(f"[bold]Verse:[/bold] {verse_row['reference']}")
    console.print(f"[bold]Theme:[/bold] {theme_row['name']}")

    if dry_run:
        console.print("\n[bold]Steps that would run:[/bold]")
        console.print("  1. Generate audio via ElevenLabs TTS")
        console.print("  2. Search & download stock footage")
        console.print("  3. Compose video with FFmpeg")
        console.print("\n[yellow]--dry-run: no media generated.[/yellow]")
        conn.close()
        return

    # 2. Generate audio
    console.print("\n[bold]Step 1:[/bold] Generating audio...")
    from src.media.tts import generate_audio, save_audio_record

    try:
        audio_info = generate_audio(prayer_id, prayer_row["prayer_text"], db_path)
        audio_id = save_audio_record(conn, prayer_id, audio_info)
        console.print(f"  Audio saved: {audio_info['file_path']}")
    except RuntimeError as exc:
        conn.close()
        console.print(f"  [red]{exc}[/red]")
        raise typer.Exit(code=1)

    # 3. Fetch stock footage
    console.print("\n[bold]Step 2:[/bold] Searching for stock footage...")
    from src.media.footage import (
        download_clip,
        save_footage_record,
        search_footage,
    )

    keywords = json.loads(theme_row["keywords"]) if theme_row["keywords"] else []
    if not keywords:
        keywords = [theme_row["name"]]

    try:
        clips = search_footage(keywords, db_path, max_results=2)
    except RuntimeError as exc:
        conn.close()
        console.print(f"  [red]{exc}[/red]")
        raise typer.Exit(code=1)

    if not clips:
        conn.close()
        console.print("  [red]No footage found. Check API keys.[/red]")
        raise typer.Exit(code=1)

    footage_paths: list[str] = []
    footage_ids: list[int] = []
    for clip in clips:
        dl_path = download_clip(clip, theme_row["slug"])
        fid = save_footage_record(
            conn, clip, str(dl_path), theme_row["id"], keywords
        )
        footage_paths.append(str(dl_path))
        footage_ids.append(fid)
        console.print(f"  Downloaded: {dl_path.name}")

    # 4. Compose video
    console.print("\n[bold]Step 3:[/bold] Composing video with FFmpeg...")
    from src.media.compositor import compose_video, save_video_record

    try:
        video_info = compose_video(
            audio_path=audio_info["file_path"],
            footage_paths=footage_paths,
            verse_ref=verse_row["reference"],
            verse_text=verse_row["text"],
            prayer_id=prayer_id,
            db_path=db_path,
        )
        video_id = save_video_record(
            conn, prayer_id, audio_id, footage_ids, video_info, db_path
        )
        console.print(f"  Video: {video_info['file_path']}")
        console.print(f"  Duration: {video_info['duration_sec']:.1f}s")
        console.print(
            f"  Size: {video_info['file_size_bytes'] / 1024 / 1024:.1f} MB"
        )
        console.print(f"\n[bold]Done![/bold] video_id={video_id}")
    except RuntimeError as exc:
        conn.close()
        console.print(f"  [red]{exc}[/red]")
        raise typer.Exit(code=1)

    conn.close()


# ---------------------------------------------------------------------------
# Phase 4 commands: publishing
# ---------------------------------------------------------------------------

@app.command("schedule")
def schedule_cmd(
    video_id: int = typer.Argument(..., help="ID of the generated video."),
    at: str = typer.Argument(
        ..., help="Scheduled datetime (ISO 8601, e.g. 2025-02-10T07:00:00)."
    ),
    platform: str = typer.Option("tiktok", help="Target platform."),
) -> None:
    """Add a video to the publish queue at a given time."""
    from src.db import connect as db_connect, init_schema
    from src.publishing.scheduler import add_to_queue, needs_human_approval

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    # Verify video exists
    video = conn.execute(
        "SELECT id, file_path FROM generated_videos WHERE id = ?", (video_id,)
    ).fetchone()
    if not video:
        conn.close()
        console.print(f"[red]Video id={video_id} not found.[/red]")
        raise typer.Exit(code=1)

    queue_id = add_to_queue(conn, video_id, at, platform)
    console.print(f"[bold]Scheduled:[/bold] queue_id={queue_id}")
    console.print(f"  Video: {video['file_path']}")
    console.print(f"  Time: {at}")
    console.print(f"  Platform: {platform}")

    if needs_human_approval(conn):
        console.print(
            "\n[yellow]Note:[/yellow] This post requires human approval. "
            "Run: python -m src.main approve " + str(queue_id)
        )

    conn.close()


@app.command("approve")
def approve_cmd(
    queue_id: int = typer.Argument(..., help="Queue item ID to approve."),
) -> None:
    """Approve a pending queue item for publishing."""
    from src.db import connect as db_connect, init_schema
    from src.publishing.scheduler import approve_item

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    if approve_item(conn, queue_id):
        console.print(f"[bold]Approved:[/bold] queue_id={queue_id}")
    else:
        console.print(
            f"[yellow]queue_id={queue_id} not found or not in 'pending' status.[/yellow]"
        )

    conn.close()


@app.command("publish")
def publish_cmd(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview what would be published."
    ),
) -> None:
    """Process the publish queue: upload due items to TikTok."""
    from src.db import connect as db_connect, init_schema
    from src.publishing.scheduler import process_queue

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    results = process_queue(conn, db_path, dry_run=dry_run)

    for r in results:
        qid = r.get("queue_id", "-")
        status = r["status"]
        if status == "blocked":
            console.print(f"[red]Blocked:[/red] {r['reason']}")
        elif status == "empty":
            console.print("[yellow]No due items in queue.[/yellow]")
        elif status == "dry_run":
            console.print(
                f"  [dim]queue_id={qid}[/dim] would publish "
                f"{r.get('video_path', '?')} ({r.get('verse_ref', '')})"
            )
        elif status == "published":
            console.print(
                f"  [green]Published[/green] queue_id={qid} "
                f"(publish_id={r.get('publish_id', '?')})"
            )
        elif status == "failed":
            console.print(
                f"  [red]Failed[/red] queue_id={qid}: {r.get('reason', '?')}"
            )
        elif status == "skipped":
            console.print(
                f"  [yellow]Skipped[/yellow] queue_id={qid}: {r.get('reason', '?')}"
            )

    conn.close()


@app.command("list-queue")
def list_queue_cmd(
    status: str = typer.Option(
        None, "--status", "-s", help="Filter by status (pending, approved, published, failed)."
    ),
    limit: int = typer.Option(20, "--limit", "-n", help="Max rows to show."),
) -> None:
    """Show the publish queue."""
    from src.db import connect as db_connect, init_schema
    from src.publishing.scheduler import get_queue

    db_path = get_db_path()
    conn = db_connect(db_path)
    init_schema(conn)

    items = get_queue(conn, status=status, limit=limit)
    conn.close()

    if not items:
        console.print("[yellow]Queue is empty.[/yellow]")
        return

    table = Table(title="Publish Queue")
    table.add_column("id", justify="right")
    table.add_column("video_id", justify="right")
    table.add_column("platform")
    table.add_column("scheduled_at")
    table.add_column("status")
    table.add_column("published_at")
    table.add_column("error")

    for item in items:
        error = (item.get("error_message") or "")[:40]
        table.add_row(
            str(item["id"]),
            str(item["video_id"]),
            item.get("platform", ""),
            item.get("scheduled_at", ""),
            item.get("status", ""),
            item.get("published_at", "") or "",
            error,
        )

    console.print(table)


if __name__ == "__main__":
    app()
