from __future__ import annotations

import tweepy


class XPublisher:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        dry_run: bool = True,
    ) -> None:
        self.dry_run = dry_run
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

    def print_authenticated_account(self) -> None:
        try:
            me = self.client.get_me(user_fields=["username", "name"])
            user = me.data
            if user is None:
                print("Authenticated X account: unknown (no user data returned)")
                return
            username = getattr(user, "username", None) or "unknown"
            name = getattr(user, "name", None) or "unknown"
            print(f"Authenticated X account: @{username} ({name})")
        except Exception as exc:
            print(f"Could not verify authenticated X account: {exc}")

    def post(self, text: str, in_reply_to_tweet_id: str | None = None) -> str:
        if self.dry_run:
            prefix = f"(reply to {in_reply_to_tweet_id}) " if in_reply_to_tweet_id else ""
            print(f"[DRY RUN] Would post to X {prefix}:\n{text}\n")
            return "dry-run"

        response = self.client.create_tweet(
            text=text,
            in_reply_to_tweet_id=in_reply_to_tweet_id,
        )
        tweet_id = str(response.data["id"])
        print(f"Posted tweet id={tweet_id}")
        return tweet_id

    def post_thread(self, posts: list[str]) -> list[str]:
        if not posts:
            return []
        tweet_ids: list[str] = []
        parent: str | None = None
        for text in posts:
            tweet_id = self.post(text=text, in_reply_to_tweet_id=parent)
            tweet_ids.append(tweet_id)
            if tweet_id != "dry-run":
                parent = tweet_id
        return tweet_ids
