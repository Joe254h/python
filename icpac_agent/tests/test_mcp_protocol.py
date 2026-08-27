"""End-to-end MCP protocol test.

Spawns the real server as a subprocess over stdio, speaks MCP to it exactly
as Claude Desktop or Claude Code would, and asserts the tools answer against
the stub OGC feeds. This is the test that proves the *integration*, not just
the internals.

Run: python3 tests/test_mcp_protocol.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from stub_ogc import StubServer  # noqa: E402

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

EXPECTED_TOOLS = {
    "list_endpoints", "search_layers", "describe_layer", "refresh_catalog",
    "resolve_place", "get_layer_value", "layer_time_series", "compare_places",
    "get_features", "render_map",
}


def payload(result) -> dict:
    """Unwrap a tool result into the dict the tool returned."""
    if getattr(result, "structuredContent", None):
        content = result.structuredContent
        # SDKs wrap a bare return value under "result".
        return content.get("result", content) if isinstance(content, dict) else content
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
    return {}


async def main() -> int:
    failures: list[str] = []

    def check(label: str, condition: bool, detail: str = "") -> None:
        if condition:
            print(f"  PASS  {label}")
        else:
            failures.append(label)
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    with StubServer() as stub:
        env = dict(os.environ)
        env["ICPAC_ENDPOINTS"] = f"stub={stub.url}|services=WMS,WFS,WCS"
        env["ICPAC_SAMPLE_GRID"] = "4"
        env["PYTHONPATH"] = str(ROOT)

        params = StdioServerParameters(
            command=sys.executable, args=[str(ROOT / "server.py")], env=env, cwd=str(ROOT)
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                info = await session.initialize()
                check(
                    "initialize handshake",
                    info.server_info.name == "icpac-climate-agent",
                    f"got {info.server_info.name!r}",
                )
                check(
                    "instructions describe the workflow",
                    "compare_places" in (info.instructions or ""),
                )

                listed = await session.list_tools()
                names = {tool.name for tool in listed.tools}
                check("all ten tools advertised", names == EXPECTED_TOOLS,
                      f"missing {EXPECTED_TOOLS - names}, extra {names - EXPECTED_TOOLS}")
                check(
                    "every tool has a description",
                    all(tool.description for tool in listed.tools),
                )

                endpoints = payload(await session.call_tool("list_endpoints", {}))
                check("list_endpoints sees the stub feeds",
                      endpoints.get("total_layers", 0) >= 4, json.dumps(endpoints)[:200])
                check("all three services report ok",
                      all(s["status"] == "ok" for s in endpoints.get("sources", [])))

                found = payload(await session.call_tool(
                    "search_layers", {"query": "drought index"}))
                matches = found.get("matches", [])
                check("search finds the SPI layer",
                      bool(matches) and "spi" in matches[0]["id"],
                      json.dumps(matches[:1])[:200])

                described = payload(await session.call_tool(
                    "describe_layer", {"layer_id": "stub:icpac:spi_3month"}))
                check("describe_layer reports the time axis",
                      described.get("time_count") == 4, str(described.get("time_count")))
                check("describe_layer lists both services",
                      described.get("services") == ["WCS", "WMS"],
                      str(described.get("services")))

                place = payload(await session.call_tool(
                    "resolve_place", {"name": "Turkana"}))
                check("resolve_place uses published boundaries",
                      place.get("exact_boundary") is True, json.dumps(place)[:200])

                value = payload(await session.call_tool(
                    "get_layer_value",
                    {"layer_id": "stub:icpac:spi_3month", "place": "Wajir"}))
                stats = value.get("statistics", {})
                check("get_layer_value returns statistics",
                      stats.get("mean") is not None and stats.get("valid", 0) > 0,
                      json.dumps(stats)[:200])
                check("the reading states its method",
                      stats.get("method") in {"wcs-coverage", "wms-sample"},
                      str(stats.get("method")))

                compared = payload(await session.call_tool(
                    "compare_places",
                    {
                        "layer_id": "stub:icpac:spi_3month",
                        "places": ["Turkana", "Marsabit", "Wajir", "Mandera"],
                        "question": "which counties are worst hit by drought?",
                    },
                ))
                order = [p["place"] for p in compared.get("places", [])]
                check("compare_places ranks driest first",
                      order[:1] == ["Mandera"] and order[-1:] == ["Turkana"], str(order))
                check("compare_places writes a narrative",
                      "Mandera" in compared.get("narrative", ""),
                      compared.get("narrative", "")[:160])
                check("compare_places attaches provenance",
                      len(compared.get("sources", [])) == 4)

                features = payload(await session.call_tool(
                    "get_features", {"layer_id": "stub:icpac:flood_alerts"}))
                check("get_features reads hazard polygons",
                      features.get("returned") == 1, json.dumps(features)[:200])

                image = await session.call_tool(
                    "render_map",
                    {"layer_id": "stub:icpac:spi_3month", "place": "Turkana"})
                kinds = {getattr(b, "type", "") for b in image.content}
                check("render_map returns an image", "image" in kinds, str(kinds))

                missing = payload(await session.call_tool(
                    "describe_layer", {"layer_id": "nope"}))
                check("unknown layers fail with suggestions",
                      "error" in missing and "did_you_mean" in missing)

    print("\n" + ("all green" if not failures else f"{len(failures)} failing"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
