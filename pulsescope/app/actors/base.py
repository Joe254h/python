"""Actor contract.

An *actor* is a self-contained scraper for one platform, in the Apify sense:
it declares what credentials it needs, whether it can run right now, and it
returns a flat list of :class:`Mention` objects for one subject.
"""

from __future__ import annotations

import abc
import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from ..config import settings
from ..models import ActorReport, Mention, ProfileSnapshot


@dataclass
class RunContext:
    """Everything an actor needs for one run, shared across all subjects."""

    client: httpx.AsyncClient
    region: str = "KE"
    locality: str = ""
    language: str = "en"
    lookback_days: int = 90
    max_items: int = 60

    @property
    def since(self) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=self.lookback_days)

    def term(self, subject: str, quoted: bool = True) -> str:
        """Search string for one subject, narrowed by locality when known."""
        core = f'"{subject}"' if quoted else subject
        return f"{core} {self.locality}".strip()


class Actor(abc.ABC):
    """Base class for every platform scraper."""

    name: str = "actor"
    platform: str = "unknown"
    requires: tuple[str, ...] = ()          # human-readable credential names
    description: str = ""
    #: actors that read public endpoints without a key
    keyless: bool = False

    # -- capability -----------------------------------------------------
    def available(self) -> bool:
        """True when this actor has what it needs to hit a live source."""
        return self.keyless or bool(self.credential())

    def credential(self) -> str:
        return ""

    def unavailable_reason(self) -> str:
        if self.requires:
            return f"missing credential: {', '.join(self.requires)}"
        return "not available"

    # -- work -----------------------------------------------------------
    @abc.abstractmethod
    async def fetch(self, subject: str, ctx: RunContext) -> list[Mention]:
        """Return mentions of ``subject``. Raise on hard failure."""

    async def profile(self, subject: str, ctx: RunContext) -> ProfileSnapshot | None:
        """Optional account-level snapshot (followers etc.)."""
        return None

    # -- driver ---------------------------------------------------------
    async def run(self, subject: str, ctx: RunContext) -> tuple[list[Mention], ActorReport]:
        started = time.perf_counter()

        def report(status: str, items: int = 0, detail: str = "", simulated: bool = False):
            return ActorReport(
                actor=self.name,
                platform=self.platform,
                subject=subject,
                status=status,  # type: ignore[arg-type]
                items=items,
                detail=detail,
                simulated=simulated,
                elapsed_ms=int((time.perf_counter() - started) * 1000),
            )

        if not self.available():
            return [], report("skipped", detail=self.unavailable_reason())

        try:
            mentions = await asyncio.wait_for(
                self.fetch(subject, ctx), timeout=settings.request_timeout * 2
            )
        except asyncio.TimeoutError:
            return [], report("error", detail="timed out")
        except httpx.HTTPStatusError as exc:
            return [], report("error", detail=f"HTTP {exc.response.status_code}")
        except Exception as exc:  # noqa: BLE001 - one bad actor must not kill the run
            return [], report("error", detail=f"{type(exc).__name__}: {exc}"[:200])

        mentions = mentions[: ctx.max_items]
        simulated = bool(mentions) and all(m.simulated for m in mentions)
        return mentions, report("ok", items=len(mentions), simulated=simulated)


# ------------------------------------------------------------------ utils ---

def clamp_text(value: str | None, limit: int = 1200) -> str:
    return (value or "").strip()[:limit]


def to_int(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def parse_dt(value: str | None) -> datetime | None:
    """Best-effort ISO-8601 / RFC-822 date parsing."""
    if not value:
        return None
    value = value.strip()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    from email.utils import parsedate_to_datetime

    try:
        dt = parsedate_to_datetime(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None
