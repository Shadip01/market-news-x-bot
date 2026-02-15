# Market News Bot (Email + X)

This project pulls market-relevant news from public/official RSS feeds, summarizes each item, and delivers updates via email and/or X.

## What it does
- Ingests from a whitelist of public feeds (Reuters business feed, CNBC markets RSS, SEC, Federal Reserve, Yahoo Finance).
- Applies source policy filters (allowlist/denylist) and optional `robots.txt` checks.
- Extracts probable ticker mentions and named entities from text.
- Keeps only recent stories (last `MAX_NEWS_AGE_HOURS`).
- Summarizes each story for:
  - X post/thread format.
  - Email digest format (headline + 3-4 summary lines + source link).
- Deduplicates posted URLs in SQLite (`data/posted_news.db`).

## Setup

1. Create and activate virtual environment:
```bash
cd /Users/shadipkhadka/Desktop/delegate/market-news-x-bot
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
```

## Email-only mode (recommended current setup)
Set in `.env`:
```env
X_ENABLED=false
EMAIL_ENABLED=true
DRY_RUN=false

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_smtp_password_or_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
```

Notes:
- If your Gmail account does not support App Passwords, use another SMTP provider.
- In email-only mode, X credentials are not required.

## X mode
If you also want X posting:
```env
X_ENABLED=true
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
```

## Run manually
```bash
python main.py
```

The bot runs once immediately, then repeats every `RUN_EVERY_HOURS`.

## Safe testing
Set `DRY_RUN=true` to print X posts and email digest content without sending live.

## Hourly background run on macOS (`launchd`)
This repo includes a one-run launcher script for `launchd`:
- `/Users/shadipkhadka/Desktop/delegate/market-news-x-bot/run_once_launchd.py`

Schedule it hourly with your LaunchAgent plist:
- `~/Library/LaunchAgents/com.shadip.marketnewsbot.plist`

Useful commands:
```bash
launchctl list | grep com.shadip.marketnewsbot
tail -n 80 /Users/shadipkhadka/Desktop/delegate/market-news-x-bot/logs/out.log
tail -n 80 /Users/shadipkhadka/Desktop/delegate/market-news-x-bot/logs/err.log
```

## Key config reference
- `X_ENABLED`: enable/disable X posting.
- `EMAIL_ENABLED`: enable/disable email digest sending.
- `DRY_RUN`: preview mode (no live sends).
- `MAX_POSTS_PER_RUN`: max stories processed per run.
- `MAX_NEWS_AGE_HOURS`: only include stories newer than this window.
- `SOURCE_ALLOWLIST` / `SOURCE_DENYLIST`: source name filters.
- `ENFORCE_ROBOTS_TXT`: skip URLs disallowed by robots rules.
