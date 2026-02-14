from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re
from urllib import robotparser
from urllib.parse import urlparse
from typing import Iterable

import feedparser
import httpx

from .models import NewsItem


# Use official/public RSS feeds to reduce legal risk.
ALLOWED_FEEDS = {
    "Reuters Business": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    "CNBC Markets": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "SEC Press Releases": "https://www.sec.gov/news/pressreleases.rss",
    "Federal Reserve News": "https://www.federalreserve.gov/feeds/press_all.xml",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
}

TICKER_PATTERN = re.compile(r"\b[A-Z]{1,5}\b")
BLOCKED_WORDS = {
    "A",
    "AN",
    "AND",
    "ARE",
    "AS",
    "AT",
    "BE",
    "BY",
    "FOR",
    "FROM",
    "HAS",
    "IN",
    "IS",
    "IT",
    "ITS",
    "OF",
    "ON",
    "OR",
    "THE",
    "TO",
    "US",
    "USD",
}
FINANCE_TERMS = {
    "EARNINGS",
    "GUIDANCE",
    "FORECAST",
    "MERGER",
    "ACQUISITION",
    "DIVIDEND",
    "BUYBACK",
    "IPO",
    "SEC",
    "FED",
    "INFLATION",
    "RATES",
    "REVENUE",
    "PROFIT",
    "LOSS",
    "OUTLOOK",
}
TICKER_CONTEXT_PATTERN = re.compile(r"\b(?:NASDAQ|NYSE|AMEX)\s*:\s*([A-Z]{1,5})\b")
DOLLAR_TICKER_PATTERN = re.compile(r"\$([A-Z]{1,5})\b")
ENTITY_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b")


def _parse_date(entry: dict) -> datetime | None:
    candidates = [entry.get("published"), entry.get("updated")]
    for raw in candidates:
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue
    return None


def _extract_tickers(title: str, summary: str) -> tuple[str, ...]:
    text = f"{title} {summary}"
    found = {m.group(0) for m in TICKER_PATTERN.finditer(text)}
    found.update(m.group(1) for m in DOLLAR_TICKER_PATTERN.finditer(text))
    found.update(m.group(1) for m in TICKER_CONTEXT_PATTERN.finditer(text))
    filtered = sorted(t for t in found if t not in BLOCKED_WORDS)
    return tuple(filtered[:8])


def _extract_entities(title: str, summary: str) -> tuple[str, ...]:
    text = f"{title}. {summary}"
    raw = {m.group(1).strip() for m in ENTITY_PATTERN.finditer(text)}
    cleaned = sorted(
        e for e in raw if len(e) >= 4 and e.upper() not in BLOCKED_WORDS and not e.isupper()
    )
    return tuple(cleaned[:8])


def _source_enabled(source_name: str, allowlist: tuple[str, ...], denylist: tuple[str, ...]) -> bool:
    lowered = source_name.lower()
    for token in denylist:
        if token.lower() in lowered:
            return False
    if not allowlist:
        return True
    return any(token.lower() in lowered for token in allowlist)


def _is_url_allowed_by_robots(
    url: str,
    robots_cache: dict[str, robotparser.RobotFileParser],
    user_agent: str = "*",
) -> bool:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False

    cache_key = f"{parsed.scheme}://{parsed.netloc}"
    rp = robots_cache.get(cache_key)
    if rp is None:
        robots_url = f"{cache_key}/robots.txt"
        rp = robotparser.RobotFileParser()
        try:
            with httpx.Client(timeout=5.0, follow_redirects=True) as client:
                response = client.get(robots_url)
                if response.status_code >= 400:
                    return True
                rp.parse(response.text.splitlines())
                robots_cache[cache_key] = rp
        except httpx.HTTPError:
            # Fail-open for availability; source allow/deny still applies.
            return True
    return rp.can_fetch(user_agent, url)


def _has_finance_signal(item: NewsItem) -> bool:
    text = f"{item.title} {item.summary}".upper()
    return any(term in text for term in FINANCE_TERMS)


def fetch_news_items(
    source_allowlist: tuple[str, ...] = (),
    source_denylist: tuple[str, ...] = (),
    enforce_robots_txt: bool = True,
) -> list[NewsItem]:
    items: list[NewsItem] = []
    robots_cache: dict[str, robotparser.RobotFileParser] = {}
    for source_name, url in ALLOWED_FEEDS.items():
        if not _source_enabled(source_name, source_allowlist, source_denylist):
            continue
        parsed = feedparser.parse(url)
        for entry in parsed.entries:
            link = entry.get("link", "").strip()
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "").strip()
            if not link or not title:
                continue
            if enforce_robots_txt and not _is_url_allowed_by_robots(link, robots_cache):
                continue

            news = NewsItem(
                id=link,
                source=source_name,
                title=title,
                summary=summary,
                url=link,
                published_at=_parse_date(entry),
                tickers=_extract_tickers(title, summary),
                entities=_extract_entities(title, summary),
            )
            items.append(news)

    # De-duplicate by canonical id (url)
    deduped = {item.id: item for item in items}
    return list(deduped.values())


def rank_news(items: Iterable[NewsItem], priority_tickers: tuple[str, ...]) -> list[NewsItem]:
    priority_set = set(priority_tickers)

    def score(item: NewsItem) -> tuple[int, int, int, float]:
        base = len(item.tickers) * 2 + len(item.entities)
        bonus = 5 if priority_set.intersection(item.tickers) else 0
        finance_bonus = 2 if _has_finance_signal(item) else 0
        ts = item.published_at.timestamp() if item.published_at else 0.0
        return (base + bonus + finance_bonus, len(item.tickers), len(item.entities), ts)

    return sorted(items, key=score, reverse=True)
