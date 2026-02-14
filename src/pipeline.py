from __future__ import annotations

from .config import Settings
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

    fresh_items = [item for item in ranked_items if not store.already_posted(item.id)]
    to_post = fresh_items[: settings.max_posts_per_run]

    if not to_post:
        print("No new items to post.")
        return 0

    summarizer = NewsSummarizer(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )
    publisher = XPublisher(
        api_key=settings.x_api_key,
        api_secret=settings.x_api_secret,
        access_token=settings.x_access_token,
        access_token_secret=settings.x_access_token_secret,
        dry_run=settings.dry_run,
    )
    publisher.print_authenticated_account()

    posted_count = 0
    for item in to_post:
        posts = summarizer.summarize_for_x(item, max_thread_posts=settings.max_thread_posts)
        publisher.post_thread(posts)
        store.mark_posted(item.id)
        posted_count += 1

    print(f"Finished run. Posted {posted_count} item(s).")
    return posted_count
