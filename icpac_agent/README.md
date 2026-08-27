# ICPAC Climate Agent

An **MCP server** that puts ICPAC's live OGC feeds in front of an LLM, so a
plain-English question becomes a defensible answer with its provenance
attached.

```
> Which counties in northern Kenya are worst hit by drought right now?

  search_layers("drought")            → icpac:spi_3month  (SPI 3-month, 4 time steps)
  compare_places(spi_3month, [Turkana, Marsabit, Wajir, Mandera])

  SPI 3-month for 2026-08-01: Mandera is the most affected at -3.87 sigma
  (extreme), Turkana the least at -3.02. Between them: Wajir -3.60,
  Marsabit -3.28. Above the alert threshold: Mandera, Wajir, Marsabit,
  Turkana (all extreme). Mean confidence 0.71.
```

Nothing about ICPAC's layer names is hard-coded. The agent reads
`GetCapabilities` from whatever servers you point it at and works from what
they publish today.

---

## See it work (no credentials, no network)

```bash
cd icpac_agent
pip install -r requirements.txt
python demo.py
```

That starts a stub ICPAC server, spawns the real MCP server as a subprocess,
and drives it over the MCP protocol exactly as Claude Desktop would —
printing each step so you can watch a question become an answer:

```
6. The question: which of these areas is worst affected?

→ compare_places(layer_id="icpac:spi_3month", places=["Turkana", …])

  #  area            value  severity   conf  scale
  1  Mandera         -3.79  extreme    0.87  █·····················
  2  Wajir            -3.70  extreme   0.87  ██····················
  3  Marsabit        -3.28  extreme    0.87  ████████████··········
  4  Turkana         -2.83  extreme    0.87  ██████████████████████

7. Where every number came from
  [ok] WCS  icpac:spi_3month   342ms  575/576 pixels
  this run used: wcs-coverage
```

Once your endpoints are configured, `python demo.py --live` runs the same
script against the real feeds.

## Quick start

```bash
cp .env.example .env          # then set ICPAC_ENDPOINTS
python server.py --selftest   # check config + feed health before wiring it up
```

`--selftest` is the first thing to run when something is wrong. It separates
a configuration problem from an outage:

```
ICPAC climate agent 1.0.0  (MCP SDK 2.x)
raster zonal statistics: rasterio available

endpoints (1):
  geoportal: https://geoportal.icpac.net/geoserver/ows WMS,WFS,WCS

feed status:
 [  ok  ] geoportal/WMS   412ms  138 layers via WMS 1.3.0
 [  ok  ] geoportal/WFS   287ms  61 layers via WFS 2.0.0
 [ ERROR] geoportal/WCS  1204ms  HTTP 502 from geoportal
```

### Connecting a client

Claude Desktop / Claude Code (`claude_desktop_config.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "icpac": {
      "command": "python",
      "args": ["/srv/icpac_agent/server.py"],
      "env": {
        "ICPAC_ENDPOINTS": "geoportal=https://geoportal.icpac.net/geoserver/ows"
      }
    }
  }
}
```

Hosted, for the ICPAC platform to call over HTTP:

```bash
python server.py --transport streamable-http --host 0.0.0.0 --port 8080
```

---

## Configuration

One variable does the essential work:

```bash
ICPAC_ENDPOINTS=geoportal=https://geoportal.icpac.net/geoserver/ows
```

Several feeds at once, each optionally limited to certain services:

```bash
ICPAC_ENDPOINTS=geoportal=https://host-a/geoserver/ows;hazards=https://host-b/geoserver/ows|services=WMS,WFS
```

The name before `=` becomes the id prefix (`geoportal:icpac:spi_3month`), so
two servers can publish the same layer name without colliding. Credentials
(`ICPAC_OGC_USER`/`PASSWORD`, or `ICPAC_OGC_TOKEN`) apply to all endpoints.
See `.env.example` for the tuning knobs — timeouts, concurrency, cache TTLs,
sampling resolution.

---

## The tools

| Tool | What it does |
|---|---|
| `list_endpoints` | Configured feeds and which services are answering right now |
| `search_layers` | Rank live layers against a description — "rainfall anomaly", "flood hazard" |
| `describe_layer` | Title, abstract, extent, CRSs, time steps, styles, services |
| `refresh_catalog` | Force a capabilities re-read after a layer is published |
| `resolve_place` | Place name → extent, from WFS boundaries or the built-in gazetteer |
| `get_layer_value` | Statistics for one layer over one place at one time |
| `layer_time_series` | Sample across recent time steps; returns baseline and fitted trend |
| `compare_places` | **The main one.** Rank areas, classify severity, write the summary |
| `get_features` | WFS vector reads — hazard polygons, stations, admin units |
| `render_map` | WMS PNG for visual context alongside the numbers |

The intended flow is `search_layers` → `describe_layer` → `compare_places`;
the server's `instructions` tell the model exactly that, so it does not need
prompting.

---

## How a number is produced

**Reading values.** Two paths, and every result says which was used:

- `wcs-coverage` — GetCoverage returns a GeoTIFF, decoded to real pixels with
  nodata masked. This is the accurate path and needs `rasterio`.
- `wms-sample` — an N×N grid of `GetFeatureInfo` calls against the *rendered*
  layer. Needs no GDAL and works against any WMS, but it is coarse and reads
  the styled output rather than source data.

WCS is tried first; the fallback is automatic and reported, never silent.

**Resolving places.** WFS admin-boundary layers are authoritative and used
when available. Otherwise a built-in Greater Horn gazetteer (11 countries,
all 47 Kenyan counties, major Ethiopian/Somali/Ugandan/South Sudanese admin
areas, key basins) supplies an *approximate rectangle*. Results are labelled
`exact_boundary: true|false` — a mean over a bounding box is not a mean over
a county, and long, thin or coastal units suffer most.

The agent finds boundary layers by searching capabilities, which is
unreliable because deployments name them inconsistently. When it falls back
it says so and lists what it tried; set `ICPAC_BOUNDARY_LAYER` to the right
layer id (or pass `boundary_layer` to `resolve_place`) and the guessing
stops. **Do this before publishing any figure** — it is the single largest
accuracy difference available.

**Identifying a dataset across services.** GeoServer publishes WCS 2.0
coverage ids as `workspace__layer` while WMS and WFS use `workspace:layer`.
The agent normalises the two, so a coverage found via WCS still reaches the
WMS sibling that carries the time dimension and the rendered map.

**Classifying severity.** By indicator family, not by generic thresholds. SPI
and SPEI use the standard sigma bands; VCI/VHI use the 10/20/35 drought
classes; percent-of-normal rainfall uses 25/50/75/90. A family the agent does
not recognise returns `"unknown"` rather than inventing a class.

**Ranking.** Worst-affected first, which is direction-aware: for SPI, VCI,
NDVI and rainfall a *lower* value is worse, so the ordering inverts relative
to a plain sort.

**Confidence.** 0–1 from sample coverage, absolute sample count, series depth,
and a penalty for the WMS fallback. Read it as "how much would I stake on this
number", not as a statistical confidence interval.

---

## Interpreting the output honestly

- **A bounding-box mean is not a zonal statistic.** Wire up a WFS boundary
  layer before publishing figures. `resolve_place` tells you which you got.
- **The WMS fallback samples rendered pixels**, so its values are quantised to
  the layer's colour ramp. Install `rasterio` for anything quotable.
- **Time steps come from the server.** If a layer's latest step is three weeks
  old, so is the answer — `describe_layer` shows `time_latest`.
- **Severity classes are conventions**, not thresholds ICPAC has endorsed for
  operational alerting. Check them against your own bulletin definitions
  before they drive a decision.
- **`unknown` severity means the family was not recognised**, not that
  conditions are normal.

Every tool returns a `sources` array — endpoint, service, status, latency,
cache hit — so any figure can be traced back to the request that produced it.

---

## Architecture

```
icpac_agent/
├── server.py              # MCP entry point (stdio / SSE / streamable-http)
└── icpac/
    ├── tools.py           # the 10 MCP tools
    ├── catalog.py         # capabilities discovery, search, concept vocabulary
    ├── geo.py             # place → extent (WFS boundaries, then gazetteer)
    ├── analysis.py        # statistics, anomalies, severity, ranking, narration
    ├── models.py          # Layer, Place, SampleStats, MetricResult, …
    ├── mcp_compat.py      # bridges MCP SDK 1.x (FastMCP) and 2.x (MCPServer)
    ├── config.py          # endpoints and tuning from the environment
    └── ogc/
        ├── client.py      # retries, TTL cache, ServiceException detection
        ├── capabilities.py# WMS/WFS/WCS capabilities parsing, both generations
        ├── wms.py         # GetMap, GetFeatureInfo, grid sampling
        ├── wfs.py         # GetFeature → GeoJSON
        └── wcs.py         # GetCoverage → pixels
```

Three decisions worth knowing about:

**Capabilities parsing is namespace-agnostic and version-tolerant.** Tags are
matched after stripping the namespace, and each service falls back through
older protocol versions (WMS 1.3.0 → 1.1.1, WFS 2.0.0 → 1.1.0 → 1.0.0, WCS
2.0.1 → 1.1.1 → 1.0.0). A GeoServer upgrade should not break the agent.

**OGC errors arrive as HTTP 200.** Servers return a `ServiceException` XML body
with a success status, so every response is checked for one; otherwise a
failure would sail through as valid data.

**The MCP SDK renamed `FastMCP` to `MCPServer` in 2.x.** `mcp_compat.py`
bridges both, so the server runs on whichever version a deployment pins.

### Adding a tool

```python
@server.tool(name="drought_alert_summary", description="…")
async def drought_alert_summary(region: str) -> dict:
    async def body(client, catalog):
        layer = catalog.get("icpac:spi_3month")
        place = await resolve_place(client, catalog, region)
        stats, report = await sample_place(client, catalog, layer, place)
        return {"statistics": stats.model_dump(), "sources": _reports([report])}
    return await _with_client(body)
```

`_with_client` handles the client lifecycle and catalogue loading; retries,
caching and error isolation come from the OGC layer.

---

## Tests

```bash
python tests/test_agent.py          # 25 tests - parsing, geo, analysis, tools
python tests/test_mcp_protocol.py   # 18 checks - real MCP stdio round-trip
```

Both run against an in-process stub OGC server (`tests/stub_ogc.py`), so they
need no network and no ICPAC credentials while still exercising the real
capabilities parsing, boundary resolution, GeoTIFF decoding and ranking code.
The stub serves a genuine GeoTIFF when `rasterio` is present — including a
nodata pixel, so masking is covered — and can be switched to refuse
`GetCoverage` to test the WMS fallback.

`test_mcp_protocol.py` spawns `server.py` as a subprocess and speaks MCP to it
exactly as Claude Desktop would. That is the test that proves the integration
rather than the internals.
