"""Core data structures shared by actors, the scorer and the API."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Metric(str, Enum):
    MOMENTUM = "momentum"
    MESSAGE_CLARITY = "message_clarity"
    SOCIAL_PRESENCE = "social_presence"
    GROUND_VISIBILITY = "ground_visibility"
    SENTIMENT = "sentiment"
    REACH = "reach"

    @property
    def label(self) -> str:
        return {
            Metric.MOMENTUM: "Momentum building",
            Metric.MESSAGE_CLARITY: "Message clarity & manifesto",
            Metric.SOCIAL_PRESENCE: "Social media presence",
            Metric.GROUND_VISIBILITY: "Ground visibility",
            Metric.SENTIMENT: "Public sentiment",
            Metric.REACH: "Audience reach",
        }[self]


DEFAULT_METRICS = [
    Metric.MOMENTUM,
    Metric.MESSAGE_CLARITY,
    Metric.SOCIAL_PRESENCE,
    Metric.GROUND_VISIBILITY,
]

JobStatus = Literal["queued", "running", "succeeded", "failed"]


class Mention(BaseModel):
    """One scraped item: a post, video, article or comment about a subject."""

    subject: str
    platform: str
    actor: str
    url: str = ""
    title: str = ""
    text: str = ""
    author: str = ""
    published_at: datetime | None = None
    likes: int = 0
    shares: int = 0
    comments: int = 0
    views: int = 0
    followers: int = 0
    kind: str = "post"  # post | video | article | comment | profile
    simulated: bool = False
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)

    @property
    def engagement(self) -> int:
        return self.likes + self.shares * 2 + self.comments * 3

    @property
    def blob(self) -> str:
        return f"{self.title} {self.text}".strip()


class ProfileSnapshot(BaseModel):
    """Account-level stats for a subject on one platform."""

    subject: str
    platform: str
    handle: str = ""
    url: str = ""
    followers: int = 0
    posts: int = 0
    verified: bool = False
    simulated: bool = False


class ActorReport(BaseModel):
    """What one actor did for one subject - shown in the run log."""

    actor: str
    platform: str
    subject: str
    status: Literal["ok", "skipped", "error"]
    items: int = 0
    simulated: bool = False
    detail: str = ""
    elapsed_ms: int = 0


class MetricScore(BaseModel):
    metric: Metric
    score: float                      # 0-100, normalised across the cohort
    raw: float                        # pre-normalisation value
    rank: int = 0
    components: dict[str, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)


class SubjectResult(BaseModel):
    subject: str
    overall: float = 0.0
    rank: int = 0
    metrics: dict[Metric, MetricScore] = Field(default_factory=dict)
    mention_count: int = 0
    total_engagement: int = 0
    total_followers: int = 0
    platforms: dict[str, int] = Field(default_factory=dict)
    timeline: dict[str, int] = Field(default_factory=dict)   # ISO week -> mentions
    top_terms: list[tuple[str, int]] = Field(default_factory=list)
    sample_mentions: list[Mention] = Field(default_factory=list)
    simulated_share: float = 0.0


class Query(BaseModel):
    raw: str = ""
    subjects: list[str] = Field(default_factory=list)
    focus: str | None = None          # the subject the question is centred on
    metrics: list[Metric] = Field(default_factory=lambda: list(DEFAULT_METRICS))
    region: str = "KE"
    locality: str = ""                # e.g. "Bungoma County" - narrows searches
    lookback_days: int = 90
    platforms: list[str] = Field(default_factory=list)   # empty = all available


class RunResult(BaseModel):
    job_id: str
    query: Query
    status: JobStatus = "succeeded"
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
    results: list[SubjectResult] = Field(default_factory=list)
    actor_reports: list[ActorReport] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = ""
    total_mentions: int = 0
    data_quality: float = 0.0         # 0-1, share of evidence from live sources

    @property
    def elapsed_s(self) -> float:
        end = self.finished_at or utcnow()
        return (end - self.started_at).total_seconds()
