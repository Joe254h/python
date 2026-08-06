"""YouTube actor.

With ``YOUTUBE_API_KEY`` it uses the official Data API v3 (search + video
statistics). Without a key it degrades to YouTube's public RSS feeds, which
carry titles and dates but no view counts.
"""

from __future__ import annotations

import urllib.parse
from xml.etree import ElementTree

from ..config import settings
from ..models import Mention
from .base import Actor, RunContext, clamp_text, parse_dt, to_int

API = "https://www.googleapis.com/youtube/v3"
YT_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


class YouTubeActor(Actor):
    name = "youtube-search"
    platform = "youtube"
    requires = ("YOUTUBE_API_KEY",)
    keyless = True  # RSS fallback keeps it useful without a key
    description = "YouTube Data API v3 search with per-video statistics (RSS fallback)."

    def credential(self) -> str:
        return settings.youtube_api_key

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        if self.credential():
            return await self._fetch_api(subject, ctx)
        return await self._fetch_rss(subject, ctx)

    async def _fetch_api(self, subject: str, ctx: RunContext) -> list[Mention]:
        params = {
            "part": "snippet",
            "q": ctx.term(subject, quoted=False),
            "type": "video",
            "maxResults": min(50, ctx.max_items),
            "order": "date",
            "publishedAfter": ctx.since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "regionCode": ctx.region,
            "key": self.credential(),
        }
        resp = await ctx.client.get(f"{API}/search", params=params)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return []

        ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
        stats: dict[str, dict] = {}
        if ids:
            sresp = await ctx.client.get(
                f"{API}/videos",
                params={"part": "statistics", "id": ",".join(ids), "key": self.credential()},
            )
            if sresp.status_code == 200:
                stats = {v["id"]: v.get("statistics", {}) for v in sresp.json().get("items", [])}

        mentions: list[Mention] = []
        for item in items:
            vid = item.get("id", {}).get("videoId")
            snip = item.get("snippet", {})
            if not vid:
                continue
            st = stats.get(vid, {})
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=f"https://www.youtube.com/watch?v={vid}",
                    title=clamp_text(snip.get("title"), 300),
                    text=clamp_text(snip.get("description")),
                    author=snip.get("channelTitle", ""),
                    published_at=parse_dt(snip.get("publishedAt")),
                    likes=to_int(st.get("likeCount")),
                    comments=to_int(st.get("commentCount")),
                    views=to_int(st.get("viewCount")),
                    kind="video",
                )
            )
        return mentions

    async def _fetch_rss(self, subject: str, ctx: RunContext) -> list[Mention]:
        url = (
            "https://www.youtube.com/feeds/videos.xml?search_query="
            + urllib.parse.quote(ctx.term(subject, quoted=False))
        )
        resp = await ctx.client.get(url)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)

        mentions: list[Mention] = []
        for entry in root.findall("atom:entry", YT_NS):
            published = parse_dt(entry.findtext("atom:published", "", YT_NS))
            if published and published < ctx.since:
                continue
            link = entry.find("atom:link", YT_NS)
            group = entry.find("media:group", YT_NS)
            community = entry.find("media:group/media:community", YT_NS)
            views = likes = 0
            if community is not None:
                stat = community.find("media:statistics", YT_NS)
                star = community.find("media:starRating", YT_NS)
                views = to_int(stat.get("views")) if stat is not None else 0
                likes = to_int(star.get("count")) if star is not None else 0
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=link.get("href", "") if link is not None else "",
                    title=clamp_text(entry.findtext("atom:title", "", YT_NS), 300),
                    text=clamp_text(
                        group.findtext("media:description", "", YT_NS) if group is not None else ""
                    ),
                    author=entry.findtext("atom:author/atom:name", "", YT_NS),
                    published_at=published,
                    views=views,
                    likes=likes,
                    kind="video",
                )
            )
        return mentions
