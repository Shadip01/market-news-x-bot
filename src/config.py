import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value: str, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    x_api_key: str
    x_api_secret: str
    x_access_token: str
    x_access_token_secret: str
    dry_run: bool
    max_posts_per_run: int
    run_every_hours: int
    priority_tickers: tuple[str, ...]
    source_allowlist: tuple[str, ...]
    source_denylist: tuple[str, ...]
    enforce_robots_txt: bool
    max_thread_posts: int


def load_settings() -> Settings:
    priority_raw = os.getenv("PRIORITY_TICKERS", "")
    source_allow_raw = os.getenv("SOURCE_ALLOWLIST", "")
    source_deny_raw = os.getenv("SOURCE_DENYLIST", "")
    priority_tickers = tuple(
        t.strip().upper() for t in priority_raw.split(",") if t.strip()
    )
    source_allowlist = tuple(s.strip() for s in source_allow_raw.split(",") if s.strip())
    source_denylist = tuple(s.strip() for s in source_deny_raw.split(",") if s.strip())
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        x_api_key=os.getenv("X_API_KEY", ""),
        x_api_secret=os.getenv("X_API_SECRET", ""),
        x_access_token=os.getenv("X_ACCESS_TOKEN", ""),
        x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET", ""),
        dry_run=_as_bool(os.getenv("DRY_RUN", "true"), default=True),
        max_posts_per_run=_as_int(os.getenv("MAX_POSTS_PER_RUN"), default=3),
        run_every_hours=max(1, _as_int(os.getenv("RUN_EVERY_HOURS"), default=2)),
        priority_tickers=priority_tickers,
        source_allowlist=source_allowlist,
        source_denylist=source_denylist,
        enforce_robots_txt=_as_bool(os.getenv("ENFORCE_ROBOTS_TXT", "true"), default=True),
        max_thread_posts=max(1, _as_int(os.getenv("MAX_THREAD_POSTS"), default=3)),
    )
