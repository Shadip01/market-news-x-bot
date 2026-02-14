from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsItem:
    id: str
    source: str
    title: str
    summary: str
    url: str
    published_at: datetime | None
    tickers: tuple[str, ...]
    entities: tuple[str, ...]
