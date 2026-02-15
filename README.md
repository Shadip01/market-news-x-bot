# Market News X Bot (Legal-First MVP)

This project pulls market-relevant news from public/official RSS feeds, summarizes each item, posts to X, and can send email digests.

## What it does
- Ingests from a whitelist of public feeds (Reuters business feed, CNBC markets RSS, SEC, Federal Reserve, Yahoo Finance).
- Applies source policy filters (allowlist/denylist) and optional `robots.txt` checks.
- Extracts probable ticker mentions and named entities from text.
- Keeps only recent stories (last `MAX_NEWS_AGE_HOURS`).
- Summarizes for X and posts as a single post or short thread.
- Sends an email digest with headline + 3-4 summary lines + source link.
- Deduplicates posted URLs in SQLite.

## Setup

1. Create and activate a virtual env:
```bash
cd /Users/shadipkhadka/Desktop/delegate/market-news-x-bot
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure env:
```bash
cp .env.example .env
```
Fill `.env` values.

## Run

```bash
python main.py
```

The bot runs once immediately, then repeats every `RUN_EVERY_HOURS`.

## Email setup
Set in `.env`:
```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
```

Use an app password if your provider requires it (Gmail/Outlook commonly do).

## Safe test mode
Set `DRY_RUN=true` in `.env` to print X posts and email digest content without sending live.

## Notes
- In live mode (`DRY_RUN=false`), X API credentials are required.
- `data/posted_news.db` tracks posted item IDs to avoid duplicates.
- Use `MAX_NEWS_AGE_HOURS` to control how recent stories must be.
- Use `SOURCE_ALLOWLIST` / `SOURCE_DENYLIST` to control feed sources.
- Set `ENFORCE_ROBOTS_TXT=true` to skip URLs disallowed by robots rules.
