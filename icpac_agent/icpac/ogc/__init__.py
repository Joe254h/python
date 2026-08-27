"""OGC service clients: capabilities discovery, WMS, WFS and WCS access."""

from .capabilities import parse_wcs, parse_wfs, parse_wms
from .client import OGCClient, OGCError
from .wcs import fetch_coverage
from .wfs import fetch_features
from .wms import feature_info, get_map, sample_grid

__all__ = [
    "OGCClient",
    "OGCError",
    "parse_wms",
    "parse_wfs",
    "parse_wcs",
    "get_map",
    "feature_info",
    "sample_grid",
    "fetch_features",
    "fetch_coverage",
]
