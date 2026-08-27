"""The MCP tool surface.

Ten tools, arranged so a model can go from a plain question to a defensible
answer without knowing any ICPAC layer names in advance: discover what is
published, resolve the places, read the values, compare and rank them.

Every tool returns its ``sources`` - which endpoint answered, with what
status and how fast - so an answer can always be traced back to the feed
it came from.
"""

from __future__ import annotations

import asyncio
import base64
from typing import Any

from . import __version__
from .analysis import (
    baseline_from,
    build_metric,
    detect_family,
    narrate,
    rank_metrics,
    sample_place,
    time_series,
)
from .catalog import Catalog, cached_catalog, load_catalog, reset_cache
from .config import Endpoint, settings
from .geo import REGION_BBOX, resolve_place
from .models import AnalysisResult, BBox, Layer, Place, SourceReport
from .ogc.client import OGCClient, OGCError
from .ogc.wfs import fetch_features
from .ogc.wms import get_map

INSTRUCTIONS = """\
Live climate and hazard analysis over ICPAC's OGC feeds (WMS/WFS/WCS).

Typical flow:
  1. search_layers("rainfall anomaly")   - find what is actually published
  2. describe_layer(<id>)                - check time steps and extent
  3. compare_places(<id>, ["Turkana", "Marsabit", "Wajir"]) - rank areas

Notes that matter for interpretation:
  - Values come from live servers; nothing is cached longer than a few minutes.
  - Every reading reports its method. "wcs-coverage" reads source pixels;
    "wms-sample" samples the rendered layer on a coarse grid and is less exact.
  - Place extents resolved from WFS boundaries are exact; gazetteer extents
    are approximate rectangles. Each result says which was used.
  - Severity classes follow the indicator family (SPI, VCI, % of normal).
    A family the agent does not recognise returns severity "unknown" rather
    than a guess.
"""


# ------------------------------------------------------------- plumbing ---

async def _with_client(fn):
    """Run one tool body against a fresh OGC client."""
    async with OGCClient.create() as client:
        catalog = await load_catalog(client)
        return await fn(client, catalog)


def _endpoint_for(layer: Layer) -> Endpoint | None:
    return next((e for e in settings.endpoints if e.name == layer.endpoint), None)


def _not_configured() -> dict[str, Any]:
    return {
        "error": "no ICPAC endpoints configured",
        "fix": "set ICPAC_ENDPOINTS (or ICPAC_OGC_URL) to your GeoServer/GeoNode OWS URL",
        "example": "ICPAC_ENDPOINTS=geoportal=https://geoportal.icpac.net/geoserver/ows",
    }


def _layer_missing(layer_id: str, catalog: Catalog) -> dict[str, Any]:
    suggestions = [layer.id for layer, _ in catalog.search(layer_id, limit=5)]
    return {
        "error": f"no published layer matches {layer_id!r}",
        "did_you_mean": suggestions,
        "hint": "call search_layers first; ids come from the live capabilities documents",
    }


def _reports(items: list[SourceReport]) -> list[dict[str, Any]]:
    return [r.model_dump() for r in items]


# ---------------------------------------------------------------- tools ---

def register(server: Any) -> Any:
    """Attach every tool to an MCP server instance."""

    # -- discovery ----------------------------------------------------
    @server.tool(
        name="list_endpoints",
        description=(
            "List the configured ICPAC OGC endpoints and whether each service "
            "(WMS/WFS/WCS) is currently answering. Use this first when something "
            "returns no data, to tell a configuration problem from an outage."
        ),
    )
    async def list_endpoints() -> dict[str, Any]:
        if not settings.configured:
            return _not_configured()

        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            counts: dict[str, int] = {}
            for layer in catalog.layers.values():
                counts[f"{layer.endpoint}/{layer.service}"] = (
                    counts.get(f"{layer.endpoint}/{layer.service}", 0) + 1
                )
            return {
                "agent_version": __version__,
                "endpoints": [
                    {"name": e.name, "url": e.url, "services": list(e.services),
                     "authenticated": bool(e.auth or e.token)}
                    for e in settings.endpoints
                ],
                "layer_counts": counts,
                "total_layers": len({layer.id for layer in catalog.layers.values()}),
                "sources": _reports(catalog.reports),
            }

        return await _with_client(body)

    @server.tool(
        name="search_layers",
        description=(
            "Search live ICPAC capabilities for layers matching a description, "
            "e.g. 'rainfall anomaly', 'NDVI', 'flood hazard', 'county boundaries'. "
            "Returns ranked layer ids to pass to the other tools. Always search "
            "before assuming a layer name exists."
        ),
    )
    async def search_layers(
        query: str, service: str = "", limit: int = 12
    ) -> dict[str, Any]:
        if not settings.configured:
            return _not_configured()

        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            hits = catalog.search(query, limit=max(1, min(limit, 50)), service=service)
            return {
                "query": query,
                "matches": [
                    {**layer.summary(), "score": score, "family": detect_family(layer)}
                    for layer, score in hits
                ],
                "total_indexed": len({layer.id for layer in catalog.layers.values()}),
                "sources": _reports(catalog.reports),
            }

        return await _with_client(body)

    @server.tool(
        name="describe_layer",
        description=(
            "Full metadata for one layer: title, abstract, spatial extent, CRSs, "
            "available time steps, styles, and which services publish it. Check "
            "this before requesting a specific time."
        ),
    )
    async def describe_layer(layer_id: str, max_times: int = 24) -> dict[str, Any]:
        if not settings.configured:
            return _not_configured()

        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            layer = catalog.get(layer_id)
            if layer is None:
                return _layer_missing(layer_id, catalog)

            siblings = catalog.siblings(layer)
            # One dataset, several services: merge the time axis so a WCS-only
            # capabilities document does not hide the steps WMS advertises.
            times = layer.time_values or next(
                (s.time_values for s in siblings.values() if s.time_values), []
            )
            return {
                "id": layer.id,
                "name": layer.name,
                "title": layer.title,
                "abstract": layer.abstract,
                "endpoint": layer.endpoint,
                "services": sorted(siblings),
                "family": detect_family(layer),
                "keywords": layer.keywords,
                "bbox": layer.bbox.as_list() if layer.bbox else None,
                "crs": layer.crs,
                "styles": layer.styles,
                "queryable": layer.queryable,
                "temporal": layer.temporal,
                "time_count": len(times),
                "time_default": layer.time_default,
                "time_first": times[0] if times else "",
                "time_latest": times[-1] if times else "",
                "time_recent": times[-max_times:] if times else [],
                "readable_pixels": "WCS" in siblings,
            }

        return await _with_client(body)

    @server.tool(
        name="refresh_catalog",
        description=(
            "Force a re-read of every GetCapabilities document. Use after a layer "
            "is published or a feed is restored; the catalogue is otherwise cached."
        ),
    )
    async def refresh_catalog() -> dict[str, Any]:
        if not settings.configured:
            return _not_configured()
        reset_cache()

        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            fresh = await load_catalog(client, force=True)
            return {
                "refreshed": True,
                "total_layers": len({layer.id for layer in fresh.layers.values()}),
                "sources": _reports(fresh.reports),
            }

        return await _with_client(body)

    # -- geography ----------------------------------------------------
    @server.tool(
        name="resolve_place",
        description=(
            "Resolve a place name (county, region, country, basin) to an extent. "
            "Prefers exact boundaries from published WFS admin layers and falls "
            "back to a built-in Greater Horn gazetteer, reporting which was used. "
            "Also accepts 'lon,lat' or 'west,south,east,north'."
        ),
    )
    async def resolve_place_tool(name: str, prefer_boundaries: bool = True) -> dict[str, Any]:
        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            place = await resolve_place(client, catalog, name, prefer_wfs=prefer_boundaries)
            if place is None:
                return {
                    "error": f"could not resolve {name!r}",
                    "hint": "try the admin unit's official name, or pass coordinates "
                            "as 'lon,lat' or 'west,south,east,north'",
                    "region_covered": REGION_BBOX.as_list(),
                }
            return {
                **place.summary(),
                "exact_boundary": place.source.startswith("wfs"),
                "caveat": "" if place.source.startswith("wfs")
                else "approximate bounding box from the built-in gazetteer",
            }

        return await _with_client(body)

    # -- reading values ------------------------------------------------
    @server.tool(
        name="get_layer_value",
        description=(
            "Read one layer's statistics over one place at one time: mean, min, "
            "max, median, percentiles, and how many samples were valid. Prefers "
            "true WCS pixels and falls back to WMS sampling, reporting which."
        ),
    )
    async def get_layer_value(
        layer_id: str, place: str, time: str = "", prefer: str = "auto"
    ) -> dict[str, Any]:
        if not settings.configured:
            return _not_configured()

        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            layer = catalog.get(layer_id)
            if layer is None:
                return _layer_missing(layer_id, catalog)
            resolved = await resolve_place(client, catalog, place)
            if resolved is None:
                return {"error": f"could not resolve place {place!r}"}

            stats, report = await sample_place(
                client, catalog, layer, resolved, time_value=time, prefer=prefer
            )
            family = detect_family(layer)
            metric = build_metric(resolved, stats, family)
            return {
                "layer": layer.id,
                "layer_title": layer.title or layer.name,
                "family": family,
                "place": resolved.summary(),
                "time": stats.time,
                "statistics": stats.model_dump(),
                "metric": metric.model_dump(),
                "sources": _reports([report]),
            }

        return await _with_client(body)

    @server.tool(
        name="layer_time_series",
        description=(
            "Sample one layer over one place across its most recent time steps. "
            "Returns the series, the mean baseline, and the fitted trend per step "
            "- the basis for saying whether a situation is improving or worsening."
        ),
    )
    async def layer_time_series(
        layer_id: str, place: str, steps: int = 12
    ) -> dict[str, Any]:
        if not settings.configured:
            return _not_configured()

        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            layer = catalog.get(layer_id)
            if layer is None:
                return _layer_missing(layer_id, catalog)
            if not layer.time_values:
                return {
                    "error": f"{layer.id} advertises no time dimension",
                    "hint": "use get_layer_value for a static layer",
                }
            resolved = await resolve_place(client, catalog, place)
            if resolved is None:
                return {"error": f"could not resolve place {place!r}"}

            stamps = layer.time_values[-max(2, min(steps, 60)):]
            series, reports = await time_series(client, catalog, layer, resolved, stamps)
            family = detect_family(layer)
            latest = series[-1] if series else None
            baseline = baseline_from(series, exclude=latest.time if latest else "")

            from .analysis import trend_per_step

            return {
                "layer": layer.id,
                "layer_title": layer.title or layer.name,
                "family": family,
                "place": resolved.summary(),
                "steps_requested": len(stamps),
                "series": [p.model_dump() for p in series],
                "latest": latest.model_dump() if latest else None,
                "baseline_mean": round(baseline, 4) if baseline is not None else None,
                "trend_per_step": trend_per_step(series),
                "sources": _reports(reports),
            }

        return await _with_client(body)

    @server.tool(
        name="compare_places",
        description=(
            "Rank several places on one layer - the main analysis tool. Reads each "
            "area from the live feed, optionally computes an anomaly against that "
            "area's own recent history, classifies severity by indicator family "
            "(SPI, VCI, % of normal), ranks worst-affected first and writes a "
            "plain-language summary. Example: compare_places('icpac:spi_3month', "
            "['Turkana','Marsabit','Wajir','Mandera'])."
        ),
    )
    async def compare_places(
        layer_id: str,
        places: list[str],
        time: str = "",
        baseline_steps: int = 0,
        question: str = "",
    ) -> dict[str, Any]:
        if not settings.configured:
            return _not_configured()
        if not places:
            return {"error": "give at least one place name"}

        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            layer = catalog.get(layer_id)
            if layer is None:
                return _layer_missing(layer_id, catalog)

            family = detect_family(layer)
            stamp = time or layer.time_default or (
                layer.time_values[-1] if layer.time_values else ""
            )
            result = AnalysisResult(
                question=question, layer=layer.id,
                layer_title=layer.title or layer.name, metric=family, time=stamp,
            )

            resolved: list[Place] = []
            for name in places[:20]:
                place = await resolve_place(client, catalog, name)
                if place is None:
                    result.warnings.append(f"could not resolve {name!r}; skipped")
                    continue
                resolved.append(place)
            if not resolved:
                result.warnings.append("no places could be resolved")
                result.narrative = "None of the requested places could be resolved to an extent."
                return result.model_dump(mode="json")

            gate = asyncio.Semaphore(settings.concurrency)

            async def one(place: Place):
                async with gate:
                    stats, report = await sample_place(
                        client, catalog, layer, place, time_value=stamp
                    )
                series = []
                baseline = None
                if baseline_steps > 1 and layer.time_values:
                    history = [t for t in layer.time_values[-baseline_steps:] if t != stamp]
                    series, extra = await time_series(client, catalog, layer, place, history)
                    baseline = baseline_from(series)
                    return place, stats, report, series, baseline, extra
                return place, stats, report, series, baseline, []

            gathered = await asyncio.gather(*(one(p) for p in resolved))

            metrics = []
            for place, stats, report, series, baseline, extra in gathered:
                result.sources.append(report)
                result.sources.extend(extra)
                metrics.append(
                    build_metric(place, stats, family, baseline=baseline, series=series)
                )

            units = next((m.units for m in metrics if m.units), "")
            result.units = units
            result.places = rank_metrics(metrics, family)
            result.narrative = narrate(layer, family, result.places, stamp, units)

            unusable = [m.place for m in result.places if m.value is None]
            if unusable:
                result.warnings.append(
                    "no usable values for: " + ", ".join(unusable)
                    + " - check the run log for the service response"
                )
            return result.model_dump(mode="json")

        return await _with_client(body)

    # -- vector data ---------------------------------------------------
    @server.tool(
        name="get_features",
        description=(
            "Read vector features from a WFS layer as GeoJSON - hazard alert "
            "polygons, station points, administrative units. Optionally clipped "
            "to a place and filtered with CQL. Returns properties plus a compact "
            "summary rather than raw geometry, to stay readable."
        ),
    )
    async def get_features(
        layer_id: str,
        place: str = "",
        cql_filter: str = "",
        limit: int = 50,
        include_geometry: bool = False,
    ) -> dict[str, Any]:
        if not settings.configured:
            return _not_configured()

        async def body(client: OGCClient, catalog: Catalog) -> dict[str, Any]:
            layer = catalog.get(layer_id)
            if layer is None:
                return _layer_missing(layer_id, catalog)
            wfs = catalog.siblings(layer).get("WFS")
            if wfs is None:
                return {
                    "error": f"{layer.id} is not published via WFS",
                    "hint": "vector reads need a WFS layer; use get_layer_value for rasters",
                }
            endpoint = _endpoint_for(wfs)
            if endpoint is None:
                return {"error": f"endpoint {wfs.endpoint!r} is no longer configured"}

            bbox: BBox | None = None
            place_summary = None
            if place:
                resolved = await resolve_place(client, catalog, place)
                if resolved is None:
                    return {"error": f"could not resolve place {place!r}"}
                bbox, place_summary = resolved.bbox, resolved.summary()

            try:
                collection = await fetch_features(
                    client, endpoint, wfs, bbox=bbox,
                    cql_filter=cql_filter, limit=max(1, min(limit, 500)),
                )
            except OGCError as exc:
                return {
                    "error": str(exc),
                    "sources": _reports([
                        SourceReport(endpoint=wfs.endpoint, service="WFS",
                                     layer=wfs.id, status="error", detail=str(exc))
                    ]),
                }

            features = collection.get("features", [])
            rows = []
            for feature in features:
                row = {"properties": feature.get("properties") or {}}
                if include_geometry:
                    row["geometry"] = feature.get("geometry")
                rows.append(row)

            return {
                "layer": wfs.id,
                "place": place_summary,
                "filter": cql_filter,
                "returned": len(rows),
                "features": rows,
                "sources": _reports([
                    SourceReport(endpoint=wfs.endpoint, service="WFS", layer=wfs.id,
                                 status="ok" if rows else "empty",
                                 detail=f"{len(rows)} features")
                ]),
            }

        return await _with_client(body)

    # -- imagery -------------------------------------------------------
    @server.tool(
        name="render_map",
        description=(
            "Render a layer over a place as a PNG via WMS - visual context to "
            "accompany the numbers. Returns the image itself."
        ),
    )
    async def render_map(
        layer_id: str, place: str = "", time: str = "", style: str = "", width: int = 768
    ):
        if not settings.configured:
            return _not_configured()

        async def body(client: OGCClient, catalog: Catalog):
            layer = catalog.get(layer_id)
            if layer is None:
                return _layer_missing(layer_id, catalog)
            wms = catalog.siblings(layer).get("WMS")
            if wms is None:
                return {"error": f"{layer.id} is not published via WMS"}
            endpoint = _endpoint_for(wms)
            if endpoint is None:
                return {"error": f"endpoint {wms.endpoint!r} is no longer configured"}

            bbox = wms.bbox or REGION_BBOX
            if place:
                resolved = await resolve_place(client, catalog, place)
                if resolved is None:
                    return {"error": f"could not resolve place {place!r}"}
                bbox = resolved.bbox.buffered(0.08)

            try:
                image, content_type = await get_map(
                    client, endpoint, wms, bbox, time=time, style=style,
                    width=max(128, min(width, 2048)),
                )
            except OGCError as exc:
                return {"error": str(exc)}

            from .mcp_compat import ImageContent

            try:
                return ImageContent(data=image, format="png")
            except Exception:  # noqa: BLE001 - SDKs differ; fall back to base64
                return {
                    "layer": wms.id,
                    "content_type": content_type,
                    "bbox": bbox.as_list(),
                    "image_base64": base64.b64encode(image).decode(),
                }

        return await _with_client(body)

    return server
