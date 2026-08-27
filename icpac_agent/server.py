#!/usr/bin/env python3
"""ICPAC climate agent - MCP server entry point.

    python server.py                       # stdio (for Claude Desktop / Code)
    python server.py --transport streamable-http --port 8080
    python server.py --selftest             # check config and feeds, then exit
    python server.py --find-boundaries      # which layer to use for admin areas
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from icpac import __version__                       # noqa: E402
from icpac.catalog import load_catalog              # noqa: E402
from icpac.config import settings                   # noqa: E402
from icpac.mcp_compat import SDK_MAJOR, build_server, run_server  # noqa: E402
from icpac.ogc.client import OGCClient              # noqa: E402
from icpac.ogc.wcs import HAVE_RASTERIO             # noqa: E402
from icpac.tools import INSTRUCTIONS, register      # noqa: E402


def configure_logging() -> None:
    """Keep stderr readable.

    An MCP server's stderr is surfaced in the client's logs, and httpx logs
    every OGC request at INFO - which for one comparison is dozens of lines
    of URL-wrapped noise. Set ICPAC_LOG_LEVEL=DEBUG to see them when
    diagnosing a feed.
    """
    level = (os.getenv("ICPAC_LOG_LEVEL") or "WARNING").upper()
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
    if level not in {"DEBUG", "INFO"}:
        for noisy in ("httpx", "httpcore", "hpack", "rasterio", "urllib3"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def create_server():
    server = build_server(
        name="icpac-climate-agent", instructions=INSTRUCTIONS, version=__version__
    )
    return register(server)


async def selftest() -> int:
    """Report configuration and live-feed health without starting the server."""
    print(f"ICPAC climate agent {__version__}  (MCP SDK {SDK_MAJOR}.x)")
    print(f"raster zonal statistics: {'rasterio available' if HAVE_RASTERIO else 'WMS sampling only (no rasterio)'}")

    if not settings.configured:
        print("\nNo endpoints configured.")
        print("  set ICPAC_ENDPOINTS=name=https://<host>/geoserver/ows")
        print("  or   ICPAC_OGC_URL=https://<host>/geoserver/ows")
        return 1

    print(f"\nendpoints ({len(settings.endpoints)}):")
    for endpoint in settings.endpoints:
        auth = " [auth]" if (endpoint.auth or endpoint.token) else ""
        print(f"  {endpoint.name}: {endpoint.url} {','.join(endpoint.services)}{auth}")

    async with OGCClient.create() as client:
        catalog = await load_catalog(client, force=True)

    print("\nfeed status:")
    failures = 0
    for report in catalog.reports:
        mark = {"ok": "  ok  ", "empty": " empty", "error": " ERROR", "skipped": " skip "}[
            report.status
        ]
        if report.status == "error":
            failures += 1
        print(f" [{mark}] {report.endpoint}/{report.service}"
              f" {report.elapsed_ms:>5}ms  {report.detail}")

    unique = {layer.id for layer in catalog.layers.values()}
    print(f"\n{len(unique)} distinct layers discovered")
    if unique:
        for hit in catalog.search("rainfall drought vegetation hazard", limit=5):
            print(f"  {hit.layer.id:<48} {hit.layer.service:<4} {hit.layer.title[:40]}")
    return 1 if failures and not unique else 0


async def find_boundaries(limit: int = 25) -> int:
    """Show which WFS layers could serve as administrative boundaries.

    Boundary-layer naming varies enough between deployments that automatic
    detection is unreliable, so this inspects the candidates directly -
    fetching a couple of features from each and printing the attributes
    that carry place names, with example values. Whichever layer lists the
    units you analyse is the one to put in ICPAC_BOUNDARY_LAYER.
    """
    if not settings.configured:
        print("No endpoints configured; set ICPAC_ENDPOINTS first.")
        return 1

    from icpac.geo import NAME_FIELDS, admin_layers
    from icpac.ogc.client import OGCError
    from icpac.ogc.wfs import fetch_features

    async with OGCClient.create() as client:
        catalog = await load_catalog(client)
        candidates = admin_layers(catalog)

        if not candidates:
            print("No WFS layer matched the boundary search terms.")
            print("All WFS layers published here:\n")
            for layer in sorted(catalog.by_service("WFS"), key=lambda x: x.id)[:60]:
                print(f"  {layer.id:<56} {layer.title[:40]}")
            return 1

        print(f"{len(candidates)} candidate boundary layer(s); "
              f"inspecting the first {min(limit, len(candidates))}:\n")

        endpoints = {e.name: e for e in settings.endpoints}
        for layer in candidates[:limit]:
            endpoint = endpoints.get(layer.endpoint)
            if endpoint is None:
                continue
            print(f"  {layer.id}")
            print(f"    {layer.title or '(no title)'}")
            try:
                collection = await fetch_features(client, endpoint, layer, limit=3)
            except OGCError as exc:
                print(f"    [could not read: {exc}]\n")
                continue

            features = collection.get("features", [])
            if not features:
                print("    [no features returned]\n")
                continue

            props = features[0].get("properties") or {}
            named = {}
            for key in props:
                if key.lower() not in NAME_FIELDS:
                    continue
                values = [
                    str((f.get("properties") or {}).get(key, "")).strip()[:22]
                    for f in features[:3]
                ]
                values = [v for v in values if v]
                if values:                       # an all-empty column proves nothing
                    named[key] = values
            if named:
                for key, values in list(named.items())[:4]:
                    print(f"    {key:<14} e.g. {', '.join(values)}")
            else:
                print(f"    (no populated name attribute) columns: "
                      f"{', '.join(list(props)[:8])}")
            print()

        print("Geoportals often publish one boundary layer per country, so name")
        print("every layer covering the areas you analyse, comma-separated and in")
        print("priority order - the resolver tries each until one matches:")
        print(f'  $env:ICPAC_BOUNDARY_LAYER = "{",".join(c.id for c in candidates[:3])}"')
        print("or add ICPAC_BOUNDARY_LAYER=<id>,<id> to your .env")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="ICPAC climate agent (MCP server).")
    ap.add_argument(
        "--transport", default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="stdio for desktop clients; HTTP transports for a hosted deployment",
    )
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--selftest", action="store_true",
                    help="check configuration and live feeds, then exit")
    ap.add_argument("--find-boundaries", action="store_true",
                    help="show which WFS layers can serve as admin boundaries, "
                         "with their name attributes, then exit")
    ap.add_argument("--list-tools", action="store_true", help="print the tool surface as JSON")
    args = ap.parse_args()

    configure_logging()

    if args.selftest:
        return asyncio.run(selftest())

    if args.find_boundaries:
        return asyncio.run(find_boundaries())

    server = create_server()

    if args.list_tools:
        tools = asyncio.run(server.list_tools())
        print(json.dumps(
            [{"name": t.name, "description": (t.description or "").split("\n")[0]}
             for t in tools],
            indent=2,
        ))
        return 0

    if not settings.configured:
        print(
            "warning: no ICPAC endpoints configured - tools will return a "
            "configuration error until ICPAC_ENDPOINTS is set",
            file=sys.stderr,
        )

    run_server(server, args.transport, args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
