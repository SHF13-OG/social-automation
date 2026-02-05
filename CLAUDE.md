# CLAUDE.md - AI Assistant Rules for Social Media Automation

## Project Overview

This project automates faith-based TikTok content creation for an audience of 45+ Christians
navigating the second half of life. Content includes daily prayer videos with Bible verses,
AI voiceovers, and stock footage backgrounds.

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

# Run dashboard
streamlit run src/dashboard.py --server.port 8501 --server.headless true
```

## Architecture

- **CLI**: Typer (`src/main.py`) - data import, report generation, content pipeline
- **Dashboard**: Streamlit (`src/dashboard.py`) - analytics, config UI, publishing queue
- **Database**: SQLite (`data/social.db`) - posts, themes, verses, generated content
- **Config**: YAML defaults (`config/`) + DB overrides (`config_overrides` table)

## CRITICAL SAFETY RULES

### API Key Security
- NEVER commit API keys, tokens, or credentials to version control
- ALWAYS use environment variables via `.env` (which is in `.gitignore`)
- NEVER log API keys or credentials in output, errors, or debug messages
- NEVER hardcode keys in source files, even temporarily
- Rotate keys immediately if exposed in any commit

### Content Publishing
- NEVER publish content without human review via dry-run mode first
- ALWAYS respect rate limits: maximum 1 post per 4 hours
- NEVER auto-reply to comments without explicit human approval
- NEVER post more than 1 video per day unless the user explicitly requests it
- ALWAYS include stock footage attribution per license requirements
- Auto-pause publishing after 3 consecutive failures

### Content Guidelines
- NEVER generate content that promises physical healing or financial prosperity
- NEVER use "name it and claim it" or prosperity gospel language
- NEVER use manipulative, fear-based, or guilt-based language
- ALWAYS verify Bible verse text accuracy against the specified translation
- ALWAYS maintain a reverent, respectful, and conversational tone
- ALWAYS keep prayers personal and relatable ("Father, I come to you...")
- Target prayer duration: 62-70 seconds (approximately 150 words at 140 WPM)
- Focus on comfort, hope, encouragement, and authentic faith

### Data Protection
- NEVER store personally identifiable information from viewers
- NEVER share audience analytics data with third parties
- Keep engagement data for analytics purposes only

## AUTOMATION BOUNDARIES

### Allowed Automations
- Scheduled posting at user-configured times
- Stock footage search and download from licensed sources
- Audio generation via configured TTS provider (ElevenLabs)
- Video compositing with pre-approved templates
- Analytics collection from own TikTok account only
- Daily test runs and CI status reporting

### Requires Human Approval
- Publishing any new content (first 10 posts minimum)
- Responding to comments or messages
- Changing posting frequency
- Modifying content themes or Bible verse database
- Changing TTS voice or video style significantly
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
