"""Turning a place name into an extent the agent can analyse.

Two paths, in this order:

1. **WFS admin boundaries** - authoritative. If any configured endpoint
   publishes an administrative-boundary layer, the name is matched against
   its attributes and the real polygon extent is used.
2. **Built-in gazetteer** - a coarse fallback for the IGAD/Greater Horn
   region so the agent still works before any boundary layer is wired up.

The gazetteer boxes are *approximate rectangles*, not polygons. Statistics
computed over them include area outside the true boundary, which matters
most for long, thin or coastal units. Every result says which path was
used, so a caller can tell a precise answer from a rough one.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from .catalog import Catalog
from .config import Endpoint, settings
from .models import BBox, Layer, Place
from .ogc.client import OGCClient, OGCError
from .ogc.wfs import fetch_features, geometry_bbox

# --------------------------------------------------------------- countries ---

COUNTRIES: dict[str, tuple[float, float, float, float]] = {
    "Kenya": (33.9, -4.7, 41.9, 5.5),
    "Ethiopia": (32.9, 3.4, 48.0, 14.9),
    "Somalia": (40.9, -1.7, 51.4, 12.0),
    "Uganda": (29.5, -1.5, 35.0, 4.2),
    "South Sudan": (24.1, 3.5, 35.9, 12.2),
    "Sudan": (21.8, 8.7, 38.6, 22.2),
    "Djibouti": (41.7, 10.9, 43.4, 12.7),
    "Eritrea": (36.4, 12.4, 43.1, 18.0),
    "Tanzania": (29.3, -11.7, 40.4, -0.9),
    "Rwanda": (28.8, -2.8, 30.9, -1.0),
    "Burundi": (29.0, -4.5, 30.8, -2.3),
}

REGION_BBOX = BBox(west=21.8, south=-11.7, east=51.4, north=22.2)   # IGAD + EAC

# ------------------------------------------------------- admin-1 gazetteer ---
# Approximate extents. WFS boundaries override these whenever available.

KENYA_COUNTIES: dict[str, tuple[float, float, float, float]] = {
    "Turkana": (34.1, 1.4, 36.7, 5.5), "Marsabit": (36.0, 1.6, 39.6, 4.6),
    "Mandera": (39.7, 2.7, 41.9, 4.7), "Wajir": (38.5, 0.4, 41.2, 3.6),
    "Garissa": (38.4, -1.9, 41.6, 1.1), "Isiolo": (36.9, -0.4, 39.5, 2.3),
    "Samburu": (36.0, 0.5, 38.1, 2.6), "West Pokot": (34.6, 1.0, 35.8, 2.6),
    "Baringo": (35.4, -0.1, 36.4, 1.9), "Laikipia": (36.1, -0.4, 37.5, 0.8),
    "Kitui": (37.5, -3.2, 39.2, -0.3), "Makueni": (37.3, -3.1, 38.3, -1.5),
    "Machakos": (36.8, -1.9, 37.9, -0.7), "Kajiado": (36.1, -3.3, 37.9, -1.1),
    "Narok": (34.9, -2.6, 36.5, -0.7), "Tana River": (38.4, -3.0, 40.5, -0.2),
    "Lamu": (40.1, -2.6, 41.6, -1.6), "Kilifi": (39.0, -4.3, 40.4, -2.4),
    "Kwale": (38.5, -4.7, 39.8, -3.4), "Mombasa": (39.5, -4.1, 39.8, -3.9),
    "Taita Taveta": (37.6, -4.3, 39.1, -2.8), "Nairobi": (36.65, -1.45, 37.1, -1.16),
    "Kiambu": (36.5, -1.3, 37.2, -0.7), "Murang'a": (36.6, -1.1, 37.4, -0.5),
    "Nyeri": (36.5, -0.6, 37.3, 0.0), "Kirinyaga": (37.0, -0.7, 37.5, -0.2),
    "Embu": (37.3, -0.9, 38.1, -0.2), "Meru": (37.3, -0.3, 38.4, 0.7),
    "Tharaka Nithi": (37.5, -0.6, 38.3, 0.1), "Nakuru": (35.6, -1.2, 36.5, 0.4),
    "Nyandarua": (36.2, -1.0, 36.8, 0.2), "Kericho": (35.0, -0.9, 35.8, -0.1),
    "Bomet": (35.0, -1.2, 35.7, -0.5), "Nandi": (34.8, -0.4, 35.5, 0.5),
    "Uasin Gishu": (34.9, -0.2, 35.7, 0.9), "Elgeyo Marakwet": (35.3, 0.0, 35.8, 1.4),
    "Trans Nzoia": (34.6, 0.7, 35.4, 1.4), "Bungoma": (34.2, 0.3, 35.2, 1.2),
    "Busia": (33.9, -0.1, 34.5, 0.9), "Kakamega": (34.4, -0.2, 35.1, 1.0),
    "Vihiga": (34.6, -0.2, 34.9, 0.2), "Siaya": (33.9, -0.4, 34.6, 0.4),
    "Kisumu": (34.2, -0.6, 35.1, 0.1), "Homa Bay": (34.0, -1.1, 34.8, -0.2),
    "Migori": (34.0, -1.5, 34.9, -0.7), "Kisii": (34.6, -1.1, 35.1, -0.5),
    "Nyamira": (34.8, -1.0, 35.2, -0.5),
}

OTHER_ADMIN: dict[str, tuple[str, tuple[float, float, float, float]]] = {
    # Ethiopia
    "Afar": ("Ethiopia", (39.7, 8.7, 42.4, 14.5)),
    "Somali Region": ("Ethiopia", (39.8, 3.4, 48.0, 11.0)),
    "Oromia": ("Ethiopia", (34.1, 3.4, 43.3, 10.5)),
    "Amhara": ("Ethiopia", (35.3, 8.7, 40.2, 13.8)),
    "Tigray": ("Ethiopia", (36.4, 12.2, 40.3, 14.9)),
    "SNNPR": ("Ethiopia", (34.9, 4.3, 39.2, 8.6)),
    # Somalia
    "Bay": ("Somalia", (42.5, 1.7, 44.8, 3.6)),
    "Bakool": ("Somalia", (42.5, 3.2, 44.8, 5.2)),
    "Gedo": ("Somalia", (41.0, 1.6, 43.2, 4.4)),
    "Lower Juba": ("Somalia", (41.0, -1.7, 43.0, 1.0)),
    "Mudug": ("Somalia", (45.7, 5.4, 50.5, 8.0)),
    "Puntland": ("Somalia", (45.5, 6.5, 51.4, 12.0)),
    "Somaliland": ("Somalia", (42.6, 8.0, 49.0, 11.5)),
    # Uganda
    "Karamoja": ("Uganda", (33.4, 1.5, 35.0, 4.2)),
    "Teso": ("Uganda", (33.2, 1.1, 34.4, 2.4)),
    # South Sudan
    "Jonglei": ("South Sudan", (30.5, 5.5, 34.6, 9.5)),
    "Upper Nile": ("South Sudan", (31.5, 8.5, 35.3, 12.2)),
    "Equatoria": ("South Sudan", (27.5, 3.5, 35.0, 6.5)),
    # Basins and lakes
    "Lake Victoria": ("", (31.5, -3.1, 34.9, 0.6)),
    "Lake Turkana": ("", (35.8, 2.4, 36.7, 4.7)),
    "Horn of Africa": ("", (32.0, -5.0, 51.5, 18.0)),
    "Greater Horn of Africa": ("", REGION_BBOX.as_list()),  # type: ignore[dict-item]
}

#: Attribute names admin-boundary layers use for the unit's name.
NAME_FIELDS = (
    "name", "name_1", "name_2", "adm1_en", "adm2_en", "adm0_en", "admin1name",
    "admin2name", "shapename", "county", "district", "region", "province",
    "woreda", "zone", "state", "nam", "nom",
)

CLEAN = re.compile(r"\b(county|district|region|province|state|zone|woreda|sub-?county)\b", re.I)


def normalise(name: str) -> str:
    return " ".join(CLEAN.sub(" ", name or "").replace("'", "").lower().split())


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalise(a), normalise(b)).ratio()


# --------------------------------------------------------------- gazetteer ---

def gazetteer_lookup(name: str) -> Place | None:
    """Best gazetteer match for a place name, or None below the threshold."""
    target = normalise(name)
    if not target:
        return None

    candidates: list[tuple[str, str, str, tuple[float, ...]]] = []
    for country, box in COUNTRIES.items():
        candidates.append((country, "country", country, box))
    for county, box in KENYA_COUNTIES.items():
        candidates.append((county, "admin", "Kenya", box))
    for place, (country, box) in OTHER_ADMIN.items():
        candidates.append((place, "admin" if country else "basin", country, tuple(box)))

    best: tuple[float, Place] | None = None
    for label, kind, country, box in candidates:
        score = similarity(label, name)
        if normalise(label) == target:
            score = 1.0
        elif target and target in normalise(label):
            score = max(score, 0.9)
        if score < 0.72:
            continue
        place = Place(
            name=label, kind=kind, country=country,
            bbox=BBox.from_list(list(box)), source="gazetteer",
        )
        if best is None or score > best[0]:
            best = (score, place)

    return best[1] if best else None


# ------------------------------------------------------------- WFS lookup ---

def admin_layers(catalog: Catalog) -> list[Layer]:
    """WFS layers that look like administrative boundaries, best first."""
    scored = catalog.search("administrative boundary county district region admin",
                            limit=25, service="WFS")
    return [layer for layer, _ in scored]


async def wfs_lookup(
    client: OGCClient, catalog: Catalog, name: str, *, max_layers: int = 3
) -> Place | None:
    """Resolve a place against published admin-boundary layers."""
    endpoints = {e.name: e for e in settings.endpoints}

    for layer in admin_layers(catalog)[:max_layers]:
        endpoint: Endpoint | None = endpoints.get(layer.endpoint)
        if endpoint is None:
            continue

        # Try a server-side filter first; fall back to scanning the layer.
        clauses = " OR ".join(f"strToLowerCase({f}) LIKE '%{normalise(name)}%'"
                              for f in NAME_FIELDS[:6])
        for cql in (clauses, ""):
            try:
                collection = await fetch_features(
                    client, endpoint, layer, cql_filter=cql, limit=400 if not cql else 40
                )
            except OGCError:
                continue

            best: tuple[float, Place] | None = None
            for feature in collection.get("features", []):
                props = {k.lower(): v for k, v in (feature.get("properties") or {}).items()}
                labels = [
                    str(props[f]) for f in NAME_FIELDS
                    if f in props and isinstance(props[f], str) and props[f].strip()
                ]
                for label in labels:
                    score = similarity(label, name)
                    if normalise(label) == normalise(name):
                        score = 1.0
                    if score < 0.82:
                        continue
                    bbox = geometry_bbox(feature.get("geometry") or {})
                    if bbox is None:
                        continue
                    place = Place(
                        name=label.strip(), kind="admin",
                        country=str(props.get("adm0_en") or props.get("country") or ""),
                        bbox=bbox, source=f"wfs:{layer.id}",
                    )
                    if best is None or score > best[0]:
                        best = (score, place)

            if best:
                return best[1]
    return None


async def resolve_place(
    client: OGCClient, catalog: Catalog, name: str, *, prefer_wfs: bool = True
) -> Place | None:
    """Resolve one place name to an extent, WFS boundaries first."""
    name = (name or "").strip()
    if not name:
        return None

    # Explicit coordinates: "36.8,-1.3" or a full bbox "w,s,e,n"
    if bbox := parse_coordinates(name):
        return Place(name=name, kind="custom", bbox=bbox, source="user")

    if prefer_wfs:
        try:
            if place := await wfs_lookup(client, catalog, name):
                return place
        except Exception:  # noqa: BLE001 - boundary lookup is best-effort
            pass
    return gazetteer_lookup(name)


def parse_coordinates(value: str) -> BBox | None:
    """Accept 'lon,lat' (point, buffered) or 'w,s,e,n' (bbox)."""
    parts = [p.strip() for p in (value or "").split(",")]
    try:
        numbers = [float(p) for p in parts]
    except ValueError:
        return None

    if len(numbers) == 2:
        lon, lat = numbers
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            return None
        return BBox(west=lon - 0.1, south=lat - 0.1, east=lon + 0.1, north=lat + 0.1)
    if len(numbers) == 4:
        w, s, e, n = numbers
        if w > e or s > n:
            return None
        return BBox(west=w, south=s, east=e, north=n)
    return None
