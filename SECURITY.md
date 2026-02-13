# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email the maintainer directly or use GitHub's private vulnerability reporting feature.

### What to include in your report

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### Response timeline

- Initial response: within 48 hours
- Status update: within 7 days
- Resolution target: within 30 days (depending on severity)

## Security Best Practices for Contributors

### API Keys and Secrets

- Never commit API keys, tokens, or credentials
- Use environment variables via `.env` (which is gitignored)
- Rotate any keys immediately if accidentally exposed

### Dependencies

- Keep dependencies up to date
- Review Dependabot alerts promptly
- Avoid adding unnecessary dependencies

### Content Safety

This project handles automated social media posting. Contributors must:

- Never bypass human review requirements
- Respect rate limits and platform terms of service
- Never store personally identifiable information from viewers

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Security Features

This project includes several security measures:

- Admin-only authentication for the dashboard
- JWT-based session management with expiration
- Environment variable isolation for secrets
- Rate limiting on automated posting
- Auto-pause after consecutive failures
