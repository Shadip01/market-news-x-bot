from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .config import Settings
from .email_client import EmailPublisher, EmailSection
from .feeds import fetch_news_items, rank_news
from .store import PostStore
from .summarizer import NewsSummarizer
from .x_client import XPublisher


def run_once(settings: Settings, store: PostStore) -> int:
    all_items = fetch_news_items(
        source_allowlist=settings.source_allowlist,
        source_denylist=settings.source_denylist,
        enforce_robots_txt=settings.enforce_robots_txt,
    )
    ranked_items = rank_news(all_items, settings.priority_tickers)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.max_news_age_hours)
    latest_items = [
        item for item in ranked_items
        if item.published_at is not None and item.published_at >= cutoff
    ]

    fresh_items = [item for item in latest_items if not store.already_posted(item.id)]
    to_post = fresh_items[: settings.max_posts_per_run]

    print(
        "Run stats: "
        f"fetched={len(all_items)} "
        f"latest_window={len(latest_items)} "
        f"unposted_latest={len(fresh_items)}"
    )

    if not to_post:
        print(
            "No new items to post. "
            f"Try increasing MAX_NEWS_AGE_HOURS (currently {settings.max_news_age_hours})."
        )
        return 0

    summarizer = NewsSummarizer(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )

    publisher: XPublisher | None = None
    if settings.x_enabled:
        publisher = XPublisher(
            api_key=settings.x_api_key,
            api_secret=settings.x_api_secret,
            access_token=settings.x_access_token,
            access_token_secret=settings.x_access_token_secret,
            dry_run=settings.dry_run,
        )
        if not settings.dry_run:
            publisher.print_authenticated_account()

    email_sections: list[EmailSection] = []

    posted_count = 0
    for item in to_post:
        if publisher is not None:
            posts = summarizer.summarize_for_x(item, max_thread_posts=settings.max_thread_posts)
            publisher.post_thread(posts)

        headline, summary_lines = summarizer.summarize_for_email(item)
        email_sections.append(
            EmailSection(
                headline=headline,
                summary_lines=summary_lines,
                link=item.url,
                source=item.source,
            )
        )

        store.mark_posted(item.id)
        posted_count += 1

    if settings.email_enabled:
        email_publisher = EmailPublisher(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_use_tls=settings.smtp_use_tls,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            email_from=settings.email_from,
            email_to=settings.email_to,
            dry_run=settings.dry_run,
        )
        email_publisher.send_digest(email_sections)

    print(f"Finished run. Posted {posted_count} item(s).")
    return posted_count
