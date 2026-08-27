"""Layer discovery and search across every configured endpoint.

The catalogue is what makes the agent usable by an LLM: instead of needing
a hard-coded list of ICPAC layer names, the model asks for "rainfall
anomaly" and gets back the layers the live servers actually publish today.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field

from .config import Endpoint, settings
from .models import Layer, SourceReport
from .ogc.capabilities import CAPABILITIES_PARAMS, FALLBACK_VERSIONS, PARSERS
from .ogc.client import OGCClient, OGCError

#: Domain vocabulary. A question mentioning any synonym boosts layers whose
#: name/title/keywords carry the canonical term - the difference between
#: "rainfall" matching `chirps_rfe_dekad` and matching nothing.
CONCEPTS: dict[str, tuple[str, ...]] = {
    "rainfall": ("rain", "rainfall", "precip", "precipitation", "rfe", "chirps",
                 "tamsat", "wet", "pptn", "mm"),
    "temperature": ("temp", "temperature", "tmax", "tmin", "lst", "heat", "degc"),
    "drought": ("drought", "spi", "spei", "vci", "tci", "vhi", "dryness", "deficit",
                "cdi", "aridity"),
    "vegetation": ("ndvi", "evi", "vegetation", "greenness", "biomass", "vci", "pasture"),
    "flood": ("flood", "inundation", "streamflow", "discharge", "runoff", "riverine"),
    "forecast": ("forecast", "outlook", "prediction", "seasonal", "gefs", "ecmwf",
                 "anomaly forecast", "probabilistic"),
    "anomaly": ("anomaly", "anomalies", "departure", "deviation", "normal", "climatology"),
    "hazard": ("hazard", "alert", "warning", "risk", "impact", "exposure", "watch"),
    "admin": ("admin", "boundary", "boundaries", "county", "counties", "district",
              "region", "province", "gadm", "adm0", "adm1", "adm2", "woreda"),
    "population": ("population", "pop", "worldpop", "density", "settlement"),
    "livestock": ("livestock", "cattle", "pasture", "rangeland", "herd"),
    "crop": ("crop", "yield", "maize", "agriculture", "cropland", "harvest", "planting"),
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def concepts_in(text: str) -> set[str]:
    lowered = (text or "").lower()
    return {
        concept
        for concept, words in CONCEPTS.items()
        if any(word in lowered for word in words)
    }


@dataclass
class Catalog:
    """Cached view of everything the configured endpoints publish."""

    layers: dict[str, Layer] = field(default_factory=dict)
    reports: list[SourceReport] = field(default_factory=list)
    fetched_at: float = 0.0

    @property
    def fresh(self) -> bool:
        return bool(self.layers) and (time.monotonic() - self.fetched_at) < settings.capabilities_ttl

    # ------------------------------------------------------------------
    def by_service(self, service: str) -> list[Layer]:
        return [layer for layer in self.layers.values() if layer.service == service]

    def get(self, layer_id: str) -> Layer | None:
        """Look a layer up by full id, bare name, or unambiguous suffix."""
        if layer_id in self.layers:
            return self.layers[layer_id]
        wanted = layer_id.lower()

        exact = [
            layer for layer in self.layers.values()
            if layer.name.lower() == wanted or layer.id.lower() == wanted
        ]
        if exact:
            return _prefer(exact)

        # "rfe_dekad" should find "icpac:workspace:rfe_dekad"
        suffix = [
            layer for layer in self.layers.values()
            if layer.name.lower().rsplit(":", 1)[-1] == wanted.rsplit(":", 1)[-1]
        ]
        return _prefer(suffix) if suffix else None

    def siblings(self, layer: Layer) -> dict[str, Layer]:
        """The same layer name as published by each service."""
        out: dict[str, Layer] = {}
        bare = layer.name.lower()
        for other in self.layers.values():
            if other.name.lower() == bare and other.endpoint == layer.endpoint:
                out[other.service] = other
        return out

    def search(self, query: str, *, limit: int = 15, service: str = "") -> list[tuple[Layer, float]]:
        """Rank layers against a free-text query."""
        query_tokens = set(tokens(query))
        query_concepts = concepts_in(query)
        if not query_tokens:
            return []

        scored: list[tuple[Layer, float]] = []
        for layer in self.layers.values():
            if service and layer.service != service.upper():
                continue

            haystack = layer.searchable_text
            layer_tokens = set(tokens(haystack))
            overlap = query_tokens & layer_tokens
            if not overlap and not (query_concepts & concepts_in(haystack)):
                continue

            score = 3.0 * len(overlap) / max(1, len(query_tokens))
            score += 2.0 * len(query_concepts & concepts_in(haystack)) / max(1, len(query_concepts))

            # Whole-phrase hits in the title are the strongest signal.
            if query.lower().strip() in (layer.title or "").lower():
                score += 3.0
            for token in query_tokens:
                if token in layer.name.lower():
                    score += 0.6
            if layer.temporal:
                score += 0.4          # live-feed questions want time-aware layers
            if layer.service == "WCS":
                score += 0.3          # real pixels beat rendered samples
            scored.append((layer, round(score, 3)))

        scored.sort(key=lambda pair: (-pair[1], pair[0].id))
        return scored[:limit]


def _prefer(candidates: list[Layer]) -> Layer:
    """Pick the richest description of a dataset.

    WMS capabilities carry the time dimension, styles and bounding box that
    WCS/WFS documents usually omit, so that is the better handle to return.
    Readers call :meth:`Catalog.siblings` to reach the WCS variant when they
    want real pixels.
    """
    order = {"WMS": 0, "WFS": 1, "WCS": 2}
    return sorted(
        candidates,
        key=lambda layer: (not layer.temporal, order.get(layer.service, 9), layer.id),
    )[0]


# ---------------------------------------------------------------- loading ---

async def _load_one(
    client: OGCClient, endpoint: Endpoint, service: str
) -> tuple[list[Layer], SourceReport]:
    started = time.perf_counter()

    def report(status: str, detail: str = "", cached: bool = False) -> SourceReport:
        return SourceReport(
            endpoint=endpoint.name,
            service=service,
            status=status,  # type: ignore[arg-type]
            detail=detail,
            cached=cached,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
        )

    base = CAPABILITIES_PARAMS[service]
    versions = [base["version"], *FALLBACK_VERSIONS.get(service, [])]
    last = ""

    for version in versions:
        try:
            body, _ = await client.get(
                endpoint, {**base, "version": version}, ttl=settings.capabilities_ttl
            )
        except OGCError as exc:
            last = str(exc)
            continue
        try:
            layers = PARSERS[service](body, endpoint.name)
        except Exception as exc:  # noqa: BLE001 - malformed XML is a source problem
            last = f"could not parse capabilities: {type(exc).__name__}"
            continue
        if layers:
            plural = "" if len(layers) == 1 else "s"
            return layers, report(
                "ok",
                f"{len(layers)} layer{plural} via {service} {version}",
                cached=client.last_call_cached,
            )
        last = f"{service} {version} advertised no layers"

    return [], report("empty" if not last.startswith(("HTTP", "Timeout")) else "error", last)


async def load_catalog(client: OGCClient, *, force: bool = False) -> Catalog:
    """Fetch capabilities from every endpoint x service, concurrently."""
    global _CACHE
    if _CACHE.fresh and not force:
        return _CACHE

    if not settings.configured:
        catalog = Catalog(
            reports=[
                SourceReport(
                    endpoint="-", service="-", status="skipped",
                    detail="no endpoints configured; set ICPAC_ENDPOINTS or ICPAC_OGC_URL",
                )
            ],
            fetched_at=time.monotonic(),
        )
        _CACHE = catalog
        return catalog

    jobs = [
        (endpoint, service)
        for endpoint in settings.endpoints
        for service in endpoint.services
        if service in PARSERS
    ]
    results = await asyncio.gather(
        *(_load_one(client, endpoint, service) for endpoint, service in jobs)
    )

    catalog = Catalog(fetched_at=time.monotonic())
    for layers, report in results:
        catalog.reports.append(report)
        for layer in layers:
            # Same name across services: keep both, keyed by service.
            catalog.layers[f"{layer.id}#{layer.service}"] = layer

    _CACHE = catalog
    return catalog


_CACHE = Catalog()


def cached_catalog() -> Catalog:
    return _CACHE


def reset_cache() -> None:
    global _CACHE
    _CACHE = Catalog()
