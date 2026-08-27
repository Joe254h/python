"""Endpoint and runtime configuration.

Every ICPAC deployment points at different servers, so nothing here is
hard-coded to one host: endpoints come from the environment, and several
may be configured at once (a GeoNode, a standalone GeoServer, a hazards
service). The agent queries all of them and says which one answered.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def _bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    return raw in {"1", "true", "yes", "on"} if raw else default


@dataclass(frozen=True)
class Endpoint:
    """One OGC server the agent can talk to."""

    name: str
    url: str
    services: tuple[str, ...] = ("WMS", "WFS", "WCS")
    username: str = ""
    password: str = ""
    token: str = ""

    @property
    def auth(self) -> tuple[str, str] | None:
        return (self.username, self.password) if self.username else None

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}


def _parse_endpoints() -> list[Endpoint]:
    """Read ICPAC_ENDPOINTS: 'name=url[|services=WMS,WFS];name2=url2'.

    Falls back to the single-endpoint variables when the list is unset.
    """
    raw = (os.getenv("ICPAC_ENDPOINTS") or "").strip()
    user = os.getenv("ICPAC_OGC_USER", "")
    pwd = os.getenv("ICPAC_OGC_PASSWORD", "")
    token = os.getenv("ICPAC_OGC_TOKEN", "")

    endpoints: list[Endpoint] = []
    if raw:
        for chunk in raw.split(";"):
            chunk = chunk.strip()
            if not chunk:
                continue
            name, _, rest = chunk.partition("=")
            if not rest:
                name, rest = f"endpoint{len(endpoints) + 1}", chunk
            url, _, opts = rest.partition("|")
            services: tuple[str, ...] = ("WMS", "WFS", "WCS")
            if opts.lower().startswith("services="):
                services = tuple(
                    s.strip().upper() for s in opts.split("=", 1)[1].split(",") if s.strip()
                )
            endpoints.append(
                Endpoint(name.strip(), url.strip().rstrip("?"), services, user, pwd, token)
            )
    elif single := (os.getenv("ICPAC_OGC_URL") or "").strip():
        endpoints.append(Endpoint("icpac", single.rstrip("?"), ("WMS", "WFS", "WCS"), user, pwd, token))

    return endpoints


@dataclass
class Settings:
    endpoints: list[Endpoint] = field(default_factory=_parse_endpoints)

    timeout: float = field(default_factory=lambda: _float("ICPAC_TIMEOUT", 45.0))
    concurrency: int = field(default_factory=lambda: _int("ICPAC_CONCURRENCY", 6))
    retries: int = field(default_factory=lambda: _int("ICPAC_RETRIES", 2))

    #: GetCapabilities documents are large and change rarely.
    capabilities_ttl: int = field(default_factory=lambda: _int("ICPAC_CAPABILITIES_TTL", 1800))
    #: Data responses are cached briefly so a multi-area comparison
    #: doesn't re-request the same coverage once per area.
    data_ttl: int = field(default_factory=lambda: _int("ICPAC_DATA_TTL", 120))

    #: Grid resolution for the WMS GetFeatureInfo sampling fallback.
    sample_grid: int = field(default_factory=lambda: _int("ICPAC_SAMPLE_GRID", 12))
    #: Largest WCS window (pixels per side) the agent will ask for.
    max_coverage_px: int = field(default_factory=lambda: _int("ICPAC_MAX_COVERAGE_PX", 512))

    verify_tls: bool = field(default_factory=lambda: _bool("ICPAC_VERIFY_TLS", True))
    user_agent: str = field(
        default_factory=lambda: os.getenv("ICPAC_UA", "ICPAC-Agent/1.0 (+MCP)")
    )

    @property
    def configured(self) -> bool:
        return bool(self.endpoints)


settings = Settings()
