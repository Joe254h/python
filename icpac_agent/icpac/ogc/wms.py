"""WMS access: rendered maps, point queries and grid sampling.

Grid sampling exists because GetFeatureInfo is the only value-reading
operation every WMS server supports. It costs one HTTP request per sample
point, so it is the *fallback*: when a layer is also published via WCS the
agent reads real pixels instead. The grid is deliberately coarse - it is
there to answer "roughly how wet is this county", not to replace zonal
statistics on the source raster.
"""

from __future__ import annotations

import asyncio
import json
import math
from typing import Any

from ..config import Endpoint, settings
from ..models import BBox, Layer
from .client import OGCClient, OGCError

INFO_FORMATS = ("application/json", "application/vnd.ogc.gml", "text/plain")


def _version_params(layer: Layer, bbox: BBox, width: int, height: int) -> dict[str, Any]:
    """WMS 1.3.0 flips axis order for EPSG:4326; CRS:84 keeps lon/lat."""
    return {
        "service": "WMS",
        "version": "1.1.1",
        "layers": layer.name,
        "srs": "EPSG:4326",
        "bbox": bbox.as_str(),
        "width": width,
        "height": height,
    }


async def get_map(
    client: OGCClient,
    endpoint: Endpoint,
    layer: Layer,
    bbox: BBox,
    *,
    width: int = 768,
    height: int = 0,
    time: str = "",
    style: str = "",
    image_format: str = "image/png",
    transparent: bool = True,
) -> tuple[bytes, str]:
    """Render the layer. Returns (image bytes, content type)."""
    if height <= 0:
        aspect = (bbox.height / bbox.width) if bbox.width else 1.0
        height = max(64, min(2048, int(width * aspect)))

    params = _version_params(layer, bbox, width, height)
    params.update(
        {
            "request": "GetMap",
            "format": image_format,
            "transparent": str(transparent).lower(),
            "styles": style,
            "time": time or layer.time_default,
        }
    )
    return await client.get(endpoint, params, expect="image", ttl=settings.data_ttl)


def _extract_value(body: bytes, content_type: str) -> float | None:
    """Pull a single numeric value out of a GetFeatureInfo response."""
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return None

    if "json" in content_type or text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        features = payload.get("features") or []
        for feature in features:
            props = feature.get("properties") or {}
            for key, value in props.items():
                if key.lower() in {"gray_index", "grey_index", "value", "band1",
                                   "red_band", "palette_index"} or isinstance(value, (int, float)):
                    try:
                        number = float(value)
                    except (TypeError, ValueError):
                        continue
                    if math.isfinite(number):
                        return number
        return None

    # text/plain: GeoServer prints "  gray_index = 12.5"
    for line in text.splitlines():
        if "=" in line:
            _, _, raw = line.partition("=")
            try:
                number = float(raw.strip())
            except ValueError:
                continue
            if math.isfinite(number):
                return number
    return None


async def feature_info(
    client: OGCClient,
    endpoint: Endpoint,
    layer: Layer,
    lon: float,
    lat: float,
    *,
    time: str = "",
    window: float = 0.02,
) -> float | None:
    """Query the layer's value at one coordinate."""
    bbox = BBox(
        west=lon - window, south=lat - window, east=lon + window, north=lat + window
    )
    size = 3   # 3x3 pixels; we query the centre one
    params = _version_params(layer, bbox, size, size)
    params.update(
        {
            "request": "GetFeatureInfo",
            "query_layers": layer.name,
            "x": 1,
            "y": 1,
            "feature_count": 1,
            "time": time or layer.time_default,
        }
    )

    for info_format in INFO_FORMATS:
        try:
            body, content_type = await client.get(
                endpoint, {**params, "info_format": info_format}
            )
        except OGCError:
            continue
        value = _extract_value(body, content_type)
        if value is not None:
            return value
    return None


def grid_points(bbox: BBox, n: int) -> list[tuple[float, float]]:
    """Cell-centre coordinates of an n x n grid over the bbox."""
    n = max(2, n)
    points = []
    for row in range(n):
        for col in range(n):
            points.append(
                (
                    bbox.west + bbox.width * (col + 0.5) / n,
                    bbox.south + bbox.height * (row + 0.5) / n,
                )
            )
    return points


async def sample_grid(
    client: OGCClient,
    endpoint: Endpoint,
    layer: Layer,
    bbox: BBox,
    *,
    time: str = "",
    grid: int = 0,
) -> tuple[list[float], int]:
    """Sample the layer across the bbox. Returns (values, points attempted)."""
    n = grid or settings.sample_grid
    points = grid_points(bbox, n)

    results = await asyncio.gather(
        *(feature_info(client, endpoint, layer, lon, lat, time=time) for lon, lat in points),
        return_exceptions=True,
    )
    values = [
        r for r in results
        if isinstance(r, (int, float)) and math.isfinite(float(r))
    ]
    return [float(v) for v in values], len(points)
