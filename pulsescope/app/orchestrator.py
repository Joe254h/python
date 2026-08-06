"""Run actors across subjects, filter the harvest, score it, narrate it."""

from __future__ import annotations

import asyncio
import time
import uuid

import httpx

from . import actors as actor_registry
from .config import settings
from .models import ActorReport, Mention, Metric, Query, RunResult, SubjectResult, utcnow
from .nlp.text import tokenize
from .scoring import score_cohort

ACCOUNT_SCOPED = {"facebook", "instagram"}   # already subject-specific by construction


def _name_tokens(subject: str) -> list[str]:
    return [t for t in tokenize(subject, drop_stopwords=False) if len(t) > 2]


def is_relevant(mention: Mention, subject: str) -> bool:
    """Drop harvest that doesn't actually mention the subject."""
    if mention.platform in ACCOUNT_SCOPED or mention.simulated:
        return True
    tokens = _name_tokens(subject)
    if not tokens:
        return True
    blob = tokenize(mention.blob, drop_stopwords=False)
    if not blob:
        return False
    present = sum(1 for t in tokens if t in blob)
    # Full name of 2+ parts: require at least two matching parts, or the
    # surname when it is distinctive (5+ characters).
    if len(tokens) >= 2:
        surname = tokens[-1]
        return present >= 2 or (len(surname) >= 5 and surname in blob)
    return present >= 1


def dedupe(mentions: list[Mention]) -> list[Mention]:
    seen: set[str] = set()
    out: list[Mention] = []
    for m in mentions:
        key = m.url or (m.platform + "|" + " ".join(m.blob.lower().split())[:120])
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
    return out


async def harvest(query: Query) -> tuple[dict[str, list[Mention]], list[ActorReport], list[str]]:
    """Run every eligible actor against every subject, concurrently."""
    chosen = actor_registry.select(query.platforms)
    warnings: list[str] = []
    reports: list[ActorReport] = []
    corpus: dict[str, list[Mention]] = {s: [] for s in query.subjects}

    if settings.demo_mode:
        chosen = []
        warnings.append("PULSESCOPE_DEMO is set - all figures are simulated.")

    limits = httpx.Limits(max_connections=settings.concurrency * 2)
    headers = {"User-Agent": settings.user_agent, "Accept-Language": f"{query.region.lower()},en"}

    async with httpx.AsyncClient(
        timeout=settings.request_timeout, follow_redirects=True, limits=limits, headers=headers
    ) as client:
        ctx = actor_registry.RunContext(
            client=client,
            region=query.region,
            locality=query.locality,
            language=settings.language,
            lookback_days=query.lookback_days,
            max_items=settings.max_items_per_actor,
        )
        gate = asyncio.Semaphore(settings.concurrency)

        async def one(actor, subject: str):
            async with gate:
                return await actor.run(subject, ctx)

        tasks = [one(a, s) for a in chosen for s in query.subjects]
        for mentions, report in await asyncio.gather(*tasks, return_exceptions=False) or []:
            reports.append(report)
            if mentions:
                corpus[report.subject].extend(m for m in mentions if is_relevant(m, report.subject))

        # Fill in subjects the live actors found nothing for.
        empty = [s for s, ms in corpus.items() if not ms]
        if empty:
            if not settings.demo_mode:
                warnings.append(
                    "No live data for: " + ", ".join(empty)
                    + ". Falling back to simulated figures for these subjects - "
                    "add API credentials in .env for real numbers."
                )
            demo_ctx = actor_registry.RunContext(
                client=client,
                region=query.region,
                locality=query.locality,
                lookback_days=query.lookback_days,
                max_items=settings.max_items_per_actor * 2,
            )
            results = await asyncio.gather(
                *(actor_registry.DEMO_ACTOR.run(s, demo_ctx) for s in empty)
            )
            for mentions, report in results:
                reports.append(report)
                corpus[report.subject].extend(mentions)

    for subject in corpus:
        corpus[subject] = dedupe(corpus[subject])
    return corpus, reports, warnings


def narrate(query: Query, results: list[SubjectResult], data_quality: float) -> str:
    if not results:
        return "No subjects could be resolved from the query."

    lines: list[str] = []
    winner = results[0]
    focus = query.focus or winner.subject
    focus_result = next((r for r in results if r.subject.lower() == focus.lower()), winner)

    lines.append(
        f"Across {len(results)} subjects and {sum(r.mention_count for r in results)} collected items, "
        f"{winner.subject} leads overall at {winner.overall}/100."
    )

    if focus_result is not winner:
        gap = round(winner.overall - focus_result.overall, 1)
        lines.append(
            f"{focus_result.subject} ranks #{focus_result.rank} of {len(results)} "
            f"at {focus_result.overall}/100, {gap} points behind the leader."
        )
    else:
        runner_up = results[1] if len(results) > 1 else None
        if runner_up:
            lines.append(
                f"{focus_result.subject} holds first place, "
                f"{round(focus_result.overall - runner_up.overall, 1)} points clear of "
                f"{runner_up.subject}."
            )

    for metric in query.metrics:
        ordered = sorted(results, key=lambda r: r.metrics[metric].score, reverse=True)
        best, worst = ordered[0], ordered[-1]
        mine = focus_result.metrics[metric]
        lines.append(
            f"{metric.label}: {best.subject} strongest ({best.metrics[metric].score}), "
            f"{worst.subject} weakest ({worst.metrics[metric].score}); "
            f"{focus_result.subject} scores {mine.score} (rank {mine.rank})."
        )

    strengths = sorted(query.metrics, key=lambda m: focus_result.metrics[m].rank)
    if len(strengths) >= 2:
        lines.append(
            f"{focus_result.subject}'s best dimension is {strengths[0].label.lower()} "
            f"and the weakest is {strengths[-1].label.lower()}."
        )

    lines.append(
        f"Data quality: {round(data_quality * 100)}% of the evidence came from live sources."
        if data_quality > 0
        else "Data quality: 0% live - every figure below is simulated and must not be quoted."
    )
    return " ".join(lines)


async def run_query(query: Query, job_id: str | None = None) -> RunResult:
    started = time.perf_counter()
    result = RunResult(job_id=job_id or uuid.uuid4().hex[:12], query=query, status="running")

    if not query.subjects:
        result.status = "failed"
        result.finished_at = utcnow()
        result.warnings.append("Could not identify any subject names in the query.")
        result.summary = "Nothing to analyse - name at least one person, brand or topic."
        return result

    corpus, reports, warnings = await harvest(query)
    result.actor_reports = reports
    result.warnings = warnings

    total = sum(len(v) for v in corpus.values())
    live = sum(1 for v in corpus.values() for m in v if not m.simulated)
    result.total_mentions = total
    result.data_quality = round(live / total, 3) if total else 0.0

    result.results = score_cohort(corpus, query.metrics, query.lookback_days)
    result.summary = narrate(query, result.results, result.data_quality)
    result.status = "succeeded"
    result.finished_at = utcnow()

    _ = time.perf_counter() - started
    return result


async def run_prompt(prompt: str, **overrides) -> RunResult:
    """Parse a plain-English prompt and run it end to end."""
    from .query_parser import parse

    query = parse(prompt)
    for key, value in overrides.items():
        if value not in (None, [], "") and hasattr(query, key):
            setattr(query, key, value)
    return await run_query(query)
