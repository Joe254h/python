"""Metric computation.

Every metric is produced in two stages:

1. **Raw value** - an interpretable number derived only from that subject's
   own corpus (e.g. "mentions in the recent third of the window divided by
   mentions in the earlier third").
2. **Score 0-100** - a blend of a *relative* term (where the subject sits
   inside this cohort) and an *absolute* term (a saturating curve on the raw
   value). The blend matters: pure min-max would hand the top of a weak field
   a 100, and a pure absolute scale would flatten a tight race.

The component values behind each score are returned as well, so nothing is a
black box.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timedelta, timezone

from .models import Mention, Metric, MetricScore, SubjectResult
from .nlp.text import (
    KEYWORD_SETS,
    has_numbers,
    keyword_density,
    normalised_entropy,
    sentiment_score,
    tokenize,
    top_terms,
)

# Relative-vs-absolute blend. 0.6 => cohort position dominates, but a field
# where nobody is doing anything cannot all score highly.
RELATIVE_WEIGHT = 0.6

#: Saturation constants for the absolute term: raw == k gives ~63/100.
SATURATION = {
    Metric.MOMENTUM: 1.0,
    Metric.MESSAGE_CLARITY: 0.45,
    Metric.SOCIAL_PRESENCE: 4.0,
    Metric.GROUND_VISIBILITY: 0.45,
    Metric.SENTIMENT: 0.5,
    Metric.REACH: 6.0,
}

COMPONENT_WEIGHTS: dict[Metric, dict[str, float]] = {
    Metric.MOMENTUM: {
        "volume_growth": 0.34,
        "engagement_growth": 0.26,
        "recency_weighted_volume": 0.22,
        "momentum_language": 0.18,
    },
    Metric.MESSAGE_CLARITY: {
        "topic_concentration": 0.28,
        "policy_language": 0.26,
        "commitment_language": 0.18,
        "specificity": 0.16,
        "manifesto_signal": 0.12,
    },
    Metric.SOCIAL_PRESENCE: {
        "platform_breadth": 0.26,
        "post_volume": 0.24,
        "engagement_volume": 0.26,
        "audience_size": 0.14,
        "posting_consistency": 0.10,
    },
    Metric.GROUND_VISIBILITY: {
        "field_activity_language": 0.32,
        "event_mention_share": 0.26,
        "activity_diversity": 0.20,
        "local_press_share": 0.22,
    },
}

ALL_PLATFORMS = ("x", "facebook", "instagram", "tiktok", "youtube", "reddit", "news", "web")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _split_window(mentions: list[Mention], lookback_days: int) -> tuple[list[Mention], list[Mention]]:
    """Split into (recent third, previous third) of the lookback window."""
    now = _now()
    cut_recent = now - timedelta(days=lookback_days / 3)
    cut_prev = now - timedelta(days=2 * lookback_days / 3)
    recent, previous = [], []
    for m in mentions:
        published = _aware(m.published_at)
        if published is None:
            continue
        if published >= cut_recent:
            recent.append(m)
        elif published >= cut_prev:
            previous.append(m)
    return recent, previous


def _ratio(a: float, b: float) -> float:
    """Growth ratio expressed on a log scale: 0 = flat, >0 = growing."""
    return math.log((a + 1.0) / (b + 1.0), 2)


# ------------------------------------------------------------ raw metrics ---

def momentum_raw(mentions: list[Mention], lookback_days: int) -> dict[str, float]:
    recent, previous = _split_window(mentions, lookback_days)

    volume_growth = max(0.0, _ratio(len(recent), len(previous)))
    eng_recent = sum(m.engagement for m in recent)
    eng_prev = sum(m.engagement for m in previous)
    engagement_growth = max(0.0, _ratio(eng_recent, eng_prev))

    # Exponentially recency-weighted volume, half-life = one sixth of window.
    half_life = max(1.0, lookback_days / 6)
    now = _now()
    weighted = 0.0
    for m in mentions:
        published = _aware(m.published_at)
        if published is None:
            weighted += 0.25
            continue
        age = max(0.0, (now - published).total_seconds() / 86400)
        weighted += 0.5 ** (age / half_life)
    recency_weighted_volume = math.log1p(weighted)

    blob = " ".join(m.blob for m in mentions)
    momentum_language = keyword_density(blob, "momentum") * 25

    return {
        "volume_growth": volume_growth,
        "engagement_growth": engagement_growth,
        "recency_weighted_volume": recency_weighted_volume,
        "momentum_language": momentum_language,
    }


def clarity_raw(mentions: list[Mention]) -> dict[str, float]:
    if not mentions:
        return {k: 0.0 for k in COMPONENT_WEIGHTS[Metric.MESSAGE_CLARITY]}

    texts = [m.blob for m in mentions if m.blob]
    counter: Counter[str] = Counter()
    for t in texts:
        counter.update(tokenize(t))
    focus = Counter(dict(counter.most_common(30)))
    topic_concentration = 1.0 - normalised_entropy(focus)

    blob = " ".join(texts)
    policy_language = keyword_density(blob, "policy") * 12
    commitment_language = keyword_density(blob, "commitment") * 8
    specificity = sum(1 for t in texts if has_numbers(t)) / max(1, len(texts))

    manifesto_terms = {"manifesto", "pledge", "pledges", "blueprint", "roadmap", "agenda", "plan"}
    hits = sum(1 for t in texts if manifesto_terms & set(tokenize(t)))
    manifesto_signal = min(1.0, hits / max(1.0, len(texts) * 0.25))

    return {
        "topic_concentration": topic_concentration,
        "policy_language": min(1.0, policy_language),
        "commitment_language": min(1.0, commitment_language),
        "specificity": specificity,
        "manifesto_signal": manifesto_signal,
    }


def presence_raw(mentions: list[Mention]) -> dict[str, float]:
    social = [m for m in mentions if m.platform not in {"news", "web"}]
    platforms = {m.platform for m in social}
    platform_breadth = len(platforms) / 6.0  # six social platforms are covered

    post_volume = math.log1p(len(social)) / math.log(101)          # 100 posts ~= 1.0
    engagement_volume = math.log1p(sum(m.engagement for m in social)) / math.log(1_000_001)
    audience_size = math.log1p(max((m.followers for m in mentions), default=0)) / math.log(1_000_001)

    weeks = {
        _aware(m.published_at).strftime("%G-W%V")
        for m in social
        if _aware(m.published_at) is not None
    }
    posting_consistency = min(1.0, len(weeks) / 12.0)

    return {
        "platform_breadth": min(1.0, platform_breadth),
        "post_volume": min(1.0, post_volume),
        "engagement_volume": min(1.0, engagement_volume),
        "audience_size": min(1.0, audience_size),
        "posting_consistency": posting_consistency,
    }


def ground_raw(mentions: list[Mention]) -> dict[str, float]:
    if not mentions:
        return {k: 0.0 for k in COMPONENT_WEIGHTS[Metric.GROUND_VISIBILITY]}

    texts = [m.blob for m in mentions if m.blob]
    blob = " ".join(texts)
    ground_vocab = KEYWORD_SETS["ground"]

    field_activity_language = min(1.0, keyword_density(blob, "ground") * 14)

    with_event = [t for t in texts if ground_vocab & set(tokenize(t))]
    event_mention_share = len(with_event) / max(1, len(texts))

    distinct = {w for t in texts for w in tokenize(t) if w in ground_vocab}
    activity_diversity = min(1.0, len(distinct) / 12.0)

    press = [m for m in mentions if m.platform == "news"]
    press_ground = [m for m in press if ground_vocab & set(tokenize(m.blob))]
    local_press_share = len(press_ground) / max(1, len(mentions)) * 4
    local_press_share = min(1.0, local_press_share)

    return {
        "field_activity_language": field_activity_language,
        "event_mention_share": event_mention_share,
        "activity_diversity": activity_diversity,
        "local_press_share": local_press_share,
    }


def sentiment_raw(mentions: list[Mention]) -> dict[str, float]:
    scores = [sentiment_score(m.blob) for m in mentions if m.blob]
    if not scores:
        return {"mean_sentiment": 0.0, "positive_share": 0.0}
    positive = sum(1 for s in scores if s > 0.05) / len(scores)
    return {
        "mean_sentiment": (sum(scores) / len(scores) + 1) / 2,  # -> 0..1
        "positive_share": positive,
    }


def reach_raw(mentions: list[Mention]) -> dict[str, float]:
    views = sum(m.views for m in mentions)
    followers = max((m.followers for m in mentions), default=0)
    engagement = sum(m.engagement for m in mentions)
    return {
        "impressions": math.log1p(views) / math.log(10_000_001),
        "audience": math.log1p(followers) / math.log(1_000_001),
        "engagement": math.log1p(engagement) / math.log(1_000_001),
    }


RAW_BUILDERS = {
    Metric.MOMENTUM: lambda ms, lb: momentum_raw(ms, lb),
    Metric.MESSAGE_CLARITY: lambda ms, lb: clarity_raw(ms),
    Metric.SOCIAL_PRESENCE: lambda ms, lb: presence_raw(ms),
    Metric.GROUND_VISIBILITY: lambda ms, lb: ground_raw(ms),
    Metric.SENTIMENT: lambda ms, lb: sentiment_raw(ms),
    Metric.REACH: lambda ms, lb: reach_raw(ms),
}


def _combine(metric: Metric, components: dict[str, float]) -> float:
    weights = COMPONENT_WEIGHTS.get(metric)
    if not weights:  # sentiment / reach use a flat mean
        return sum(components.values()) / max(1, len(components))
    return sum(components.get(k, 0.0) * w for k, w in weights.items())


def _normalise(metric: Metric, raw: float, cohort: list[float]) -> float:
    lo, hi = min(cohort), max(cohort)
    if hi - lo < 1e-9:
        relative = 0.5
    else:
        relative = (raw - lo) / (hi - lo)

    k = SATURATION.get(metric, 1.0)
    absolute = 1.0 - math.exp(-max(0.0, raw) / k)

    blended = RELATIVE_WEIGHT * relative + (1 - RELATIVE_WEIGHT) * absolute
    return round(8 + 90 * blended, 1)   # keep inside 8..98, never a bare 0 or 100


def _evidence(metric: Metric, mentions: list[Mention]) -> list[str]:
    """A few real lines from the corpus that drove the score."""
    family = {
        Metric.GROUND_VISIBILITY: "ground",
        Metric.MESSAGE_CLARITY: "policy",
        Metric.MOMENTUM: "momentum",
    }.get(metric)

    def key(m: Mention) -> tuple:
        vocab_hit = len(KEYWORD_SETS[family] & set(tokenize(m.blob))) if family else 0
        return (vocab_hit, m.engagement)

    ranked = sorted((m for m in mentions if m.blob), key=key, reverse=True)
    out = []
    for m in ranked[:3]:
        snippet = " ".join(m.blob.split())[:180]
        tag = "SIMULATED " if m.simulated else ""
        out.append(f"[{tag}{m.platform}] {snippet}")
    return out


def _timeline(mentions: list[Mention]) -> dict[str, int]:
    buckets: Counter[str] = Counter()
    for m in mentions:
        published = _aware(m.published_at)
        if published:
            buckets[published.strftime("%G-W%V")] += 1
    return dict(sorted(buckets.items()))


def score_cohort(
    corpus: dict[str, list[Mention]],
    metrics: list[Metric],
    lookback_days: int,
) -> list[SubjectResult]:
    """Score every subject on every requested metric and rank the field."""
    subjects = list(corpus)
    if not subjects:
        return []

    raw_table: dict[Metric, dict[str, tuple[float, dict[str, float]]]] = {}
    for metric in metrics:
        builder = RAW_BUILDERS[metric]
        raw_table[metric] = {}
        for subject in subjects:
            components = builder(corpus[subject], lookback_days)
            raw_table[metric][subject] = (_combine(metric, components), components)

    results: list[SubjectResult] = []
    for subject in subjects:
        mentions = corpus[subject]
        result = SubjectResult(
            subject=subject,
            mention_count=len(mentions),
            total_engagement=sum(m.engagement for m in mentions),
            total_followers=max((m.followers for m in mentions), default=0),
            platforms=dict(Counter(m.platform for m in mentions)),
            timeline=_timeline(mentions),
            top_terms=top_terms([m.blob for m in mentions], 12),
            sample_mentions=sorted(mentions, key=lambda m: m.engagement, reverse=True)[:5],
            simulated_share=(
                sum(1 for m in mentions if m.simulated) / len(mentions) if mentions else 0.0
            ),
        )
        for metric in metrics:
            raw, components = raw_table[metric][subject]
            cohort = [raw_table[metric][s][0] for s in subjects]
            result.metrics[metric] = MetricScore(
                metric=metric,
                score=_normalise(metric, raw, cohort),
                raw=round(raw, 4),
                components={k: round(v, 4) for k, v in components.items()},
                evidence=_evidence(metric, mentions),
            )
        result.overall = round(
            sum(result.metrics[m].score for m in metrics) / max(1, len(metrics)), 1
        )
        results.append(result)

    # Ranks: overall, then per metric.
    results.sort(key=lambda r: r.overall, reverse=True)
    for i, r in enumerate(results, start=1):
        r.rank = i
    for metric in metrics:
        ordered = sorted(results, key=lambda r: r.metrics[metric].score, reverse=True)
        for i, r in enumerate(ordered, start=1):
            r.metrics[metric].rank = i
    return results
