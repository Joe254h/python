"""Layer discovery and search across every configured endpoint.

The catalogue is what makes the agent usable by an LLM: instead of needing
a hard-coded list of ICPAC layer names, the model asks for "rainfall
anomaly" and gets back the layers the live servers actually publish today.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections import Counter
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
    "anomaly": ("anomaly", "anomalies", "departure", "deviation", "climatology",
                "of normal", "percent of normal", "pct of normal", "normalised",
                "normalized"),
    "hazard": ("hazard", "alert", "warning", "risk", "impact", "exposure", "watch"),
    "admin": ("admin", "boundary", "boundaries", "county", "counties", "district",
              "region", "province", "gadm", "adm0", "adm1", "adm2", "woreda"),
    "population": ("population", "pop", "worldpop", "density", "settlement"),
    "livestock": ("livestock", "cattle", "pasture", "rangeland", "herd"),
    "crop": ("crop", "yield", "maize", "agriculture", "cropland", "harvest", "planting"),
}

TOKEN_RE = re.compile(r"[a-z0-9]+")

#: Words too generic to identify a dataset on their own.
NOISE = {"geonode", "layer", "data", "dataset", "map", "raster", "vector",
         "the", "and", "of", "for", "in", "on", "a", "an", "with", "by"}


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def concepts_in(text: str) -> set[str]:
    """Concepts present in ``text``.

    Single-word synonyms match whole tokens, not substrings - otherwise the
    rainfall synonym "mm" hits "summer" and "community", and every third
    layer looks like a rainfall product.
    """
    lowered = (text or "").lower()
    present = set(tokens(lowered))
    found: set[str] = set()
    for concept, words in CONCEPTS.items():
        for word in words:
            hit = (word in lowered) if " " in word else (word in present)
            if hit:
                found.add(concept)
                break
    return found


@dataclass
class Hit:
    """One search result, with why it matched."""

    layer: Layer
    score: float
    quality: str          # strong | partial | weak
    matched_tokens: list[str] = field(default_factory=list)
    matched_concepts: list[str] = field(default_factory=list)


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
        """Look a layer up by full id, bare name, or unambiguous suffix.

        Matching is done on :attr:`Layer.key`, so a WCS coverage id
        (``ws__layer``) and its WMS/WFS name (``ws:layer``) resolve to the
        same dataset.
        """
        if layer_id in self.layers:
            return self.layers[layer_id]
        wanted = layer_id.replace("__", ":").lower()

        exact = [
            layer for layer in self.layers.values()
            if layer.key == wanted or layer.id.replace("__", ":").lower() == wanted
        ]
        if exact:
            return _prefer(exact)

        # "rfe_dekad" should find "icpac:workspace:rfe_dekad"
        tail = wanted.rsplit(":", 1)[-1]
        suffix = [
            layer for layer in self.layers.values()
            if layer.key.rsplit(":", 1)[-1] == tail
        ]
        return _prefer(suffix) if suffix else None

    def siblings(self, layer: Layer) -> dict[str, Layer]:
        """The same dataset as published by each service."""
        out: dict[str, Layer] = {}
        for other in self.layers.values():
            if other.key == layer.key and other.endpoint == layer.endpoint:
                out[other.service] = other
        return out

    def search(self, query: str, *, limit: int = 15, service: str = "") -> list[Hit]:
        """Rank layers against a free-text query.

        Direct token overlap dominates. A layer matching only by concept -
        no word in common with the query - is kept but heavily discounted
        and labelled "weak", because against a catalogue of several hundred
        layers those otherwise float to the top and read as real answers.
        """
        query_tokens = set(tokens(query)) - NOISE
        query_concepts = concepts_in(query)
        if not query_tokens:
            return []

        hits: list[Hit] = []
        for layer in self.layers.values():
            if service and layer.service != service.upper():
                continue

            haystack = layer.searchable_text
            layer_tokens = set(tokens(haystack)) - NOISE
            overlap = query_tokens & layer_tokens
            shared_concepts = query_concepts & concepts_in(haystack)
            if not overlap and not shared_concepts:
                continue

            token_share = len(overlap) / max(1, len(query_tokens))
            concept_share = len(shared_concepts) / max(1, len(query_concepts))

            score = 6.0 * token_share + 1.5 * concept_share
            if query.lower().strip() in (layer.title or "").lower():
                score += 4.0                      # whole phrase in the title
            score += 0.6 * sum(1 for t in overlap if t in layer.name.lower())
            if layer.temporal:
                score += 0.4                      # live-feed questions want time
            if layer.service == "WCS":
                score += 0.3                      # real pixels beat rendered samples

            if token_share >= 0.5 or (overlap and shared_concepts):
                quality = "strong"
            elif overlap:
                quality = "partial"
            else:
                quality = "weak"
                score *= 0.25                     # never outrank a real word match

            hits.append(
                Hit(
                    layer=layer,
                    score=round(score, 3),
                    quality=quality,
                    matched_tokens=sorted(overlap),
                    matched_concepts=sorted(shared_concepts),
                )
            )

        hits.sort(key=lambda hit: (-hit.score, hit.layer.id))
        return hits[:limit]

    def vocabulary(self, limit: int = 30) -> list[str]:
        """The most common meaningful words across published layer names.

        With several hundred layers a failed search is usually a vocabulary
        mismatch, so this gives the caller something concrete to retry with.
        """
        counter: Counter[str] = Counter()
        for layer in self.layers.values():
            counter.update(
                t for t in set(tokens(f"{layer.name} {layer.title}"))
                if t not in NOISE and len(t) > 2 and not t.isdigit()
            )
        return [word for word, _ in counter.most_common(limit)]


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
