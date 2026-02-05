# Social Automation

Faith-based TikTok content automation for 45+ Christians. Generates daily prayer videos with Bible verses, AI voiceovers, and stock footage backgrounds.

## Features

- **Content Generation** - Theme-based Bible verse selection with LLM prayer generation (OpenAI) and template fallback
- **Media Pipeline** - ElevenLabs TTS, Pexels/Pixabay stock footage, FFmpeg video compositing (1080x1920 vertical)
- **Publishing** - TikTok Content Posting API with scheduling queue and safety limits
- **Dashboard** - Streamlit multipage app: analytics, content pipeline, publish queue, configuration, CI status
- **CLI** - 14 Typer commands for every operation
- **Safety** - Human approval for first 10 posts, 4h min interval, 3-failure auto-pause, no prosperity gospel language

## Quick Start

```bash
# Clone and set up
git clone https://github.com/SHF13-OG/social-automation.git
cd social-automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python -m src.main init-db
python -m src.main init-themes
python -m src.main import-verses

# Generate content
python -m src.main generate --theme grief --dry-run
python -m src.main generate --theme grief

# Compose video (requires ElevenLabs + Pexels keys + FFmpeg)
python -m src.main compose <prayer_id> --dry-run

# Schedule and publish
python -m src.main schedule <video_id> "2025-03-01T07:00:00"
python -m src.main approve <queue_id>
python -m src.main publish --dry-run

# Run dashboard
streamlit run src/dashboard.py --server.headless true
```

## CLI Commands

| Command | Description |
|---|---|
| `doctor` | Sanity check: Python path, DB path, row count |
| `import <csv>` | Import TikTok posts CSV into SQLite |
| `report` | Generate performance report in terminal |
| `export --out <path>` | Export report to markdown |
| `init-db` | Initialize full database schema |
| `config-show` | Display merged configuration |
| `list-themes` | List content themes |
| `init-themes` | Load themes from YAML |
| `import-verses` | Load Bible verses from YAML |
| `generate` | Pick theme + verse, generate prayer text |
| `compose <prayer_id>` | Generate audio + footage + video |
| `schedule <video_id> <datetime>` | Add to publish queue |
| `approve <queue_id>` | Approve a pending post |
| `publish` | Process due queue items |
| `list-queue` | Show publish queue |

## Project Structure

```
src/
  main.py              # CLI (14 commands)
  db.py                # SQLite utilities, schema (10 tables)
  config.py            # YAML defaults + DB overrides
  dashboard.py         # Streamlit analytics homepage
  content/
    themes.py          # Theme rotation (least-recently-used)
    verses.py          # Verse selection (avoid repeats)
    prayers.py         # LLM prayer generation + fallback
  media/
    tts.py             # ElevenLabs text-to-speech
    footage.py         # Pexels/Pixabay search & download
    compositor.py      # FFmpeg video assembly
  publishing/
    tiktok.py          # TikTok Content Posting API
    scheduler.py       # Queue processing + safety checks
pages/
  2_Content_Pipeline.py  # Prayer browser, theme coverage
  3_Publish_Queue.py     # Queue management, approvals
  4_Configuration.py     # Settings UI, overrides
  5_CI_Status.py         # Test run history
config/
  default.yaml         # All configurable settings
  themes.yaml          # 8 content themes
  verses.yaml          # 40 Bible verses (ESV)
tests/                 # 107 tests
```

## Configuration

Settings are managed in two layers:

1. **YAML defaults** (`config/default.yaml`) - voice speed, video resolution, font settings, publishing rules
2. **DB overrides** (`config_overrides` table) - set via dashboard UI or CLI, take precedence over YAML

API keys go in `.env` (never committed):

```bash
DB_PATH=data/social.db
ELEVENLABS_API_KEY=
PEXELS_API_KEY=
PIXABAY_API_KEY=
OPENAI_API_KEY=
TIKTOK_ACCESS_TOKEN=
TIKTOK_REFRESH_TOKEN=
```

## Content Themes

8 themes targeting second-half-of-life challenges:

| Theme | Tone | Description |
|---|---|---|
| grief | comforting | Comfort for those mourning loved ones |
| retirement | encouraging | Finding purpose beyond career |
| health | hopeful | Strength through physical trials |
| faith-doubts | reassuring | Navigating spiritual uncertainty |
| adult-children | peaceful | Letting go, trusting God with your kids |
| marriage-renewal | loving | Rekindling love after 25+ years |
| legacy | inspiring | Making an impact that outlasts your years |
| grandparenting | joyful | Joy and responsibility of grandchildren |

## Safety Rules

See [CLAUDE.md](CLAUDE.md) for the complete safety ruleset. Key limits:

- First 10 posts require human approval
- Max 1 post per 4 hours
- Auto-pause after 3 consecutive failures
- No prosperity gospel language
- All posts start as private (SELF_ONLY)
- Bible verse accuracy verification required

## Development

```bash
# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/ pages/

# All commands
python -m src.main --help
```

## Tech Stack

- **Python 3.12+** with type hints
- **Typer** - CLI framework
- **Streamlit** - dashboard
- **SQLite** - database (WAL mode, foreign keys)
- **ElevenLabs** - text-to-speech
- **OpenAI** - prayer generation
- **Pexels/Pixabay** - stock footage
- **FFmpeg** - video compositing
- **Ruff** - linting
- **Pytest** - testing (107 tests)
- **GitHub Actions** - CI (lint + test on push/PR/daily)
