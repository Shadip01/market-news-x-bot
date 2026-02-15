from __future__ import annotations

import html
import re

from openai import OpenAI

from .models import NewsItem


class NewsSummarizer:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def summarize_for_x(self, item: NewsItem, max_thread_posts: int = 3) -> list[str]:
        ticker_text = ", ".join(item.tickers[:4]) if item.tickers else "none"
        entity_text = ", ".join(item.entities[:4]) if item.entities else "none"
        prompt = (
            "You are a financial news editor. Write a concise social summary for X. "
            "Be factual, neutral, and concise. No hype, no investment advice. "
            "Must include source attribution as 'Source: <name>' and 1-3 hashtags max. "
            "Target 300-700 characters so it can be split into a short thread if needed. "
            "Do not invent details.\n\n"
            f"Source: {item.source}\n"
            f"Title: {item.title}\n"
            f"Summary: {item.summary}\n"
            f"Tickers: {ticker_text}\n"
            f"Entities: {entity_text}\n"
            f"URL: {item.url}\n"
        )

        text = self._complete(prompt)
        if not text:
            return [self._fallback_x(item)]

        if item.url not in text:
            text = f"{text} {item.url}".strip()
        return self._to_thread(text, max_posts=max_thread_posts)

    def summarize_for_email(self, item: NewsItem) -> tuple[str, tuple[str, ...]]:
        clean_summary = self._clean_text(item.summary)
        prompt = (
            "Create an email-ready market news brief. "
            "Return exactly 5 lines in this format and no markdown:\n"
            "Headline: <clear headline>\n"
            "Line1: <summary sentence>\n"
            "Line2: <summary sentence>\n"
            "Line3: <summary sentence>\n"
            "Line4: <summary sentence>\n\n"
            "Use factual neutral tone, no investment advice, no invented facts.\n"
            f"Source: {item.source}\n"
            f"Title: {item.title}\n"
            f"Summary: {clean_summary}\n"
            f"URL: {item.url}\n"
        )
        text = self._complete(prompt)
        parsed = self._parse_email_lines(text)
        if parsed is not None:
            return parsed
        return self._fallback_email(item)

    def _complete(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        if resp.choices and resp.choices[0].message:
            return (resp.choices[0].message.content or "").strip()
        return ""

    @staticmethod
    def _parse_email_lines(text: str) -> tuple[str, tuple[str, ...]] | None:
        if not text:
            return None
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        headline = ""
        summary_lines: list[str] = []
        for line in lines:
            lowered = line.lower()
            if lowered.startswith("headline:"):
                headline = line.split(":", 1)[1].strip()
                continue
            if lowered.startswith("line") and ":" in line:
                candidate = line.split(":", 1)[1].strip()
                if candidate:
                    summary_lines.append(candidate)

        if headline and 3 <= len(summary_lines) <= 4:
            return headline, tuple(summary_lines)
        return None

    @staticmethod
    def _clean_text(value: str) -> str:
        text = html.unescape(value or "")
        text = re.sub(r"<[^>]+>", " ", text)
        return " ".join(text.split())

    def _to_thread(self, text: str, max_posts: int) -> list[str]:
        text = " ".join(text.split())
        if len(text) <= 280:
            return [text]

        chunks: list[str] = []
        remaining = text
        while remaining and len(chunks) < max_posts:
            if len(remaining) <= 280:
                chunks.append(remaining)
                remaining = ""
                break

            split_at = remaining.rfind(" ", 0, 260)
            if split_at <= 0:
                split_at = 260
            part = remaining[:split_at].strip()
            remaining = remaining[split_at:].strip()
            chunks.append(part)

        if remaining:
            chunks[-1] = f"{chunks[-1][:260].rstrip()}..."

        if len(chunks) == 1:
            return chunks

        numbered: list[str] = []
        total = len(chunks)
        for idx, part in enumerate(chunks, start=1):
            suffix = f" ({idx}/{total})"
            limit = 280 - len(suffix)
            numbered.append(f"{part[:limit].rstrip()}{suffix}")
        return numbered

    def _fallback_email(self, item: NewsItem) -> tuple[str, tuple[str, ...]]:
        headline = item.title[:120]
        clean = self._clean_text(item.summary)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
        if not sentences:
            sentences = ["Key market update from the source article."]
        summary_lines = tuple(sentences[:4])
        if len(summary_lines) < 3:
            summary_lines = summary_lines + (
                "Read the linked article for full details.",
            )
        return headline, summary_lines[:4]

    @staticmethod
    def _fallback_x(item: NewsItem) -> str:
        ticker = f" (${item.tickers[0]})" if item.tickers else ""
        entity = f" [{item.entities[0]}]" if item.entities else ""
        text = f"{item.title[:150]}{ticker}{entity} Source: {item.source}. {item.url}"
        return text[:280]
