# Market News X Bot (Legal-First MVP)

This project pulls market-relevant news from public/official RSS feeds, summarizes each item, and posts short attributed updates to X.

## What it does
- Ingests from a **whitelist** of public feeds (Reuters business feed, CNBC markets RSS, SEC, Federal Reserve, Yahoo Finance).
- Applies source policy filters (allowlist/denylist) and optional `robots.txt` checks.
- Extracts probable ticker mentions and named entities from text.
- Ranks and selects the top fresh items.
- Summarizes into a concise X-ready post with source attribution.
- Posts to X as a single post or short thread when text is longer than one post.
- Deduplicates posted URLs in SQLite.

## Legal posture (important)
- Uses feed metadata and links, not full-content republishing.
- Adds source attribution and original link.
- Keeps summaries short and transformative.
- You are still responsible for checking each source's Terms of Service and API/RSS license before production use.

## Setup

1. Create and activate a virtual env:
```bash
cd /Users/shadipkhadka/delegate/market-news-x-bot
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

## Safe test mode
Set `DRY_RUN=true` in `.env` to print posts instead of sending to X.

## Notes
- In live mode (`DRY_RUN=false`), X API credentials are required.
- `data/posted_news.db` tracks posted item IDs to avoid duplicates.
- Adjust `MAX_POSTS_PER_RUN`, `MAX_THREAD_POSTS`, and `PRIORITY_TICKERS` in `.env`.
- Use `SOURCE_ALLOWLIST` / `SOURCE_DENYLIST` to control feed sources by name substring.
- Set `ENFORCE_ROBOTS_TXT=true` to skip URLs disallowed by each domain's robots policy.
# market-news-x-bot
