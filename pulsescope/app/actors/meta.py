"""Facebook and Instagram actors, via the Meta Graph API.

Meta does not expose a public keyword search: the Graph API only reads Pages
and Instagram Business accounts you are authorised for. So these actors work
by resolving each subject to a Page / IG account and reading its posts, which
is the supported and ToS-compliant path.
"""

from __future__ import annotations

from ..config import settings
from ..models import Mention, ProfileSnapshot
from .base import Actor, RunContext, clamp_text, parse_dt, to_int

GRAPH = "https://graph.facebook.com/v19.0"


class _MetaActor(Actor):
    requires = ("META_ACCESS_TOKEN",)

    def credential(self) -> str:
        return settings.meta_access_token

    async def _search_page(self, subject: str, ctx: RunContext) -> dict | None:
        resp = await ctx.client.get(
            f"{GRAPH}/pages/search",
            params={"q": subject, "fields": "id,name,fan_count,verification_status",
                    "access_token": self.credential()},
        )
        if resp.status_code != 200:
            return None
        for page in resp.json().get("data", []):
            if subject.lower().split()[0] in page.get("name", "").lower():
                return page
        return None


class FacebookActor(_MetaActor):
    name = "facebook-page-feed"
    platform = "facebook"
    description = "Meta Graph API: resolves the subject's Page and reads its feed + reactions."

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        page = await self._search_page(subject, ctx)
        if not page:
            return []
        fields = (
            "message,story,created_time,permalink_url,"
            "reactions.summary(true).limit(0),comments.summary(true).limit(0),"
            "shares"
        )
        resp = await ctx.client.get(
            f"{GRAPH}/{page['id']}/posts",
            params={"fields": fields, "limit": ctx.max_items, "access_token": self.credential()},
        )
        resp.raise_for_status()

        followers = to_int(page.get("fan_count"))
        mentions: list[Mention] = []
        for post in resp.json().get("data", []):
            published = parse_dt(post.get("created_time"))
            if published and published < ctx.since:
                continue
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=post.get("permalink_url", ""),
                    text=clamp_text(post.get("message") or post.get("story")),
                    author=page.get("name", ""),
                    published_at=published,
                    likes=to_int(post.get("reactions", {}).get("summary", {}).get("total_count")),
                    comments=to_int(post.get("comments", {}).get("summary", {}).get("total_count")),
                    shares=to_int((post.get("shares") or {}).get("count")),
                    followers=followers,
                    kind="post",
                )
            )
        return mentions

    async def profile(self, subject: str, ctx: RunContext) -> ProfileSnapshot | None:
        page = await self._search_page(subject, ctx)
        if not page:
            return None
        return ProfileSnapshot(
            subject=subject,
            platform=self.platform,
            handle=page.get("name", ""),
            url=f"https://facebook.com/{page['id']}",
            followers=to_int(page.get("fan_count")),
            verified=page.get("verification_status") in {"blue_verified", "grey_verified"},
        )


class InstagramActor(_MetaActor):
    name = "instagram-business-discovery"
    platform = "instagram"
    description = "Meta Graph business_discovery: public IG business/creator account media."

    def _ig_user_id(self) -> str:
        import os

        return os.getenv("IG_BUSINESS_ACCOUNT_ID", "")

    def available(self) -> bool:
        return bool(self.credential() and self._ig_user_id())

    def unavailable_reason(self) -> str:
        return "missing credential: META_ACCESS_TOKEN + IG_BUSINESS_ACCOUNT_ID"

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        handle = subject.lower().replace(" ", "")
        fields = (
            f"business_discovery.username({handle})"
            "{followers_count,media_count,media{caption,like_count,comments_count,timestamp,permalink}}"
        )
        resp = await ctx.client.get(
            f"{GRAPH}/{self._ig_user_id()}",
            params={"fields": fields, "access_token": self.credential()},
        )
        if resp.status_code != 200:
            return []
        bd = resp.json().get("business_discovery", {})
        followers = to_int(bd.get("followers_count"))

        mentions: list[Mention] = []
        for media in bd.get("media", {}).get("data", [])[: ctx.max_items]:
            published = parse_dt(media.get("timestamp"))
            if published and published < ctx.since:
                continue
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=media.get("permalink", ""),
                    text=clamp_text(media.get("caption")),
                    author=handle,
                    published_at=published,
                    likes=to_int(media.get("like_count")),
                    comments=to_int(media.get("comments_count")),
                    followers=followers,
                    kind="post",
                )
            )
        return mentions
