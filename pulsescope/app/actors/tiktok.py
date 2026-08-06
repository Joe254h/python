"""TikTok actor - official Research / Display API when a token is supplied."""

from __future__ import annotations

from datetime import datetime

from ..config import settings
from ..models import Mention
from .base import Actor, RunContext, clamp_text, to_int

RESEARCH_API = "https://open.tiktokapis.com/v2/research/video/query/"


class TikTokActor(Actor):
    name = "tiktok-research-query"
    platform = "tiktok"
    requires = ("TIKTOK_ACCESS_TOKEN",)
    description = "TikTok Research API keyword query with view/like/share counts."

    def credential(self) -> str:
        return settings.tiktok_access_token

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        body = {
            "query": {
                "and": [
                    {"operation": "IN", "field_name": "region_code", "field_values": [ctx.region]},
                    {"operation": "EQ", "field_name": "keyword", "field_values": [subject]},
                ]
            },
            "start_date": ctx.since.strftime("%Y%m%d"),
            "end_date": datetime.utcnow().strftime("%Y%m%d"),
            "max_count": min(100, ctx.max_items),
        }
        resp = await ctx.client.post(
            RESEARCH_API,
            params={
                "fields": "id,video_description,create_time,username,like_count,"
                          "comment_count,share_count,view_count"
            },
            json=body,
            headers={"Authorization": f"Bearer {self.credential()}"},
        )
        resp.raise_for_status()

        mentions: list[Mention] = []
        for video in resp.json().get("data", {}).get("videos", []):
            username = video.get("username", "")
            created = video.get("create_time")
            mentions.append(
                Mention(
                    subject=subject,
                    platform=self.platform,
                    actor=self.name,
                    url=f"https://www.tiktok.com/@{username}/video/{video.get('id')}",
                    text=clamp_text(video.get("video_description")),
                    author=username,
                    published_at=datetime.utcfromtimestamp(created).replace(tzinfo=None)
                    if isinstance(created, (int, float))
                    else None,
                    likes=to_int(video.get("like_count")),
                    comments=to_int(video.get("comment_count")),
                    shares=to_int(video.get("share_count")),
                    views=to_int(video.get("view_count")),
                    kind="video",
                )
            )
        return mentions
