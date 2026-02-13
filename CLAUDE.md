# CLAUDE.md - AI Assistant Rules for Social Media Automation

## Project Overview

This project automates faith-based TikTok content creation for an audience of 45+ Christians
navigating the second half of life. Content includes daily prayer videos with Bible verses,
AI voiceovers, and stock footage backgrounds.

**Publishing Model:** Videos are generated automatically, then manually uploaded to TikTok
via TikTok Studio. The TikTok Content Posting API code is preserved but disabled pending
approval for production use (see `src/publishing/tiktok.py`).

## Development Commands

```bash
# Activate environment
source .venv/bin/activate

# Run tests
pytest -q

# Lint
ruff check src/ tests/

# Run CLI
python -m src.main --help
python -m src.main doctor

# Generate daily content
python -m src.main generate-daily

# Run dashboard
streamlit run src/dashboard.py --server.port 8501 --server.headless true
```

## Daily Workflow

### Automated (runs via cron or manually)
```bash
python -m src.main generate-daily
```
This creates:
- Prayer text (AI-generated)
- Audio voiceover (ElevenLabs)
- Composited video (FFmpeg)
- Output: `media/YYYY-MM-DD_prayer.mp4`

### Manual (2-5 minutes daily)
1. Open TikTok Studio: https://www.tiktok.com/tiktokstudio
2. Click "Upload" → drag video from `media/` folder
3. Add caption (verse reference + hashtags)
4. Schedule or post immediately

## Architecture

- **CLI**: Typer (`src/main.py`) - data import, report generation, content pipeline
- **Dashboard**: Streamlit (`src/dashboard.py`) - analytics, config UI, publishing queue
- **Database**: SQLite (`data/social.db`) - posts, themes, verses, generated content
- **Config**: YAML defaults (`config/`) + DB overrides (`config_overrides` table)
- **Website**: Next.js (`website/`) - public prayer display + admin dashboard

### Content Pipeline
```
Theme Selection → Verse Selection → Prayer Generation (AI)
                                          ↓
                                    Audio (ElevenLabs)
                                          ↓
                                    Stock Footage (Pexels)
                                          ↓
                                    Video Compositing (FFmpeg)
                                          ↓
                                    Output: media/YYYY-MM-DD_prayer.mp4
                                          ↓
                                    [Manual] Upload to TikTok Studio
```

### TikTok API Integration (Currently Disabled)

The TikTok Content Posting API integration is fully implemented but disabled:
- **Why disabled:** TikTok rejected our sandbox submission because their API
  does not support personal/internal company use (managing your own account).
- **Code location:** `src/publishing/tiktok.py` (commented out, well-documented)
- **To re-enable:** If approved for production API access in the future, uncomment
  the code and set `TIKTOK_ACCESS_TOKEN` in `.env`.

## CRITICAL SAFETY RULES

### API Key Security
- NEVER commit API keys, tokens, or credentials to version control
- ALWAYS use environment variables via `.env` (which is in `.gitignore`)
- NEVER log API keys or credentials in output, errors, or debug messages
- NEVER hardcode keys in source files, even temporarily
- Rotate keys immediately if exposed in any commit

### Content Publishing
- NEVER publish content without human review first
- ALWAYS preview generated videos before uploading to TikTok
- NEVER post more than 1 video per day unless explicitly decided
- ALWAYS include stock footage attribution per license requirements

### Content Guidelines
- NEVER generate content that promises physical healing or financial prosperity
- NEVER use "name it and claim it" or prosperity gospel language
- NEVER use manipulative, fear-based, or guilt-based language
- ALWAYS verify Bible verse text accuracy against the specified translation (ESV)
- ALWAYS maintain a reverent, respectful, and conversational tone
- ALWAYS keep prayers personal and relatable ("Father, I come to you...")
- Target prayer duration: 62-70 seconds (approximately 150 words at 140 WPM)
- Focus on comfort, hope, encouragement, and authentic faith

### Data Protection
- NEVER store personally identifiable information from viewers
- NEVER share audience analytics data with third parties
- Keep engagement data for analytics purposes only

## AUTOMATION BOUNDARIES

### Fully Automated
- Prayer text generation (AI)
- Audio voiceover generation (ElevenLabs TTS)
- Stock footage search and download (Pexels/Pixabay)
- Video compositing (FFmpeg)
- Daily content pipeline execution
- Test runs and CI status reporting

### Requires Human Action
- Uploading videos to TikTok (via TikTok Studio)
- Reviewing generated content before posting
- Responding to comments or messages
- Changing posting frequency
- Modifying content themes or Bible verse database
- Any interaction with followers

### Prohibited Actions
- Direct messaging followers
- Purchasing followers, likes, or engagement
- Cross-posting to platforms not explicitly configured
- Generating content outside the defined faith themes
- Scraping other accounts' content or analytics
- Automated follow/unfollow behavior

## Code Standards

- Python 3.12+ with type hints
- Ruff for linting (all checks must pass)
- Pytest for testing (maintain >80% coverage)
- SQLite with WAL mode for database
- All timestamps stored in UTC, displayed in configured timezone
- YAML for configuration, environment variables for secrets
- DRY: Extract common logic into reusable functions
- Safe: Validate inputs, handle errors gracefully, fail loudly on critical issues

## Scripture Attribution

Scripture quotations are from the ESV Bible (The Holy Bible, English Standard Version),
copyright 2001 by Crossway, a publishing ministry of Good News Publishers.
Used by permission. All rights reserved.
