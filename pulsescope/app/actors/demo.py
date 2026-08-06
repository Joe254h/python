"""Deterministic synthetic actor.

Runs only when live actors return nothing (no network, no credentials) or
when demo mode is forced. Every mention it produces carries
``simulated=True`` so the report, the API payload and the UI can label the
figures as fabricated. It exists to exercise the pipeline, not to inform a
decision.
"""

from __future__ import annotations

import hashlib
import random
from datetime import timedelta

from ..models import Mention
from .base import Actor, RunContext

PLATFORM_MIX = {
    "x": (0.30, "post"),
    "facebook": (0.24, "post"),
    "news": (0.16, "article"),
    "youtube": (0.10, "video"),
    "tiktok": (0.10, "video"),
    "instagram": (0.07, "post"),
    "reddit": (0.03, "post"),
}

TEMPLATES = [
    "{name} addressed residents at the {place} grassroots meeting, promising {policy} within {n} months.",
    "Huge turnout as {name} toured {place} ward; supporters say the campaign has real momentum.",
    "{name} launched a manifesto pledging {policy}, {policy2} and a {n}-year development plan.",
    "Analysts say {name} still lacks a clear message beyond generic promises about {policy}.",
    "{name} held a harambee at {place} church, raising funds for a local bursary programme.",
    "Critics accused {name} of avoiding hard questions on {policy} during the {place} debate.",
    "{name} was endorsed by elders in {place} after a door-to-door mobilisation drive.",
    "Social media buzz around {name} keeps rising following the {place} roadshow.",
    "{name} skipped the {place} town hall; opponents called the absence telling.",
    "{name} unveiled costed plans on {policy}, targeting {n} projects across the constituency.",
]

PLACES = ["Kimilili", "Bungoma", "Webuye", "Kanduyi", "Sirisia", "Tongaren", "Mt Elgon", "Naitiri"]
POLICIES = [
    "youth employment", "water access", "road repairs", "school bursaries", "healthcare funding",
    "dairy cooperatives", "market stalls", "electricity connections", "farm subsidies",
]


class DemoActor(Actor):
    """Synthetic data generator - clearly labelled, never mixed with live data silently."""

    name = "demo-simulator"
    platform = "simulated"
    keyless = True
    description = "Deterministic synthetic corpus used when no live source is reachable."

    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        seed = int(hashlib.sha256(subject.lower().encode()).hexdigest()[:12], 16)
        rng = random.Random(seed)

        # Per-subject personality so the cohort actually differentiates.
        volume = rng.randint(28, 95)
        clarity_bias = rng.uniform(0.2, 1.0)
        ground_bias = rng.uniform(0.2, 1.0)
        trend = rng.uniform(-0.6, 1.4)          # positive => accelerating
        audience = rng.randint(1_500, 220_000)

        platforms = list(PLATFORM_MIX)
        weights = [PLATFORM_MIX[p][0] for p in platforms]

        mentions: list[Mention] = []
        for i in range(min(volume, ctx.max_items)):
            platform = rng.choices(platforms, weights=weights, k=1)[0]
            kind = PLATFORM_MIX[platform][1]

            # Skew dates toward "now" when trend is positive.
            u = rng.random() ** (1.0 + max(0.0, trend))
            age_days = u * ctx.lookback_days
            published = ctx.since + timedelta(days=ctx.lookback_days - age_days)

            template = rng.choice(TEMPLATES)
            if rng.random() > clarity_bias:
                template = rng.choice(TEMPLATES[:2] + TEMPLATES[7:9])
            text = template.format(
                name=subject,
                place=rng.choice(PLACES),
                policy=rng.choice(POLICIES),
                policy2=rng.choice(POLICIES),
                n=rng.randint(2, 24),
            )
            if rng.random() < ground_bias * 0.4:
                text += f" The {rng.choice(PLACES)} rally drew a large crowd of residents."

            base = max(1, int(audience ** 0.55 * rng.uniform(0.05, 0.9)))
            mentions.append(
                Mention(
                    subject=subject,
                    platform=platform,
                    actor=self.name,
                    url=f"https://example.invalid/{platform}/{seed % 99991}/{i}",
                    title=text[:90],
                    text=text,
                    author=f"user{rng.randint(1000, 9999)}",
                    published_at=published,
                    likes=base,
                    shares=int(base * rng.uniform(0.05, 0.35)),
                    comments=int(base * rng.uniform(0.05, 0.4)),
                    views=int(base * rng.uniform(6, 40)) if kind == "video" else 0,
                    followers=audience,
                    kind=kind,
                    simulated=True,
                )
            )
        return mentions
