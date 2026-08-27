"""Types shared by the OGC clients, the analysis layer and the MCP tools."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

ServiceKind = Literal["WMS", "WFS", "WCS"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BBox(BaseModel):
    """Bounding box in EPSG:4326, always (west, south, east, north)."""

    west: float
    south: float
    east: float
    north: float

    @classmethod
    def from_list(cls, values: list[float] | tuple[float, ...]) -> "BBox":
        w, s, e, n = values
        return cls(west=w, south=s, east=e, north=n)

    def as_list(self) -> list[float]:
        return [self.west, self.south, self.east, self.north]

    def as_str(self) -> str:
        return ",".join(f"{v:.6f}" for v in self.as_list())

    @property
    def centre(self) -> tuple[float, float]:
        return ((self.west + self.east) / 2, (self.south + self.north) / 2)

    @property
    def width(self) -> float:
        return abs(self.east - self.west)

    @property
    def height(self) -> float:
        return abs(self.north - self.south)

    def contains(self, lon: float, lat: float) -> bool:
        return self.west <= lon <= self.east and self.south <= lat <= self.north

    def intersects(self, other: "BBox") -> bool:
        return not (
            self.east < other.west
            or self.west > other.east
            or self.north < other.south
            or self.south > other.north
        )

    def buffered(self, factor: float = 0.05) -> "BBox":
        dx, dy = self.width * factor, self.height * factor
        return BBox(
            west=self.west - dx, south=self.south - dy,
            east=self.east + dx, north=self.north + dy,
        )


class Layer(BaseModel):
    """One published OGC layer, normalised across WMS/WFS/WCS."""

    id: str                                  # endpoint-qualified: "icpac:rfe_dekad"
    name: str                                # server-side layer name
    endpoint: str
    service: ServiceKind
    title: str = ""
    abstract: str = ""
    keywords: list[str] = Field(default_factory=list)
    bbox: BBox | None = None
    crs: list[str] = Field(default_factory=list)
    time_values: list[str] = Field(default_factory=list)
    time_default: str = ""
    styles: list[str] = Field(default_factory=list)
    formats: list[str] = Field(default_factory=list)
    queryable: bool = False

    @property
    def searchable_text(self) -> str:
        return " ".join([self.name, self.title, self.abstract, " ".join(self.keywords)]).lower()

    @property
    def temporal(self) -> bool:
        return bool(self.time_values or self.time_default)

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "service": self.service,
            "title": self.title or self.name,
            "endpoint": self.endpoint,
            "temporal": self.temporal,
            "times": len(self.time_values),
            "latest_time": self.time_values[-1] if self.time_values else self.time_default,
            "bbox": self.bbox.as_list() if self.bbox else None,
        }


class Place(BaseModel):
    """A named area the agent can analyse."""

    name: str
    kind: str = "admin"          # admin | country | basin | point | custom
    country: str = ""
    bbox: BBox
    source: str = "gazetteer"    # gazetteer | wfs | user

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name, "kind": self.kind, "country": self.country,
            "bbox": self.bbox.as_list(), "source": self.source,
        }


class SampleStats(BaseModel):
    """Summary statistics for one layer over one area at one time."""

    layer: str
    place: str
    time: str = ""
    count: int = 0
    valid: int = 0
    mean: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    stdev: float | None = None
    p10: float | None = None
    median: float | None = None
    p90: float | None = None
    units: str = ""
    method: Literal["wcs-coverage", "wms-sample", "wfs-features"] = "wms-sample"
    note: str = ""

    @property
    def usable(self) -> bool:
        return self.valid > 0 and self.mean is not None


class SeriesPoint(BaseModel):
    time: str
    value: float | None = None
    valid: int = 0


class MetricResult(BaseModel):
    """One computed indicator for one place - the unit of comparison."""

    place: str
    metric: str
    value: float | None = None
    units: str = ""
    rank: int = 0
    severity: Literal["none", "low", "moderate", "high", "extreme", "unknown"] = "unknown"
    baseline: float | None = None
    anomaly: float | None = None
    anomaly_pct: float | None = None
    trend_per_step: float | None = None
    confidence: float = 0.0       # 0-1, from sample coverage and series length
    method: str = ""
    evidence: list[str] = Field(default_factory=list)


class SourceReport(BaseModel):
    """What each live feed did during a call - always returned to the caller."""

    endpoint: str
    service: str
    layer: str = ""
    status: Literal["ok", "empty", "error", "skipped"] = "ok"
    detail: str = ""
    elapsed_ms: int = 0
    cached: bool = False


class AnalysisResult(BaseModel):
    """The full answer to one question, with provenance attached."""

    question: str = ""
    layer: str = ""
    layer_title: str = ""
    metric: str = ""
    time: str = ""
    units: str = ""
    places: list[MetricResult] = Field(default_factory=list)
    narrative: str = ""
    sources: list[SourceReport] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utcnow)

    @property
    def ok(self) -> bool:
        return any(p.value is not None for p in self.places)
