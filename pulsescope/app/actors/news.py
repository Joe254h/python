"""Google News RSS actor - keyless, works anywhere Google News is reachable."""

from __future__ import annotations

import re
import urllib.parse
from xml.etree import ElementTree

from ..models import Mention
from .base import Actor, RunContext, clamp_text, parse_dt

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str) -> str:
    return " ".join(TAG_RE.sub(" ", value or "").split())


class GoogleNewsActor(Actor):
    name = "google-news-rss"
    platform = "news"
    keyless = True
    description = "Search-scoped Google News RSS feed; national and local press coverage."

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        window = max(1, min(ctx.lookback_days, 365))
        query = f"{ctx.term(subject)} when:{window}d"
        url = (
            "https://news.google.com/rss/search?q="
            + urllib.parse.quote(query)
            + f"&hl={ctx.language}-{ctx.region}&gl={ctx.region}&ceid={ctx.region}:{ctx.language}"
        )
        resp = await ctx.client.get(url)
        resp.raise_for_status()

        root = ElementTree.fromstring(resp.content)
        mentions: list[Mention] = []
        for item in root.iter("item"):
            title = strip_html(item.findtext("title", ""))
            if not title:
                continue
            source = item.findtext("{http://news.google.com}source") or item.findtext("source") or ""
            published = parse_dt(item.findtext("pubDate"))
            if published and published < ctx.since:
                continue
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=item.findtext("link", ""),
                    title=title,
                    text=clamp_text(strip_html(item.findtext("description", ""))),
                    author=source,
                    published_at=published,
                    kind="article",
                )
            )
        return mentions


class BingNewsActor(Actor):
    """Fallback press feed for regions where Google News is unavailable."""

    name = "bing-news-rss"
    platform = "news"
    keyless = True
    description = "Bing News RSS - secondary press source."

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        url = (
            "https://www.bing.com/news/search?format=RSS&q="
            + urllib.parse.quote(ctx.term(subject))
            + f"&cc={ctx.region}"
        )
        resp = await ctx.client.get(url)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)

        mentions: list[Mention] = []
        for item in root.iter("item"):
            title = strip_html(item.findtext("title", ""))
            published = parse_dt(item.findtext("pubDate"))
            if not title or (published and published < ctx.since):
                continue
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=item.findtext("link", ""),
                    title=title,
                    text=clamp_text(strip_html(item.findtext("description", ""))),
                    published_at=published,
                    kind="article",
                )
            )
        return mentions
