"""Open-web actors: search engines and Wikipedia.

Web search catches the long tail - blogs, county press releases, party
sites - that platform APIs miss, and it is what makes "ground visibility"
measurable at all.
"""

from __future__ import annotations

import urllib.parse

from ..config import settings
from ..models import Mention
from .base import Actor, RunContext, clamp_text, parse_dt


class SerperActor(Actor):
    name = "serper-web-search"
    platform = "web"
    requires = ("SERPER_API_KEY",)
    description = "Google results via serper.dev - blogs, party sites, local press."

    def credential(self) -> str:
        return settings.serper_api_key

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        resp = await ctx.client.post(
            "https://google.serper.dev/search",
            json={"q": ctx.term(subject), "gl": ctx.region.lower(), "num": min(20, ctx.max_items)},
            headers={"X-API-KEY": self.credential(), "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        payload = resp.json()

        mentions: list[Mention] = []
        for block in ("organic", "news", "topStories"):
            for hit in payload.get(block, []) or []:
                mentions.append(
                    Mention(
                        subject=subject,
                        platform=self.platform,
                        actor=self.name,
                        url=hit.get("link", ""),
                        title=clamp_text(hit.get("title"), 300),
                        text=clamp_text(hit.get("snippet")),
                        author=hit.get("source", ""),
                        published_at=parse_dt(hit.get("date")),
                        kind="article",
                    )
                )
        return mentions


class BraveActor(Actor):
    name = "brave-web-search"
    platform = "web"
    requires = ("BRAVE_API_KEY",)
    description = "Brave Search API - independent web index."

    def credential(self) -> str:
        return settings.brave_api_key

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        resp = await ctx.client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": ctx.term(subject), "country": ctx.region, "count": min(20, ctx.max_items)},
            headers={"X-Subscription-Token": self.credential(), "Accept": "application/json"},
        )
        resp.raise_for_status()

        mentions: list[Mention] = []
        for hit in resp.json().get("web", {}).get("results", []):
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=hit.get("url", ""),
                    title=clamp_text(hit.get("title"), 300),
                    text=clamp_text(hit.get("description")),
                    published_at=parse_dt(hit.get("page_age")),
                    kind="article",
                )
            )
        return mentions


class WikipediaActor(Actor):
    name = "wikipedia-search"
    platform = "web"
    keyless = True
    description = "Wikipedia search + extracts; establishes public-figure baseline notability."

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        resp = await ctx.client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": subject,
                "srlimit": 5,
                "format": "json",
            },
        )
        resp.raise_for_status()

        mentions: list[Mention] = []
        for hit in resp.json().get("query", {}).get("search", []):
            title = hit.get("title", "")
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url="https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
                    title=title,
                    text=clamp_text(
                        hit.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", "")
                    ),
                    published_at=parse_dt(hit.get("timestamp")),
                    kind="article",
                )
            )
        return mentions
