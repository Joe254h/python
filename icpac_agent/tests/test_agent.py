"""Test suite. Run: python3 tests/test_agent.py   (or pytest tests -q)

Everything runs against an in-process stub OGC server, so the suite needs
no network and no ICPAC credentials, while still exercising the real
capabilities parsing, place resolution, sampling and ranking code.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from stub_ogc import BOUNDARIES, StubServer, stub_value  # noqa: E402

from icpac import analysis, catalog as catalog_mod, config, geo  # noqa: E402
from icpac.config import Endpoint  # noqa: E402
from icpac.models import BBox, MetricResult, Place, SampleStats  # noqa: E402
from icpac.ogc.capabilities import expand_time_extent, parse_wcs, parse_wfs, parse_wms  # noqa: E402
from icpac.ogc.client import OGCClient, service_exception  # noqa: E402
from icpac.ogc.wfs import geometry_bbox  # noqa: E402


def _point_it(server: StubServer) -> None:
    """Aim the agent at the stub and clear cached state."""
    config.settings.endpoints = [Endpoint("stub", server.url, ("WMS", "WFS", "WCS"))]
    config.settings.sample_grid = 4          # keep the suite quick
    catalog_mod.reset_cache()


async def _catalog(server: StubServer):
    client = OGCClient.create()
    cat = await catalog_mod.load_catalog(client, force=True)
    return client, cat


# ----------------------------------------------------------- unit: parse ---

def test_time_extent_instants_and_ranges():
    assert expand_time_extent("2026-01-01,2026-01-02") == ["2026-01-01", "2026-01-02"]

    monthly = expand_time_extent("2026-05-01T00:00:00Z/2026-08-01T00:00:00Z/P1M")
    assert len(monthly) == 4
    assert monthly[0].startswith("2026-05-01")
    assert monthly[-1].startswith("2026-07-30") or monthly[-1].startswith("2026-08")

    assert expand_time_extent("") == []


def test_time_extent_is_capped_and_keeps_recent():
    daily = expand_time_extent("1990-01-01T00:00:00Z/2026-01-01T00:00:00Z/P1D")
    assert len(daily) <= 400
    assert daily[-1].startswith("2026-01-01")


def test_wms_capabilities_parsing():
    from stub_ogc import WMS_CAPS

    layers = parse_wms(WMS_CAPS.encode(), "stub")
    names = {layer.name for layer in layers}
    assert {"icpac:spi_3month", "icpac:rfe_dekad", "icpac:admin1"} <= names

    spi = next(layer for layer in layers if layer.name == "icpac:spi_3month")
    assert spi.title.startswith("SPI 3-month")
    assert spi.temporal and len(spi.time_values) == 4
    assert spi.queryable and "spi_default" in spi.styles
    assert spi.bbox is not None and spi.bbox.contains(37.0, 2.0)   # inherited from parent


def test_wfs_and_wcs_capabilities_parsing():
    from stub_ogc import WCS_CAPS, WFS_CAPS

    wfs = parse_wfs(WFS_CAPS.encode(), "stub")
    assert {layer.name for layer in wfs} == {"icpac:admin1", "icpac:flood_alerts"}
    assert wfs[0].bbox is not None and wfs[0].bbox.north == 23.0

    wcs = parse_wcs(WCS_CAPS.encode(), "stub")
    assert [layer.name for layer in wcs] == ["icpac:spi_3month"]
    assert wcs[0].service == "WCS"


def test_service_exception_detection():
    from stub_ogc import EXCEPTION

    assert "Unknown layer" in service_exception(EXCEPTION.encode(), "text/xml")
    assert service_exception(b'{"ok": true}', "application/json") == ""
    assert service_exception(b"\x89PNG\r\n", "image/png") == ""


# -------------------------------------------------------------- unit: geo ---

def test_gazetteer_resolves_counties_and_countries():
    turkana = geo.gazetteer_lookup("Turkana")
    assert turkana and turkana.country == "Kenya" and turkana.bbox.contains(35.5, 3.0)

    assert geo.gazetteer_lookup("turkana county") is not None    # suffix tolerated
    assert geo.gazetteer_lookup("Ethiopia").kind == "country"
    assert geo.gazetteer_lookup("Nowherestan") is None


def test_coordinate_parsing():
    point = geo.parse_coordinates("36.8,-1.3")
    assert point and point.contains(36.8, -1.3)

    box = geo.parse_coordinates("34,1,37,5")
    assert box and box.west == 34 and box.north == 5

    assert geo.parse_coordinates("not,coords") is None
    assert geo.parse_coordinates("400,900") is None              # out of range


def test_geometry_bbox_handles_nested_rings():
    polygon = {"type": "Polygon", "coordinates": [[[34, 1], [37, 1], [37, 5], [34, 5], [34, 1]]]}
    box = geometry_bbox(polygon)
    assert box and box.as_list() == [34.0, 1.0, 37.0, 5.0]
    assert geometry_bbox({}) is None


def test_bbox_helpers():
    box = BBox(west=34, south=1, east=38, north=5)
    assert box.centre == (36.0, 3.0)
    assert box.contains(36, 3) and not box.contains(40, 3)
    assert box.intersects(BBox(west=37, south=2, east=42, north=6))
    assert not box.intersects(BBox(west=45, south=2, east=48, north=6))
    assert box.buffered(0.1).west < box.west


# --------------------------------------------------------- unit: analysis ---

def test_severity_by_indicator_family():
    assert analysis.classify("spi", -2.4) == "extreme"
    assert analysis.classify("spi", -1.2) == "moderate"
    assert analysis.classify("spi", 0.1) == "none"
    assert analysis.classify("vci", 8) == "extreme"
    assert analysis.classify("vci", 60) == "none"
    assert analysis.classify("generic", 5) == "unknown"
    assert analysis.classify("spi", None) == "unknown"


def test_severity_falls_back_to_percent_of_normal():
    assert analysis.classify("generic", 12.0, anomaly_pct=40.0) == "high"
    assert analysis.classify("generic", 12.0, anomaly_pct=100.0) == "none"


def test_family_detection_prefers_the_longer_hint():
    from icpac.models import Layer

    plain = Layer(id="a", name="chirps_rfe", endpoint="e", service="WMS", title="Rainfall estimate")
    anomaly = Layer(id="b", name="rfe_anom", endpoint="e", service="WMS",
                    title="Rainfall anomaly percent of normal")
    assert analysis.detect_family(plain) == "rainfall"
    assert analysis.detect_family(anomaly) == "rainfall_anomaly"


def test_summarise_statistics():
    stats = analysis.summarise([1.0, 2.0, 3.0, 4.0], 6, method="wcs-coverage", units="mm")
    assert stats.valid == 4 and stats.count == 6
    assert stats.mean == 2.5 and stats.minimum == 1.0 and stats.maximum == 4.0
    assert stats.median == 2.5 and stats.usable

    empty = analysis.summarise([], 6, method="wms-sample")
    assert not empty.usable and empty.mean is None


def test_confidence_rewards_coverage_and_method():
    full = analysis.summarise([1.0] * 90, 100, method="wcs-coverage")
    sparse = analysis.summarise([1.0] * 5, 100, method="wms-sample")
    assert analysis.confidence(full, 12) > analysis.confidence(sparse, 12)
    assert 0.0 <= analysis.confidence(sparse) <= 1.0
    assert analysis.confidence(analysis.summarise([], 10, method="wms-sample")) == 0.0


def test_trend_detects_direction():
    from icpac.models import SeriesPoint

    falling = [SeriesPoint(time=str(i), value=10.0 - i) for i in range(6)]
    rising = [SeriesPoint(time=str(i), value=float(i)) for i in range(6)]
    assert analysis.trend_per_step(falling) < 0
    assert analysis.trend_per_step(rising) > 0
    assert analysis.trend_per_step(falling[:2]) is None


def test_ranking_puts_worst_condition_first():
    metrics = [
        MetricResult(place="Dry", metric="spi", value=-2.2),
        MetricResult(place="Mid", metric="spi", value=-0.9),
        MetricResult(place="Wet", metric="spi", value=0.4),
        MetricResult(place="Unknown", metric="spi", value=None),
    ]
    ranked = analysis.rank_metrics(metrics, "spi")
    assert [m.place for m in ranked[:3]] == ["Dry", "Mid", "Wet"]
    assert ranked[0].rank == 1
    assert ranked[-1].place == "Unknown" and ranked[-1].rank == 0


def test_build_metric_computes_anomaly_and_flags_extent_quality():
    place = Place(name="Turkana", bbox=BBox(west=34, south=1, east=37, north=5),
                  source="gazetteer")
    stats = analysis.summarise([40.0] * 20, 20, method="wms-sample", units="mm")
    stats.layer, stats.place = "icpac:rfe", "Turkana"

    metric = analysis.build_metric(place, stats, "rainfall", baseline=80.0)
    assert metric.anomaly == -40.0
    assert metric.anomaly_pct == 50.0
    assert any("gazetteer" in line for line in metric.evidence)


# ------------------------------------------------------ end-to-end: live ---

def test_catalog_discovers_all_three_services():
    with StubServer() as server:
        _point_it(server)

        async def run():
            client, cat = await _catalog(server)
            try:
                assert {r.status for r in cat.reports} == {"ok"}
                assert len(cat.by_service("WMS")) == 3
                assert len(cat.by_service("WFS")) == 2
                assert len(cat.by_service("WCS")) == 1

                spi = cat.get("icpac:spi_3month")
                assert spi is not None
                assert set(cat.siblings(spi)) == {"WMS", "WCS"}
                assert cat.get("spi_3month") is not None      # bare-name lookup
                assert cat.get("no_such_layer") is None
            finally:
                await client.aclose()

        asyncio.run(run())


def test_search_ranks_by_concept_not_just_words():
    with StubServer() as server:
        _point_it(server)

        async def run():
            client, cat = await _catalog(server)
            try:
                drought = cat.search("drought conditions")
                assert drought and "spi" in drought[0][0].name

                rain = cat.search("rainfall")
                assert rain and "rfe" in rain[0][0].name

                admin = cat.search("county boundaries", service="WFS")
                assert admin and admin[0][0].name == "icpac:admin1"

                assert cat.search("zzzz nothing") == []
            finally:
                await client.aclose()

        asyncio.run(run())


def test_place_resolution_prefers_published_boundaries():
    with StubServer() as server:
        _point_it(server)

        async def run():
            client, cat = await _catalog(server)
            try:
                place = await geo.resolve_place(client, cat, "Turkana")
                assert place is not None
                assert place.source.startswith("wfs")
                assert place.bbox.as_list() == BOUNDARIES["Turkana"]

                # A place the stub does not publish falls back to the gazetteer.
                fallback = await geo.resolve_place(client, cat, "Ethiopia")
                assert fallback is not None and fallback.source == "gazetteer"
            finally:
                await client.aclose()

        asyncio.run(run())


def test_sampling_reads_real_coverage_pixels():
    """The production path: WCS GeoTIFF decoded to real pixel statistics."""
    from icpac.ogc.wcs import HAVE_RASTERIO

    if not HAVE_RASTERIO:
        print("    (skipped: rasterio not installed)")
        return

    with StubServer() as server:
        _point_it(server)

        async def run():
            client, cat = await _catalog(server)
            try:
                layer = cat.get("icpac:spi_3month")
                place = await geo.resolve_place(client, cat, "Turkana")
                stats, report = await analysis.sample_place(client, cat, layer, place)

                assert report.status == "ok" and report.service == "WCS"
                assert stats.method == "wcs-coverage"
                # 24x24 grid with one nodata pixel masked out.
                assert stats.count == 576 and stats.valid == 575
                assert stats.minimum <= stats.mean <= stats.maximum
                assert stats.minimum > -9000, "nodata sentinel leaked into the statistics"
            finally:
                await client.aclose()

        asyncio.run(run())


def test_sampling_falls_back_to_wms_when_wcs_fails():
    import stub_ogc

    with StubServer() as server:
        _point_it(server)
        stub_ogc.SERVE_COVERAGES = False
        try:
            async def run():
                client, cat = await _catalog(server)
                try:
                    layer = cat.get("icpac:spi_3month")
                    place = await geo.resolve_place(client, cat, "Turkana")
                    stats, report = await analysis.sample_place(client, cat, layer, place)

                    assert report.status == "ok" and report.service == "WMS"
                    assert stats.method == "wms-sample"
                    assert stats.usable and stats.valid == stats.count == 16
                    assert "GetFeatureInfo" in stats.note
                finally:
                    await client.aclose()

            asyncio.run(run())
        finally:
            stub_ogc.SERVE_COVERAGES = True


def test_compare_places_ranks_the_driest_first():
    """The stub's field gets drier eastward, so Mandera must outrank Turkana."""
    with StubServer() as server:
        _point_it(server)
        from icpac.tools import register

        class Collector:
            def __init__(self):
                self.fns = {}

            def tool(self, name="", description="", **kw):
                def wrap(fn):
                    self.fns[name or fn.__name__] = fn
                    return fn
                return wrap

        collector = Collector()
        register(collector)

        result = asyncio.run(
            collector.fns["compare_places"](
                "icpac:spi_3month", ["Turkana", "Marsabit", "Wajir", "Mandera"]
            )
        )

        # Ids are endpoint-qualified, so two feeds can publish the same name.
        assert result["layer"] == "stub:icpac:spi_3month"
        assert result["metric"] == "spi"
        order = [p["place"] for p in result["places"]]
        assert order[0] == "Mandera" and order[-1] == "Turkana"
        assert result["places"][0]["rank"] == 1

        for entry in result["places"]:
            assert entry["value"] is not None
            assert entry["severity"] in {"extreme", "high", "moderate", "low", "none"}
            assert 0.0 <= entry["confidence"] <= 1.0
        assert "Mandera" in result["narrative"]
        assert result["sources"] and all(s["status"] == "ok" for s in result["sources"])


def test_tools_report_configuration_and_lookup_errors():
    with StubServer() as server:
        _point_it(server)
        from icpac.tools import register

        class Collector:
            def __init__(self):
                self.fns = {}

            def tool(self, name="", description="", **kw):
                def wrap(fn):
                    self.fns[name or fn.__name__] = fn
                    return fn
                return wrap

        collector = Collector()
        register(collector)
        fns = collector.fns

        missing = asyncio.run(fns["describe_layer"]("icpac:does_not_exist"))
        assert "error" in missing and "did_you_mean" in missing

        described = asyncio.run(fns["describe_layer"]("icpac:spi_3month"))
        assert described["time_count"] == 4
        assert described["services"] == ["WCS", "WMS"]
        assert described["family"] == "spi"

        features = asyncio.run(fns["get_features"]("icpac:flood_alerts", limit=5))
        assert features["returned"] == 1
        assert features["features"][0]["properties"]["severity"] == "high"

        endpoints = asyncio.run(fns["list_endpoints"]())
        assert endpoints["total_layers"] >= 4

        series = asyncio.run(fns["layer_time_series"]("icpac:spi_3month", "Wajir", steps=3))
        assert len(series["series"]) == 3
        assert series["baseline_mean"] is not None

        # No endpoints configured at all.
        config.settings.endpoints = []
        catalog_mod.reset_cache()
        unconfigured = asyncio.run(fns["search_layers"]("rainfall"))
        assert "no ICPAC endpoints configured" in unconfigured["error"]


def test_stub_field_is_actually_monotonic():
    """Guards the ranking test: the fixture must vary the way it claims."""
    west = stub_value("icpac:spi_3month", 35.0, 3.0)
    east = stub_value("icpac:spi_3month", 41.0, 3.0)
    assert east < west


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print("\n" + ("all green" if not failures else f"{failures} failing"))
    raise SystemExit(1 if failures else 0)
