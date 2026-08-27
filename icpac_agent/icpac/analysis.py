"""Statistics, anomalies and comparison over live ICPAC layers.

The agent's job is not to hand an LLM a pile of pixels - it is to turn a
coverage into a defensible number with a stated method, a confidence, and
a severity class an analyst would recognise. Everything here reports how it
was computed, because a mean over a bounding box and a mean over a real
county boundary are not the same claim.
"""

from __future__ import annotations

import asyncio
import math
import statistics
import time

import numpy as np

from .catalog import Catalog
from .config import Endpoint, settings
from .models import (
    BBox,
    Layer,
    MetricResult,
    Place,
    SampleStats,
    SeriesPoint,
    SourceReport,
)
from .ogc.client import OGCClient, OGCError
from .ogc.wcs import HAVE_RASTERIO, fetch_coverage
from .ogc.wms import sample_grid

# --------------------------------------------------------------- families ---
#: Recognised indicator families, matched against layer name/title. The
#: family decides how a value is classified - an SPI of -1.8 and a VCI of
#: 18 are both "severe", but nothing generic could know that.
FAMILY_HINTS: dict[str, tuple[str, ...]] = {
    "spi": ("spi", "standardized precipitation", "standardised precipitation"),
    "spei": ("spei",),
    "vci": ("vci", "vegetation condition"),
    "vhi": ("vhi", "vegetation health"),
    "ndvi": ("ndvi", "vegetation index", "greenness"),
    "rainfall": ("rain", "rfe", "precip", "chirps", "tamsat", "pptn"),
    "rainfall_anomaly": ("rain anomaly", "rainfall anomaly", "precip anomaly",
                         "percent of normal", "pct of normal", "rfe anomaly"),
    "temperature": ("temp", "tmax", "tmin", "lst"),
    "flood": ("flood", "inundation", "discharge", "streamflow"),
}

UNIT_HINTS: dict[str, str] = {
    "rainfall": "mm", "rainfall_anomaly": "% of normal", "temperature": "°C",
    "spi": "sigma", "spei": "sigma", "vci": "index 0-100", "vhi": "index 0-100",
    "ndvi": "index -1..1",
}

#: (family, threshold, label) - first matching row wins, evaluated in order.
SEVERITY_RULES: dict[str, list[tuple[float, str, str]]] = {
    # "lt" rules fire when value < threshold; "gt" when value > threshold.
    "spi": [(-2.0, "lt", "extreme"), (-1.5, "lt", "high"), (-1.0, "lt", "moderate"),
            (-0.5, "lt", "low"), (2.0, "gt", "extreme"), (1.5, "gt", "high"),
            (1.0, "gt", "moderate")],
    "vci": [(10, "lt", "extreme"), (20, "lt", "high"), (35, "lt", "moderate"),
            (50, "lt", "low")],
    "vhi": [(15, "lt", "extreme"), (25, "lt", "high"), (35, "lt", "moderate"),
            (50, "lt", "low")],
    "rainfall_anomaly": [(25, "lt", "extreme"), (50, "lt", "high"), (75, "lt", "moderate"),
                         (90, "lt", "low"), (200, "gt", "extreme"), (150, "gt", "high"),
                         (125, "gt", "moderate")],
}
SEVERITY_RULES["spei"] = SEVERITY_RULES["spi"]


def detect_family(layer: Layer) -> str:
    text = f"{layer.name} {layer.title} {layer.abstract}".lower()
    # Longest hint first so "rainfall anomaly" beats "rain".
    ordered = sorted(
        ((family, hint) for family, hints in FAMILY_HINTS.items() for hint in hints),
        key=lambda pair: -len(pair[1]),
    )
    for family, hint in ordered:
        if hint in text:
            return family
    return "generic"


def classify(family: str, value: float | None, anomaly_pct: float | None = None) -> str:
    if value is None:
        return "unknown"

    rules = SEVERITY_RULES.get(family)
    if rules is None and anomaly_pct is not None:
        rules, value = SEVERITY_RULES["rainfall_anomaly"], anomaly_pct
    if rules is None:
        return "unknown"

    for threshold, direction, label in rules:
        if direction == "lt" and value < threshold:
            return label
        if direction == "gt" and value > threshold:
            return label
    return "none"


# ------------------------------------------------------------- statistics ---

def summarise(
    values: list[float], attempted: int, *, method: str, units: str = "", note: str = ""
) -> SampleStats:
    stats = SampleStats(
        layer="", place="", count=attempted, valid=len(values),
        units=units, method=method, note=note,  # type: ignore[arg-type]
    )
    if not values:
        return stats

    array = np.asarray(values, dtype="float64")
    array = array[np.isfinite(array)]
    if array.size == 0:
        stats.valid = 0
        return stats

    stats.valid = int(array.size)
    stats.mean = float(np.mean(array))
    stats.minimum = float(np.min(array))
    stats.maximum = float(np.max(array))
    stats.stdev = float(np.std(array)) if array.size > 1 else 0.0
    stats.median = float(np.median(array))
    stats.p10 = float(np.percentile(array, 10))
    stats.p90 = float(np.percentile(array, 90))
    return stats


def confidence(stats: SampleStats, series_length: int = 0) -> float:
    """0-1 from sample coverage, absolute sample size and series depth."""
    if not stats.usable:
        return 0.0
    coverage = stats.valid / max(1, stats.count)
    volume = min(1.0, math.log1p(stats.valid) / math.log(1000))
    depth = min(1.0, series_length / 12) if series_length else 0.5
    method_weight = 1.0 if stats.method == "wcs-coverage" else 0.75
    return round(min(1.0, (0.45 * coverage + 0.35 * volume + 0.20 * depth) * method_weight), 3)


def trend_per_step(series: list[SeriesPoint]) -> float | None:
    """Least-squares slope per time step over the valid points."""
    points = [(i, p.value) for i, p in enumerate(series) if p.value is not None]
    if len(points) < 3:
        return None
    xs = np.asarray([p[0] for p in points], dtype="float64")
    ys = np.asarray([p[1] for p in points], dtype="float64")
    slope = float(np.polyfit(xs, ys, 1)[0])
    return round(slope, 6)


# ----------------------------------------------------------- data reading ---

def _endpoint_for(layer: Layer) -> Endpoint | None:
    return next((e for e in settings.endpoints if e.name == layer.endpoint), None)


async def sample_place(
    client: OGCClient,
    catalog: Catalog,
    layer: Layer,
    place: Place,
    *,
    time_value: str = "",
    prefer: str = "auto",
) -> tuple[SampleStats, SourceReport]:
    """Read ``layer`` over ``place``. Prefers WCS pixels, falls back to WMS.

    ``prefer`` is "auto" (WCS then WMS), "wcs" or "wms".
    """
    started = time.perf_counter()
    family = detect_family(layer)
    units = UNIT_HINTS.get(family, "")

    def report(status: str, detail: str, service: str) -> SourceReport:
        return SourceReport(
            endpoint=layer.endpoint, service=service, layer=layer.id,
            status=status, detail=detail,  # type: ignore[arg-type]
            elapsed_ms=int((time.perf_counter() - started) * 1000),
        )

    siblings = catalog.siblings(layer)
    stamp = time_value or layer.time_default

    # ---- WCS: real pixels -------------------------------------------
    if prefer in {"auto", "wcs"} and HAVE_RASTERIO:
        wcs_layer = siblings.get("WCS") or (layer if layer.service == "WCS" else None)
        endpoint = _endpoint_for(wcs_layer) if wcs_layer else None
        if wcs_layer and endpoint:
            try:
                values, pixels = await fetch_coverage(
                    client, endpoint, wcs_layer, place.bbox, time=stamp
                )
                stats = summarise(
                    values, pixels, method="wcs-coverage", units=units,
                    note="" if place.source.startswith("wfs")
                    else "extent is an approximate bounding box, not the exact boundary",
                )
                stats.layer, stats.place, stats.time = layer.id, place.name, stamp
                if stats.usable:
                    return stats, report("ok", f"{stats.valid}/{pixels} pixels", "WCS")
            except OGCError as exc:
                if prefer == "wcs":
                    empty = SampleStats(layer=layer.id, place=place.name, time=stamp,
                                        method="wcs-coverage", units=units)
                    return empty, report("error", str(exc), "WCS")

    # ---- WMS: sampled from the rendered layer ------------------------
    if prefer in {"auto", "wms"}:
        wms_layer = siblings.get("WMS") or (layer if layer.service == "WMS" else None)
        endpoint = _endpoint_for(wms_layer) if wms_layer else None
        if wms_layer and endpoint:
            try:
                values, attempted = await sample_grid(
                    client, endpoint, wms_layer, place.bbox, time=stamp
                )
                note = "sampled from the rendered layer via GetFeatureInfo"
                if not HAVE_RASTERIO:
                    note += "; install rasterio for true WCS zonal statistics"
                stats = summarise(values, attempted, method="wms-sample",
                                  units=units, note=note)
                stats.layer, stats.place, stats.time = layer.id, place.name, stamp
                status = "ok" if stats.usable else "empty"
                return stats, report(
                    status, f"{stats.valid}/{attempted} sample points", "WMS"
                )
            except OGCError as exc:
                empty = SampleStats(layer=layer.id, place=place.name, time=stamp,
                                    method="wms-sample", units=units)
                return empty, report("error", str(exc), "WMS")

    empty = SampleStats(layer=layer.id, place=place.name, time=stamp, units=units)
    return empty, report("skipped", "layer offers no readable WCS or WMS service", layer.service)


async def time_series(
    client: OGCClient,
    catalog: Catalog,
    layer: Layer,
    place: Place,
    times: list[str],
) -> tuple[list[SeriesPoint], list[SourceReport]]:
    """Sample one place across several time steps, concurrently."""
    gate = asyncio.Semaphore(settings.concurrency)

    async def one(stamp: str) -> tuple[SeriesPoint, SourceReport]:
        async with gate:
            stats, report = await sample_place(client, catalog, layer, place, time_value=stamp)
        return SeriesPoint(time=stamp, value=stats.mean, valid=stats.valid), report

    results = await asyncio.gather(*(one(t) for t in times))
    return [r[0] for r in results], [r[1] for r in results]


def baseline_from(series: list[SeriesPoint], exclude: str = "") -> float | None:
    values = [p.value for p in series if p.value is not None and p.time != exclude]
    return statistics.fmean(values) if values else None


def build_metric(
    place: Place,
    stats: SampleStats,
    family: str,
    *,
    baseline: float | None = None,
    series: list[SeriesPoint] | None = None,
) -> MetricResult:
    """Assemble one comparable indicator from a sample plus optional history."""
    anomaly = anomaly_pct = None
    if baseline is not None and stats.mean is not None:
        anomaly = round(stats.mean - baseline, 4)
        if abs(baseline) > 1e-9:
            anomaly_pct = round(100.0 * stats.mean / baseline, 2)

    evidence = [
        f"{stats.valid} of {stats.count} samples valid via {stats.method}",
        f"range {stats.minimum:.3g} to {stats.maximum:.3g}"
        if stats.minimum is not None else "no valid samples",
    ]
    if stats.note:
        evidence.append(stats.note)
    if place.source.startswith("wfs"):
        evidence.append(f"extent from {place.source}")
    else:
        evidence.append("extent from the built-in gazetteer (approximate box)")

    return MetricResult(
        place=place.name,
        metric=family,
        value=round(stats.mean, 4) if stats.mean is not None else None,
        units=stats.units,
        severity=classify(family, stats.mean, anomaly_pct),  # type: ignore[arg-type]
        baseline=round(baseline, 4) if baseline is not None else None,
        anomaly=anomaly,
        anomaly_pct=anomaly_pct,
        trend_per_step=trend_per_step(series) if series else None,
        confidence=confidence(stats, len(series or [])),
        method=stats.method,
        evidence=evidence,
    )


# ------------------------------------------------------------- narration ---

SEVERITY_ORDER = {"extreme": 4, "high": 3, "moderate": 2, "low": 1, "none": 0, "unknown": -1}

#: Families where a *lower* value is the worse condition.
LOWER_IS_WORSE = {"spi", "spei", "vci", "vhi", "ndvi", "rainfall", "rainfall_anomaly"}


def rank_metrics(results: list[MetricResult], family: str) -> list[MetricResult]:
    """Rank by severity of condition, not by raw magnitude."""
    scored = [r for r in results if r.value is not None]
    missing = [r for r in results if r.value is None]

    reverse = family not in LOWER_IS_WORSE
    scored.sort(key=lambda r: (r.value if r.value is not None else 0.0), reverse=reverse)
    for i, result in enumerate(scored, start=1):
        result.rank = i
    for result in missing:
        result.rank = 0
    return scored + missing


def narrate(
    layer: Layer, family: str, results: list[MetricResult], stamp: str, units: str
) -> str:
    usable = [r for r in results if r.value is not None]
    if not usable:
        return (
            f"No usable values were returned for {layer.title or layer.name} over the "
            f"requested areas. The run log shows what each service replied."
        )

    label = layer.title or layer.name
    when = f" for {stamp}" if stamp else ""
    unit = f" {units}" if units else ""

    worst, best = usable[0], usable[-1]
    lines = [
        f"{label}{when}: {worst.place} is the most affected at "
        f"{worst.value:.3g}{unit}"
        + (f" ({worst.severity})" if worst.severity not in {"unknown", "none"} else "")
        + f", {best.place} the least at {best.value:.3g}{unit}."
    ]

    if len(usable) > 2:
        middle = ", ".join(f"{r.place} {r.value:.3g}" for r in usable[1:-1][:6])
        if middle:
            lines.append(f"Between them: {middle}.")

    flagged = [r for r in usable if SEVERITY_ORDER.get(r.severity, -1) >= 3]
    if flagged:
        lines.append(
            "Above the alert threshold: "
            + ", ".join(f"{r.place} ({r.severity})" for r in flagged)
            + "."
        )

    with_anomaly = [r for r in usable if r.anomaly_pct is not None]
    if with_anomaly:
        driest = min(with_anomaly, key=lambda r: r.anomaly_pct or 0)
        lines.append(
            f"Against its own recent baseline, {driest.place} sits at "
            f"{driest.anomaly_pct:.0f}% of normal."
        )

    trending = [r for r in usable if r.trend_per_step is not None]
    if trending:
        steepest = min(trending, key=lambda r: r.trend_per_step or 0)
        direction = "falling" if (steepest.trend_per_step or 0) < 0 else "rising"
        lines.append(
            f"{steepest.place} shows the steepest {direction} trend "
            f"({steepest.trend_per_step:+.3g}{unit} per step)."
        )

    mean_conf = statistics.fmean([r.confidence for r in usable])
    approximate = sum(1 for r in usable if "gazetteer" in " ".join(r.evidence))
    caveat = (
        f" {approximate} of {len(usable)} extents came from the built-in gazetteer, "
        "so those figures cover an approximate box rather than the exact boundary."
        if approximate else ""
    )
    lines.append(f"Mean confidence {mean_conf:.2f}.{caveat}")
    return " ".join(lines)
