"""GetCapabilities parsing for WMS, WFS and WCS.

Written namespace-agnostically (tags are compared after stripping the
namespace) because ICPAC-style stacks mix GeoServer versions, and a parser
pinned to one schema breaks the first time a server is upgraded. Both the
older and newer encodings of each service are handled.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

from ..models import BBox, Layer
from .client import strip_ns

#: Never expand a time range into more than this many instants.
MAX_TIME_VALUES = 400

ISO_DURATION = re.compile(
    r"^P(?:(?P<years>\d+)Y)?(?:(?P<months>\d+)M)?(?:(?P<days>\d+)D)?"
    r"(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$",
    re.I,
)


def _first(element: ElementTree.Element, *names: str) -> ElementTree.Element | None:
    """First **direct** child whose local tag matches any of ``names``.

    Direct-only matters: WMS nests <Layer> inside <Layer>, so a descendant
    search would let a container layer inherit its first child's Name.
    """
    wanted = {n.lower() for n in names}
    for child in element:
        if strip_ns(child.tag).lower() in wanted:
            return child
    return None


def _find(element: ElementTree.Element, *names: str) -> ElementTree.Element | None:
    """First direct-or-nested descendant matching any of ``names``."""
    wanted = {n.lower() for n in names}
    for child in element.iter():
        if child is not element and strip_ns(child.tag).lower() in wanted:
            return child
    return None


def _children(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [c for c in element if strip_ns(c.tag).lower() == name.lower()]


def _keywords(element: ElementTree.Element) -> list[str]:
    """Keywords from this node's own KeywordList, not a child layer's."""
    container = _first(element, "KeywordList", "Keywords")
    if container is None:
        return []
    return [_text(k) for k in container if strip_ns(k.tag) == "Keyword" and _text(k)][:20]


def _text(element: ElementTree.Element | None, default: str = "") -> str:
    if element is None or element.text is None:
        return default
    return " ".join(element.text.split())


def _parse_duration(value: str) -> timedelta | None:
    m = ISO_DURATION.match(value.strip())
    if not m or not any(m.groupdict().values()):
        return None
    g = {k: int(v) for k, v in m.groupdict(default="0").items()}
    # Calendar months/years are approximated - fine for enumerating instants.
    days = g["years"] * 365 + g["months"] * 30 + g["days"]
    return timedelta(
        days=days, hours=g["hours"], minutes=g["minutes"], seconds=g["seconds"]
    )


def _parse_instant(value: str) -> datetime | None:
    value = value.strip()
    if not value or value.lower() in {"current", "now", "present"}:
        return datetime.now(timezone.utc)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(value.replace(".000", ""), fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def expand_time_extent(extent: str) -> list[str]:
    """Turn a WMS/WCS time extent into a list of ISO instants.

    Handles comma-separated instants and ``start/end/period`` ranges. Ranges
    are expanded from the *end* backwards so the most recent steps survive
    the cap - those are what a live-feed question almost always asks about.
    """
    extent = (extent or "").strip()
    if not extent:
        return []

    out: list[str] = []
    for part in extent.split(","):
        part = part.strip()
        if not part:
            continue
        if "/" not in part:
            out.append(part)
            continue

        bits = part.split("/")
        start, end = _parse_instant(bits[0]), _parse_instant(bits[1] if len(bits) > 1 else "")
        step = _parse_duration(bits[2]) if len(bits) > 2 else None
        if not start or not end:
            out.append(part)
            continue
        if not step or step.total_seconds() <= 0:
            out.extend([bits[0], bits[1]])
            continue

        span = (end - start).total_seconds()
        count = int(span // step.total_seconds()) + 1
        if count > MAX_TIME_VALUES:
            start = end - step * (MAX_TIME_VALUES - 1)
            count = MAX_TIME_VALUES

        cursor = start
        for _ in range(max(1, count)):
            out.append(cursor.strftime("%Y-%m-%dT%H:%M:%SZ"))
            cursor += step

    if len(out) > MAX_TIME_VALUES:
        out = out[-MAX_TIME_VALUES:]
    return out


# ------------------------------------------------------------------- WMS ---

def _wms_bbox(node: ElementTree.Element) -> BBox | None:
    if geo := _first(node, "EX_GeographicBoundingBox"):
        try:
            return BBox(
                west=float(_text(_first(geo, "westBoundLongitude"))),
                south=float(_text(_first(geo, "southBoundLatitude"))),
                east=float(_text(_first(geo, "eastBoundLongitude"))),
                north=float(_text(_first(geo, "northBoundLatitude"))),
            )
        except (TypeError, ValueError):
            pass
    if ll := _first(node, "LatLonBoundingBox"):
        try:
            return BBox(
                west=float(ll.get("minx", "nan")), south=float(ll.get("miny", "nan")),
                east=float(ll.get("maxx", "nan")), north=float(ll.get("maxy", "nan")),
            )
        except ValueError:
            pass
    return None


def _wms_time(node: ElementTree.Element) -> tuple[list[str], str]:
    for tag in ("Dimension", "Extent"):
        for element in node:
            if strip_ns(element.tag) != tag:
                continue
            if (element.get("name") or "").lower() != "time":
                continue
            values = expand_time_extent(element.text or "")
            default = element.get("default") or (values[-1] if values else "")
            if values or default:
                return values, default
    return [], ""


def parse_wms(xml: bytes, endpoint: str) -> list[Layer]:
    root = ElementTree.fromstring(xml)
    layers: list[Layer] = []

    def walk(node: ElementTree.Element, inherited_crs: list[str], inherited_bbox: BBox | None):
        crs = list(inherited_crs)
        for child in node:
            if strip_ns(child.tag) in {"CRS", "SRS"} and child.text:
                crs.append(child.text.strip())

        bbox = _wms_bbox(node) or inherited_bbox
        name = _text(_first(node, "Name"))

        if name:
            times, default = _wms_time(node)
            layers.append(
                Layer(
                    id=f"{endpoint}:{name}",
                    name=name,
                    endpoint=endpoint,
                    service="WMS",
                    title=_text(_first(node, "Title")),
                    abstract=_text(_first(node, "Abstract"))[:800],
                    keywords=_keywords(node),
                    bbox=bbox,
                    crs=sorted(set(crs))[:12],
                    time_values=times,
                    time_default=default,
                    styles=[
                        _text(_first(s, "Name"))
                        for s in _children(node, "Style")
                        if _text(_first(s, "Name"))
                    ][:10],
                    queryable=node.get("queryable") in {"1", "true"},
                )
            )

        for child in _children(node, "Layer"):
            walk(child, crs, bbox)

    capability = _find(root, "Capability")
    for top in _children(capability if capability is not None else root, "Layer"):
        walk(top, [], None)

    # A GetCapabilities root layer often has no Name; those are containers.
    return [layer for layer in layers if layer.name]


# ------------------------------------------------------------------- WFS ---

def _corner_bbox(node: ElementTree.Element) -> BBox | None:
    container = _first(node, "WGS84BoundingBox", "BoundingBox") or node
    lower = _first(container, "LowerCorner")
    upper = _first(container, "UpperCorner")
    if lower is None or upper is None:
        return None
    try:
        w, s = (float(v) for v in _text(lower).split()[:2])
        e, n = (float(v) for v in _text(upper).split()[:2])
        return BBox(west=w, south=s, east=e, north=n)
    except ValueError:
        return None


def parse_wfs(xml: bytes, endpoint: str) -> list[Layer]:
    root = ElementTree.fromstring(xml)
    layers: list[Layer] = []

    for ft in root.iter():
        if strip_ns(ft.tag) != "FeatureType":
            continue
        name = _text(_first(ft, "Name"))
        if not name:
            continue
        crs = [
            _text(c) for c in ft
            if strip_ns(c.tag) in {"DefaultCRS", "DefaultSRS", "OtherCRS", "OtherSRS"}
            and _text(c)
        ]
        layers.append(
            Layer(
                id=f"{endpoint}:{name}",
                name=name,
                endpoint=endpoint,
                service="WFS",
                title=_text(_first(ft, "Title")),
                abstract=_text(_first(ft, "Abstract"))[:800],
                keywords=_keywords(ft),
                bbox=_corner_bbox(ft) or _wms_bbox(ft),
                crs=crs[:12],
                queryable=True,
            )
        )
    return layers


# ------------------------------------------------------------------- WCS ---

def parse_wcs(xml: bytes, endpoint: str) -> list[Layer]:
    root = ElementTree.fromstring(xml)
    layers: list[Layer] = []

    # WCS 2.0: Contents/CoverageSummary/CoverageId
    for summary in root.iter():
        if strip_ns(summary.tag) != "CoverageSummary":
            continue
        name = _text(_first(summary, "CoverageId")) or _text(_first(summary, "Identifier"))
        if not name:
            continue
        layers.append(
            Layer(
                id=f"{endpoint}:{name}",
                name=name,
                endpoint=endpoint,
                service="WCS",
                title=_text(_first(summary, "Title")),
                abstract=_text(_first(summary, "Abstract"))[:800],
                bbox=_corner_bbox(summary),
            )
        )

    if layers:
        return layers

    # WCS 1.0: ContentMetadata/CoverageOfferingBrief/name + lonLatEnvelope
    for brief in root.iter():
        if strip_ns(brief.tag) != "CoverageOfferingBrief":
            continue
        name = _text(_first(brief, "name"))
        if not name:
            continue
        bbox = None
        if envelope := _first(brief, "lonLatEnvelope"):
            positions = [
                _text(p) for p in envelope if strip_ns(p.tag) == "pos" and _text(p)
            ]
            if len(positions) >= 2:
                try:
                    w, s = (float(v) for v in positions[0].split()[:2])
                    e, n = (float(v) for v in positions[1].split()[:2])
                    bbox = BBox(west=w, south=s, east=e, north=n)
                except ValueError:
                    bbox = None
        layers.append(
            Layer(
                id=f"{endpoint}:{name}",
                name=name,
                endpoint=endpoint,
                service="WCS",
                title=_text(_first(brief, "label")) or _text(_first(brief, "description")),
                abstract=_text(_first(brief, "description"))[:800],
                bbox=bbox,
            )
        )
    return layers


PARSERS = {"WMS": parse_wms, "WFS": parse_wfs, "WCS": parse_wcs}

CAPABILITIES_PARAMS = {
    "WMS": {"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"},
    "WFS": {"service": "WFS", "request": "GetCapabilities", "version": "2.0.0"},
    "WCS": {"service": "WCS", "request": "GetCapabilities", "version": "2.0.1"},
}

#: Tried in order when the preferred version is rejected by the server.
FALLBACK_VERSIONS = {"WMS": ["1.1.1"], "WFS": ["1.1.0", "1.0.0"], "WCS": ["1.1.1", "1.0.0"]}
