"""Actor registry - add a new platform by appending one class here."""

from __future__ import annotations

from .base import Actor, RunContext
from .demo import DemoActor
from .meta import FacebookActor, InstagramActor
from .news import BingNewsActor, GoogleNewsActor
from .reddit import RedditActor
from .tiktok import TikTokActor
from .web import BraveActor, SerperActor, WikipediaActor
from .x_twitter import XActor
from .youtube import YouTubeActor

#: Every live actor, in the order they appear in the run log.
LIVE_ACTORS: list[Actor] = [
    XActor(),
    FacebookActor(),
    InstagramActor(),
    TikTokActor(),
    YouTubeActor(),
    RedditActor(),
    GoogleNewsActor(),
    BingNewsActor(),
    SerperActor(),
    BraveActor(),
    WikipediaActor(),
]

DEMO_ACTOR = DemoActor()


def all_actors() -> list[Actor]:
    return list(LIVE_ACTORS)


def select(platforms: list[str] | None = None) -> list[Actor]:
    """Live actors, optionally filtered to a set of platform slugs."""
    if not platforms:
        return list(LIVE_ACTORS)
    wanted = {p.lower() for p in platforms}
    return [a for a in LIVE_ACTORS if a.platform in wanted]


def catalogue() -> list[dict]:
    """Serialisable description of every actor, for the /api/actors endpoint."""
    return [
        {
            "name": a.name,
            "platform": a.platform,
            "description": a.description,
            "requires": list(a.requires),
            "available": a.available(),
            "reason": "" if a.available() else a.unavailable_reason(),
        }
        for a in LIVE_ACTORS
    ]


__all__ = [
    "Actor",
    "RunContext",
    "LIVE_ACTORS",
    "DEMO_ACTOR",
    "all_actors",
    "select",
    "catalogue",
]
