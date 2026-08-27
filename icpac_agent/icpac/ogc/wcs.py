"""WCS access: real coverage pixels for zonal statistics.

This is the preferred path for any "how much rain fell over X" question -
it reads the source raster rather than sampling a rendered image. It needs
``rasterio`` to decode the GeoTIFF; when that is not installed the caller
falls back to WMS grid sampling and the returned statistics say so.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..config import Endpoint, settings
from ..models import BBox, Layer
from .client import OGCClient, OGCError

try:  # optional - see module docstring
    import rasterio
    from rasterio.io import MemoryFile

    HAVE_RASTERIO = True
except ImportError:  # pragma: no cover - exercised by deployments without GDAL
    HAVE_RASTERIO = False


def _pixel_size(bbox: BBox) -> tuple[int, int]:
    cap = settings.max_coverage_px
    aspect = (bbox.height / bbox.width) if bbox.width else 1.0
    if aspect >= 1:
        height = cap
        width = max(16, int(cap / aspect))
    else:
        width = cap
        height = max(16, int(cap * aspect))
    return width, height


def _requests(layer: Layer, bbox: BBox, time: str) -> list[dict[str, Any]]:
    """Candidate GetCoverage requests, newest WCS version first."""
    width, height = _pixel_size(bbox)
    stamp = time or layer.time_default

    v201: dict[str, Any] = {
        "service": "WCS",
        "version": "2.0.1",
        "request": "GetCoverage",
        "coverageId": layer.name,
        "format": "image/tiff",
        "subset": [
            f"Long({bbox.west},{bbox.east})",
            f"Lat({bbox.south},{bbox.north})",
        ],
    }
    if stamp:
        v201["subset"] = list(v201["subset"]) + [f'time("{stamp}")']

    v100 = {
        "service": "WCS",
        "version": "1.0.0",
        "request": "GetCoverage",
        "coverage": layer.name,
        "crs": "EPSG:4326",
        "bbox": bbox.as_str(),
        "width": width,
        "height": height,
        "format": "GeoTIFF",
        "time": stamp,
    }
    return [v201, v100]


def _flatten(body: bytes) -> tuple[list[float], int]:
    """Decode a GeoTIFF into finite values. Returns (values, total pixels)."""
    with MemoryFile(body) as memfile:
        with memfile.open() as dataset:
            band = dataset.read(1, masked=True)
            total = int(band.size)
            data = np.ma.filled(band.astype("float64"), np.nan)
            nodata = dataset.nodata
            if nodata is not None and math.isfinite(float(nodata)):
                data = np.where(np.isclose(data, float(nodata)), np.nan, data)
            finite = data[np.isfinite(data)]
            return finite.tolist(), total


async def fetch_coverage(
    client: OGCClient,
    endpoint: Endpoint,
    layer: Layer,
    bbox: BBox,
    *,
    time: str = "",
) -> tuple[list[float], int]:
    """Read coverage values inside the bbox. Returns (values, pixels).

    Raises :class:`OGCError` when no WCS version answers, or when rasterio
    is unavailable - both are conditions the caller handles by falling back
    to WMS sampling.
    """
    if not HAVE_RASTERIO:
        raise OGCError("rasterio is not installed - install it for WCS zonal statistics")

    last = ""
    for params in _requests(layer, bbox, time):
        try:
            body, content_type = await client.get(endpoint, params)
        except OGCError as exc:
            last = str(exc)
            continue
        if "tif" not in content_type and not body[:4] in (b"II*\x00", b"MM\x00*"):
            last = f"expected GeoTIFF, got {content_type or 'unknown type'}"
            continue
        try:
            return _flatten(body)
        except Exception as exc:  # noqa: BLE001 - a corrupt tile is just a miss
            last = f"could not decode coverage: {type(exc).__name__}"
            continue

    raise OGCError(last or "no WCS version returned a coverage")
