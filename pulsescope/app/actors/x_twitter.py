"""X / Twitter actor.

Uses the official v2 API when ``X_BEARER_TOKEN`` is set. X blocks
unauthenticated scraping, so without a token this actor stays dormant and the
run log says so rather than inventing numbers.
"""

from __future__ import annotations

from ..config import settings
from ..models import Mention, ProfileSnapshot
from .base import Actor, RunContext, clamp_text, parse_dt, to_int

API = "https://api.twitter.com/2"


class XActor(Actor):
    name = "x-recent-search"
    platform = "x"
    requires = ("X_BEARER_TOKEN",)
    description = "X/Twitter API v2 recent search with public engagement metrics."

    def credential(self) -> str:
        return settings.x_bearer_token

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.credential()}"}

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        params = {
            "query": f"{ctx.term(subject)} -is:retweet",
            "max_results": max(10, min(100, ctx.max_items)),
            "tweet.fields": "created_at,public_metrics,lang,author_id",
            "expansions": "author_id",
            "user.fields": "username,public_metrics,verified",
        }
        resp = await ctx.client.get(
            f"{API}/tweets/search/recent", params=params, headers=self._headers
        )
        resp.raise_for_status()
        payload = resp.json()

        users = {
            u["id"]: u for u in payload.get("includes", {}).get("users", [])
        }
        mentions: list[Mention] = []
        for tweet in payload.get("data", []):
            metrics = tweet.get("public_metrics", {})
            user = users.get(tweet.get("author_id"), {})
            handle = user.get("username", "")
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=f"https://x.com/{handle or 'i'}/status/{tweet['id']}",
                    text=clamp_text(tweet.get("text")),
                    author=handle,
                    published_at=parse_dt(tweet.get("created_at")),
                    likes=to_int(metrics.get("like_count")),
                    shares=to_int(metrics.get("retweet_count")) + to_int(metrics.get("quote_count")),
                    comments=to_int(metrics.get("reply_count")),
                    views=to_int(metrics.get("impression_count")),
                    followers=to_int(user.get("public_metrics", {}).get("followers_count")),
                    kind="post",
                )
            )
        return mentions

    async def profile(self, subject: str, ctx: RunContext) -> ProfileSnapshot | None:
        handle = subject.replace(" ", "")
        resp = await ctx.client.get(
            f"{API}/users/by/username/{handle}",
            params={"user.fields": "public_metrics,verified"},
            headers=self._headers,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data")
        if not data:
            return None
        pm = data.get("public_metrics", {})
        return ProfileSnapshot(
            subject=subject,
            platform=self.platform,
            handle=data.get("username", handle),
            url=f"https://x.com/{data.get('username', handle)}",
            followers=to_int(pm.get("followers_count")),
            posts=to_int(pm.get("tweet_count")),
            verified=bool(data.get("verified")),
        )
