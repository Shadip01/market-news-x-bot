from __future__ import annotations

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

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = ""
        if resp.choices and resp.choices[0].message:
            text = (resp.choices[0].message.content or "").strip()
        if not text:
            return [self._fallback(item)]

        if item.url not in text:
            text = f"{text} {item.url}".strip()
        return self._to_thread(text, max_posts=max_thread_posts)

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

    @staticmethod
    def _fallback(item: NewsItem) -> str:
        ticker = f" (${item.tickers[0]})" if item.tickers else ""
        entity = f" [{item.entities[0]}]" if item.entities else ""
        text = f"{item.title[:150]}{ticker}{entity} Source: {item.source}. {item.url}"
        return text[:280]
