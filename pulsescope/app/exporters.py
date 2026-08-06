"""CSV exports for the scoreboard and the raw mention corpus."""

from __future__ import annotations

import csv
import io

from .models import RunResult


def scores_csv(run: RunResult) -> str:
    buf = io.StringIO()
    metrics = run.query.metrics
    writer = csv.writer(buf)
    writer.writerow(
        ["rank", "subject", "overall"]
        + [m.value for m in metrics]
        + ["mentions", "engagement", "max_followers", "simulated_share"]
    )
    for r in run.results:
        writer.writerow(
            [r.rank, r.subject, r.overall]
            + [r.metrics[m].score for m in metrics]
            + [r.mention_count, r.total_engagement, r.total_followers, round(r.simulated_share, 3)]
        )
    return buf.getvalue()


def mentions_csv(run: RunResult) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["subject", "platform", "actor", "published_at", "author", "title", "text",
         "likes", "shares", "comments", "views", "url", "simulated"]
    )
    for r in run.results:
        for m in r.sample_mentions:
            writer.writerow(
                [
                    m.subject, m.platform, m.actor,
                    m.published_at.isoformat() if m.published_at else "",
                    m.author, m.title, " ".join(m.text.split()),
                    m.likes, m.shares, m.comments, m.views, m.url, m.simulated,
                ]
            )
    return buf.getvalue()
