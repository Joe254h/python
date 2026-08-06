"""Reddit actor - public search JSON, no key required."""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import Mention
from .base import Actor, RunContext, clamp_text, to_int


class RedditActor(Actor):
    name = "reddit-search"
    platform = "reddit"
    keyless = True
    description = "Reddit public search JSON: posts, scores and comment counts."

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        resp = await ctx.client.get(
            "https://www.reddit.com/search.json",
            params={
                "q": ctx.term(subject),
                "limit": min(100, ctx.max_items),
                "sort": "new",
                "t": "year" if ctx.lookback_days > 90 else "month",
            },
        )
        resp.raise_for_status()

        mentions: list[Mention] = []
        for child in resp.json().get("data", {}).get("children", []):
            post = child.get("data", {})
            created = post.get("created_utc")
            published = (
                datetime.fromtimestamp(created, tz=timezone.utc)
                if isinstance(created, (int, float))
                else None
            )
            if published and published < ctx.since:
                continue
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url="https://www.reddit.com" + post.get("permalink", ""),
                    title=clamp_text(post.get("title"), 300),
                    text=clamp_text(post.get("selftext")),
                    author=post.get("author", ""),
                    published_at=published,
                    likes=to_int(post.get("score")),
                    comments=to_int(post.get("num_comments")),
                    kind="post",
                    raw={"subreddit": post.get("subreddit")},
                )
            )
        return mentions
