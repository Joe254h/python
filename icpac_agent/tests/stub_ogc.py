"""A minimal in-process OGC server, so the agent can be tested for real.

It speaks enough WMS 1.1.1/1.3.0, WFS 2.0.0 and WCS 2.0.1 to exercise the
whole path: capabilities discovery, boundary resolution, value sampling and
ranking. Values vary with longitude, so places genuinely differ and the
ranking logic is tested against something other than a constant.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

WMS_CAPS = """<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms">
  <Service><Name>WMS</Name><Title>Stub ICPAC WMS</Title></Service>
  <Capability>
    <Layer>
      <Title>Stub root</Title>
      <CRS>EPSG:4326</CRS>
      <EX_GeographicBoundingBox>
        <westBoundLongitude>21.0</westBoundLongitude>
        <eastBoundLongitude>52.0</eastBoundLongitude>
        <southBoundLatitude>-12.0</southBoundLatitude>
        <northBoundLatitude>23.0</northBoundLatitude>
      </EX_GeographicBoundingBox>
      <Layer queryable="1">
        <Name>icpac:spi_3month</Name>
        <Title>SPI 3-month standardized precipitation index</Title>
        <Abstract>Standardized Precipitation Index over 3 months.</Abstract>
        <KeywordList><Keyword>drought</Keyword><Keyword>spi</Keyword></KeywordList>
        <Dimension name="time" units="ISO8601"
                   default="2026-08-01T00:00:00Z">2026-05-01T00:00:00Z/2026-08-01T00:00:00Z/P1M</Dimension>
        <Style><Name>spi_default</Name><Title>Default</Title></Style>
      </Layer>
      <Layer queryable="1">
        <Name>icpac:rfe_dekad</Name>
        <Title>Dekadal rainfall estimate (CHIRPS)</Title>
        <Abstract>Rainfall estimate in mm per dekad.</Abstract>
        <KeywordList><Keyword>rainfall</Keyword><Keyword>chirps</Keyword></KeywordList>
        <Dimension name="time" units="ISO8601"
                   default="2026-08-20T00:00:00Z">2026-06-01T00:00:00Z,2026-06-11T00:00:00Z,2026-08-20T00:00:00Z</Dimension>
      </Layer>
      <Layer queryable="1">
        <Name>icpac:admin1</Name>
        <Title>Administrative boundaries level 1</Title>
        <KeywordList><Keyword>admin</Keyword><Keyword>boundary</Keyword></KeywordList>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>
"""

WFS_CAPS = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:WFS_Capabilities version="2.0.0"
    xmlns:wfs="http://www.opengis.net/wfs/2.0"
    xmlns:ows="http://www.opengis.net/ows/1.1">
  <wfs:FeatureTypeList>
    <wfs:FeatureType>
      <wfs:Name>icpac:admin1</wfs:Name>
      <wfs:Title>Administrative boundaries level 1</wfs:Title>
      <wfs:Abstract>County and region boundaries.</wfs:Abstract>
      <ows:Keywords><ows:Keyword>admin</ows:Keyword><ows:Keyword>boundary</ows:Keyword></ows:Keywords>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::4326</wfs:DefaultCRS>
      <ows:WGS84BoundingBox>
        <ows:LowerCorner>21.0 -12.0</ows:LowerCorner>
        <ows:UpperCorner>52.0 23.0</ows:UpperCorner>
      </ows:WGS84BoundingBox>
    </wfs:FeatureType>
    <wfs:FeatureType>
      <wfs:Name>icpac:flood_alerts</wfs:Name>
      <wfs:Title>Active flood hazard alerts</wfs:Title>
      <ows:Keywords><ows:Keyword>flood</ows:Keyword><ows:Keyword>hazard</ows:Keyword></ows:Keywords>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::4326</wfs:DefaultCRS>
    </wfs:FeatureType>
  </wfs:FeatureTypeList>
</wfs:WFS_Capabilities>
"""

WCS_CAPS = """<?xml version="1.0" encoding="UTF-8"?>
<wcs:Capabilities version="2.0.1"
    xmlns:wcs="http://www.opengis.net/wcs/2.0"
    xmlns:ows="http://www.opengis.net/ows/2.0">
  <wcs:Contents>
    <wcs:CoverageSummary>
      <wcs:CoverageId>icpac__spi_3month</wcs:CoverageId>
      <ows:Title>SPI 3-month standardized precipitation index</ows:Title>
      <ows:WGS84BoundingBox>
        <ows:LowerCorner>21.0 -12.0</ows:LowerCorner>
        <ows:UpperCorner>52.0 23.0</ows:UpperCorner>
      </ows:WGS84BoundingBox>
    </wcs:CoverageSummary>
    <wcs:CoverageSummary>
      <wcs:CoverageId>geonode__Above_ground_biomass_normal</wcs:CoverageId>
      <ows:Title>Above_ground_biomass_normal</ows:Title>
    </wcs:CoverageSummary>
  </wcs:Contents>
</wcs:Capabilities>
"""

EXCEPTION = """<?xml version="1.0"?>
<ServiceExceptionReport><ServiceException code="LayerNotDefined">Unknown layer</ServiceException></ServiceExceptionReport>
"""

#: Set False by tests that want to exercise the WMS fallback instead of WCS.
SERVE_COVERAGES = True

#: Admin units the stub publishes, with real-ish extents.
BOUNDARIES = {
    "Turkana": [34.1, 1.4, 36.7, 5.5],
    "Marsabit": [36.0, 1.6, 39.6, 4.6],
    "Wajir": [38.5, 0.4, 41.2, 3.6],
    "Mandera": [39.7, 2.7, 41.9, 4.7],
}


def _ring(box):
    w, s, e, n = box
    return [[[w, s], [e, s], [e, n], [w, n], [w, s]]]


def make_geotiff(layer: str, bbox, width: int = 24, height: int = 24) -> bytes | None:
    """Encode the synthetic field as a real GeoTIFF, if rasterio is present.

    Lets the suite exercise the production WCS path rather than only the
    WMS fallback. Returns None when rasterio is unavailable, and the stub
    then answers GetCoverage with an exception so the fallback is tested.
    """
    try:
        import numpy as np
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.transform import from_bounds
    except ImportError:
        return None

    w, s, e, n = bbox
    lons = np.linspace(w, e, width)
    lats = np.linspace(n, s, height)
    grid = np.array([[stub_value(layer, lon, lat) for lon in lons] for lat in lats],
                    dtype="float32")
    grid[0, 0] = -9999.0          # a nodata pixel, so masking is exercised

    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff", height=height, width=width, count=1, dtype="float32",
            crs="EPSG:4326", transform=from_bounds(w, s, e, n, width, height),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(grid, 1)
        return memfile.read()


def stub_value(layer: str, lon: float, lat: float) -> float:
    """Deterministic synthetic field - drier to the east, wetter to the west."""
    if "spi" in layer:
        return round(-2.6 + (lon - 34.0) * -0.18 + (lat - 3.0) * 0.05, 3)
    if "rfe" in layer:
        return round(max(0.0, 120.0 - (lon - 34.0) * 11.0 + (lat - 3.0) * 2.0), 2)
    return round(lon + lat, 3)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence the default stderr logging
        pass

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        query = parse_qs(urlparse(self.path).query)
        get = lambda key, default="": (query.get(key) or query.get(key.upper())  # noqa: E731
                                       or query.get(key.lower()) or [default])[0]

        service = get("service").upper()
        request = get("request").lower()

        if request == "getcapabilities":
            body = {"WMS": WMS_CAPS, "WFS": WFS_CAPS, "WCS": WCS_CAPS}.get(service)
            if body is None:
                return self._send(EXCEPTION.encode(), "text/xml", 400)
            return self._send(body.encode(), "text/xml")

        if request == "getfeatureinfo":
            layer = get("query_layers") or get("layers")
            bbox = [float(v) for v in (get("bbox") or "0,0,1,1").split(",")]
            lon = (bbox[0] + bbox[2]) / 2
            lat = (bbox[1] + bbox[3]) / 2
            payload = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "properties": {"GRAY_INDEX": stub_value(layer, lon, lat)}}
                ],
            }
            return self._send(json.dumps(payload).encode(), "application/json")

        if request == "getmap":
            # 1x1 transparent PNG - enough to prove the path works.
            png = bytes.fromhex(
                "89504e470d0a1a0a0000000d494844520000000100000001080600000"
                "01f15c4890000000a49444154789c6360000002000100ffff03000006000557bfabd4"
                "0000000049454e44ae426082"
            )
            return self._send(png, "image/png")

        if request == "getfeature":
            type_name = get("typeNames") or get("typeName")
            cql = (get("cql_filter") or "").lower()
            if "flood" in type_name:
                features = [
                    {
                        "type": "Feature",
                        "properties": {"name": "Tana delta", "severity": "high", "people": 42000},
                        "geometry": {"type": "Polygon", "coordinates": _ring([39.8, -2.6, 40.4, -1.8])},
                    }
                ]
            else:
                features = [
                    {
                        "type": "Feature",
                        "properties": {"name": name, "adm0_en": "Kenya"},
                        "geometry": {"type": "Polygon", "coordinates": _ring(box)},
                    }
                    for name, box in BOUNDARIES.items()
                    if not cql or name.lower() in cql
                ]
            payload = {"type": "FeatureCollection", "features": features}
            return self._send(json.dumps(payload).encode(), "application/json")

        if request == "getcoverage":
            if not globals()["SERVE_COVERAGES"]:
                # Forces the documented WMS fallback path.
                return self._send(EXCEPTION.encode(), "text/xml")

            layer = get("coverageId") or get("coverage")
            subsets = query.get("subset") or query.get("SUBSET") or []
            bbox = [21.0, -12.0, 52.0, 23.0]
            for axis in subsets:
                if "(" not in axis:
                    continue
                name, _, span = axis.partition("(")
                lo, _, hi = span.rstrip(")").partition(",")
                try:
                    lo_f, hi_f = float(lo), float(hi)
                except ValueError:
                    continue
                if name.lower().startswith("long"):
                    bbox[0], bbox[2] = lo_f, hi_f
                elif name.lower().startswith("lat"):
                    bbox[1], bbox[3] = lo_f, hi_f
            if get("bbox"):
                bbox = [float(v) for v in get("bbox").split(",")[:4]]

            tif = make_geotiff(layer, bbox)
            if tif is None:
                return self._send(EXCEPTION.encode(), "text/xml")
            return self._send(tif, "image/tiff")

        return self._send(EXCEPTION.encode(), "text/xml", 400)


class StubServer:
    """Context manager that runs the stub on a free localhost port."""

    def __init__(self) -> None:
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}/ows"

    def __enter__(self) -> "StubServer":
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
