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


def _as_csv(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    x_enabled: bool
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
    max_news_age_hours: int
    email_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    smtp_username: str
    smtp_password: str
    email_from: str
    email_to: tuple[str, ...]


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        x_enabled=_as_bool(os.getenv("X_ENABLED", "true"), default=True),
        x_api_key=os.getenv("X_API_KEY", ""),
        x_api_secret=os.getenv("X_API_SECRET", ""),
        x_access_token=os.getenv("X_ACCESS_TOKEN", ""),
        x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET", ""),
        dry_run=_as_bool(os.getenv("DRY_RUN", "true"), default=True),
        max_posts_per_run=_as_int(os.getenv("MAX_POSTS_PER_RUN"), default=3),
        run_every_hours=max(1, _as_int(os.getenv("RUN_EVERY_HOURS"), default=2)),
        priority_tickers=tuple(t.upper() for t in _as_csv(os.getenv("PRIORITY_TICKERS", ""))),
        source_allowlist=_as_csv(os.getenv("SOURCE_ALLOWLIST", "")),
        source_denylist=_as_csv(os.getenv("SOURCE_DENYLIST", "")),
        enforce_robots_txt=_as_bool(os.getenv("ENFORCE_ROBOTS_TXT", "true"), default=True),
        max_thread_posts=max(1, _as_int(os.getenv("MAX_THREAD_POSTS"), default=3)),
        max_news_age_hours=max(1, _as_int(os.getenv("MAX_NEWS_AGE_HOURS"), default=12)),
        email_enabled=_as_bool(os.getenv("EMAIL_ENABLED", "false"), default=False),
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=max(1, _as_int(os.getenv("SMTP_PORT"), default=587)),
        smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS", "true"), default=True),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        email_from=os.getenv("EMAIL_FROM", ""),
        email_to=_as_csv(os.getenv("EMAIL_TO", "")),
    )
