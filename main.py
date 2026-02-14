from __future__ import annotations

from pathlib import Path
import time

from apscheduler.schedulers.blocking import BlockingScheduler

from src.config import load_settings
from src.pipeline import run_once
from src.store import PostStore


def validate_config() -> None:
    settings = load_settings()
    if not settings.openai_api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    if not settings.dry_run:
        required = {
            "X_API_KEY": settings.x_api_key,
            "X_API_SECRET": settings.x_api_secret,
            "X_ACCESS_TOKEN": settings.x_access_token,
            "X_ACCESS_TOKEN_SECRET": settings.x_access_token_secret,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise RuntimeError(f"Missing X credentials for live posting: {', '.join(missing)}")


def main() -> None:
    validate_config()
    settings = load_settings()
    store = PostStore(Path("data/posted_news.db"))

    # Run immediately once, then on schedule.
    run_once(settings, store)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_once,
        "interval",
        hours=settings.run_every_hours,
        args=[settings, store],
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()


if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"Bot crashed: {exc}")
            # Simple recovery loop.
            time.sleep(10)
