"""WFS access: vector features as GeoJSON.

Used for two jobs: reading hazard/alert polygons and station points as
data, and resolving administrative boundaries so a question about "Turkana"
is answered over the county's real extent rather than a guessed box.
"""

from __future__ import annotations

import json
from typing import Any

from ..config import Endpoint
from ..models import BBox, Layer
from .client import OGCClient, OGCError

#: GeoServer accepts several spellings of the GeoJSON output format.
JSON_FORMATS = ("application/json", "json", "GEOJSON", "application/geo+json")


def _params(layer: Layer, version: str, limit: int) -> dict[str, Any]:
    count_key = "count" if version.startswith("2") else "maxFeatures"
    type_key = "typeNames" if version.startswith("2") else "typeName"
    return {
        "service": "WFS",
        "version": version,
        "request": "GetFeature",
        type_key: layer.name,
        count_key: limit,
        "srsName": "EPSG:4326",
    }


async def fetch_features(
    client: OGCClient,
    endpoint: Endpoint,
    layer: Layer,
    *,
    bbox: BBox | None = None,
    cql_filter: str = "",
    limit: int = 200,
    properties: str = "",
) -> dict[str, Any]:
    """Fetch features as a GeoJSON FeatureCollection.

    Tries WFS 2.0.0 then 1.1.0, and each supported GeoJSON format spelling,
    because which combination works varies by server version.
    """
    last_error = ""
    for version in ("2.0.0", "1.1.0"):
        base = _params(layer, version, limit)
        if bbox is not None:
            base["bbox"] = f"{bbox.as_str()},EPSG:4326"
        if cql_filter:
            base["cql_filter"] = cql_filter
        if properties:
            base["propertyName"] = properties

        for output_format in JSON_FORMATS:
            try:
                body, _ = await client.get(
                    endpoint, {**base, "outputFormat": output_format}
                )
            except OGCError as exc:
                last_error = str(exc)
                continue
            try:
                payload = json.loads(body.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                last_error = "response was not valid JSON"
                continue
            if isinstance(payload, dict) and "features" in payload:
                return payload

    raise OGCError(last_error or "no WFS version/format combination returned GeoJSON")


def geometry_bbox(geometry: dict[str, Any]) -> BBox | None:
    """Bounding box of any GeoJSON geometry, without a geometry library."""
    xs: list[float] = []
    ys: list[float] = []

    def walk(node: Any) -> None:
        if isinstance(node, (list, tuple)):
            if (
                len(node) >= 2
                and isinstance(node[0], (int, float))
                and isinstance(node[1], (int, float))
            ):
                xs.append(float(node[0]))
                ys.append(float(node[1]))
            else:
                for item in node:
                    walk(item)

    if not isinstance(geometry, dict):
        return None
    if geometry.get("type") == "GeometryCollection":
        for geom in geometry.get("geometries", []):
            walk(geom.get("coordinates"))
    else:
        walk(geometry.get("coordinates"))

    if not xs or not ys:
        return None
    return BBox(west=min(xs), south=min(ys), east=max(xs), north=max(ys))


def numeric_property(feature: dict[str, Any], names: tuple[str, ...]) -> float | None:
    """First numeric property matching one of ``names`` (case-insensitive)."""
    props = feature.get("properties") or {}
    lowered = {k.lower(): v for k, v in props.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None
