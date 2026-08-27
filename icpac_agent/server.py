#!/usr/bin/env python3
"""ICPAC climate agent - MCP server entry point.

    python server.py                       # stdio (for Claude Desktop / Code)
    python server.py --transport streamable-http --port 8080
    python server.py --selftest             # check config and feeds, then exit
"""

from __future__ import annotations

import argparse
import asyncio
import json
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
        for layer, score in catalog.search("rainfall drought vegetation hazard", limit=5):
            print(f"  {layer.id:<48} {layer.service:<4} {layer.title[:40]}")
    return 1 if failures and not unique else 0


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
    ap.add_argument("--list-tools", action="store_true", help="print the tool surface as JSON")
    args = ap.parse_args()

    if args.selftest:
        return asyncio.run(selftest())

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
