#!/usr/bin/env python3
"""See the agent work, with no ICPAC credentials and no network.

Starts the stub OGC server from the test suite, spawns the real MCP server
as a subprocess, and drives it over the MCP protocol exactly as Claude
Desktop would - printing each step so you can watch a question turn into a
ranked, sourced answer.

    python demo.py                 # against the built-in stub feeds
    python demo.py --live          # against whatever ICPAC_ENDPOINTS points at
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


def _colour_supported() -> bool:
    """Older Windows consoles print escape codes as literal garbage."""
    if os.getenv("NO_COLOR") or not sys.stdout.isatty():
        return False
    if os.name != "nt":
        return True
    # Windows Terminal and ANSICON handle VT; plain conhost needs enabling.
    if os.getenv("WT_SESSION") or os.getenv("ANSICON"):
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        # 7 = stdout handle, 0x0004 = ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return bool(kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7))
    except Exception:  # noqa: BLE001 - no colour is a fine outcome
        return False


if _colour_supported():
    BOLD, DIM, CYAN, GREEN, YELLOW, RED, RESET = (
        "\033[1m", "\033[2m", "\033[36m", "\033[32m", "\033[33m", "\033[31m", "\033[0m"
    )
else:
    BOLD = DIM = CYAN = GREEN = YELLOW = RED = RESET = ""


def _unicode_supported() -> bool:
    """Legacy Windows consoles use cp437 and would mangle box drawing."""
    try:
        "─█·→•…".encode(sys.stdout.encoding or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


UNICODE = _unicode_supported()
HRULE, FULL, EMPTY, ARROW, DOT, ELLIPSIS = (
    ("─", "█", "·", "→", "•", "…") if UNICODE else ("-", "#", ".", ">", "*", "...")
)

SEVERITY_COLOUR = {
    "extreme": RED, "high": RED, "moderate": YELLOW, "low": CYAN,
    "none": GREEN, "unknown": DIM,
}


def rule(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{HRULE * 74}{RESET}")
    print(f"{BOLD}{title}{RESET}")
    print(f"{CYAN}{HRULE * 74}{RESET}")


def call_line(tool: str, args: dict) -> None:
    shown = ", ".join(f"{k}={json.dumps(v)}" for k, v in args.items())
    print(f"\n{DIM}{ARROW} {tool}({shown}){RESET}")


def payload(result) -> dict:
    if getattr(result, "structuredContent", None):
        content = result.structuredContent
        return content.get("result", content) if isinstance(content, dict) else content
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
    return {}


def bar(value: float, low: float, high: float, width: int = 22) -> str:
    if high - low < 1e-9:
        return HRULE * width
    filled = int(round(width * (value - low) / (high - low)))
    return FULL * max(1, filled) + EMPTY * (width - max(1, filled))


async def run(session: ClientSession, live: bool) -> None:
    info = await session.initialize()
    tools = (await session.list_tools()).tools

    rule("1. The client connects and sees what the agent can do")
    print(f"server   : {info.server_info.name} v{info.server_info.version}")
    print(f"tools    : {len(tools)}")
    for tool in tools:
        print(f"  {GREEN}{DOT}{RESET} {tool.name:<20} {DIM}{(tool.description or '')[:52]}{ELLIPSIS}{RESET}")

    # -- 2. what feeds are alive ---------------------------------------
    rule("2. Which live feeds are answering right now?")
    call_line("list_endpoints", {})
    endpoints = payload(await session.call_tool("list_endpoints", {}))
    if "error" in endpoints:
        print(f"{RED}{endpoints['error']}{RESET}\n  fix: {endpoints.get('fix')}")
        return
    for e in endpoints["endpoints"]:
        print(f"  {e['name']}: {e['url']}")
    for source in endpoints["sources"]:
        mark = GREEN + "ok" + RESET if source["status"] == "ok" else RED + source["status"] + RESET
        print(f"  [{mark}] {source['endpoint']}/{source['service']:<4}"
              f" {source['elapsed_ms']:>5}ms  {source['detail']}")
    print(f"\n  {BOLD}{endpoints['total_layers']}{RESET} distinct layers discovered "
          f"{DIM}(read from GetCapabilities, nothing hard-coded){RESET}")

    # -- 3. find a layer by describing it -------------------------------
    rule("3. Ask for a concept, not a layer name")
    query = "drought index" if not live else "rainfall anomaly"
    call_line("search_layers", {"query": query})
    found = payload(await session.call_tool("search_layers", {"query": query, "limit": 5}))
    matches = found.get("matches", [])
    if not matches:
        print(f"{YELLOW}no layers matched {query!r} on this server{RESET}")
        return
    for match in matches:
        print(f"  {match['score']:>5.2f}  {match['id']:<40} {DIM}{match['service']}"
              f"  {match['title'][:34]}{RESET}")
    layer_id = matches[0]["id"]

    # -- 4. inspect it ---------------------------------------------------
    rule("4. Check the layer before trusting a number from it")
    call_line("describe_layer", {"layer_id": layer_id})
    described = payload(await session.call_tool("describe_layer", {"layer_id": layer_id}))
    print(f"  title        : {described.get('title')}")
    print(f"  family       : {described.get('family')}  {DIM}(decides the severity scale){RESET}")
    print(f"  services     : {', '.join(described.get('services', []))}")
    print(f"  real pixels  : {'yes (WCS)' if described.get('readable_pixels') else 'no - WMS sampling only'}")
    print(f"  time steps   : {described.get('time_count')}  latest {described.get('time_latest') or '-'}")

    # -- 5. resolve a place ---------------------------------------------
    rule("5. Turn a place name into an extent")
    for name in ("Turkana", "Ethiopia"):
        call_line("resolve_place", {"name": name})
        place = payload(await session.call_tool("resolve_place", {"name": name}))
        if "error" in place:
            print(f"  {YELLOW}{place['error']}{RESET}")
            continue
        exact = place.get("exact_boundary")
        label = (f"{GREEN}exact boundary{RESET} from {place['source']}" if exact
                 else f"{YELLOW}approximate box{RESET} from {place['source']}")
        print(f"  {place['name']:<12} {label}")
        print(f"  {'':12} bbox {['%.2f' % v for v in place['bbox']]}")
        for note in place.get("notes", [])[:3]:
            print(f"  {'':12} {DIM}{note[:72]}{RESET}")

    # -- 6. the actual question -----------------------------------------
    places = ["Turkana", "Marsabit", "Wajir", "Mandera"]
    rule("6. The question: which of these areas is worst affected?")
    call_line("compare_places", {"layer_id": layer_id, "places": places})
    result = payload(await session.call_tool(
        "compare_places",
        {"layer_id": layer_id, "places": places,
         "question": "which counties are worst affected?"},
    ))

    ranked = [p for p in result.get("places", []) if p.get("value") is not None]
    if ranked:
        values = [p["value"] for p in ranked]
        low, high = min(values), max(values)
        units = result.get("units", "")
        print(f"\n  {'#':<3}{'area':<12}{'value':>9}  {'severity':<10}{'conf':>5}  scale")
        for entry in ranked:
            colour = SEVERITY_COLOUR.get(entry["severity"], "")
            print(f"  {entry['rank']:<3}{entry['place']:<12}{entry['value']:>9.3g}"
                  f"  {colour}{entry['severity']:<10}{RESET}{entry['confidence']:>5.2f}"
                  f"  {DIM}{bar(entry['value'], low, high)}{RESET}")
        if units:
            print(f"  {DIM}units: {units}{RESET}")

    print(f"\n{BOLD}  Answer:{RESET}")
    for line in wrap(result.get("narrative", "(none)"), 68):
        print(f"    {line}")

    for warning in result.get("warnings", []):
        print(f"  {YELLOW}! {warning}{RESET}")

    # -- 7. provenance ---------------------------------------------------
    rule("7. Where every number came from")
    for source in result.get("sources", [])[:8]:
        mark = GREEN + "ok" + RESET if source["status"] == "ok" else RED + source["status"] + RESET
        print(f"  [{mark}] {source['service']:<4} {source['layer']:<34}"
              f" {source['elapsed_ms']:>5}ms  {source['detail']}")

    if ranked:
        print(f"\n{DIM}  Method shown per reading: 'wcs-coverage' = real source pixels;{RESET}")
        print(f"{DIM}  'wms-sample' = coarse grid over the rendered layer.{RESET}")
        print(f"  this run used: {BOLD}{ranked[0]['method']}{RESET}")

    # -- 8. vector + imagery ---------------------------------------------
    rule("8. Hazard polygons and a rendered map")
    hazards = payload(await session.call_tool("search_layers", {"query": "flood hazard alerts"}))
    hazard_layers = [m for m in hazards.get("matches", []) if m["service"] == "WFS"]
    if hazard_layers:
        hid = hazard_layers[0]["id"]
        call_line("get_features", {"layer_id": hid})
        features = payload(await session.call_tool("get_features", {"layer_id": hid, "limit": 5}))
        print(f"  {features.get('returned', 0)} feature(s) from {hid}")
        for feature in features.get("features", [])[:3]:
            print(f"    {json.dumps(feature['properties'])[:66]}")
    else:
        print(f"  {DIM}no WFS hazard layer published here{RESET}")

    call_line("render_map", {"layer_id": layer_id, "place": "Turkana"})
    image = await session.call_tool("render_map", {"layer_id": layer_id, "place": "Turkana"})
    for block in image.content:
        if getattr(block, "type", "") == "image":
            # SDK 2.x renamed mimeType -> mime_type.
            mime = getattr(block, "mime_type", None) or getattr(block, "mimeType", "image/png")
            size = len(getattr(block, "data", "") or "")
            print(f"  received a {mime} image ({size} base64 chars) "
                  f"{DIM}- an LLM client displays this inline{RESET}")
            break
    else:
        print(f"  {YELLOW}no image returned{RESET}")


def wrap(text: str, width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


async def main(live: bool) -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    stub = None

    if not live:
        from stub_ogc import StubServer

        stub = StubServer()
        stub.__enter__()
        env["ICPAC_ENDPOINTS"] = f"stub={stub.url}|services=WMS,WFS,WCS"
        env["ICPAC_SAMPLE_GRID"] = "4"
        print(f"{DIM}Using built-in stub ICPAC feeds at {stub.url}")
        print(f"(pass --live to run against ICPAC_ENDPOINTS instead){RESET}")
    else:
        if not env.get("ICPAC_ENDPOINTS") and not env.get("ICPAC_OGC_URL"):
            print(f"{RED}--live needs ICPAC_ENDPOINTS set (see .env.example){RESET}")
            return 1
        print(f"{DIM}Using live feeds: {env.get('ICPAC_ENDPOINTS') or env.get('ICPAC_OGC_URL')}{RESET}")

    try:
        params = StdioServerParameters(
            command=sys.executable, args=[str(ROOT / "server.py")], env=env, cwd=str(ROOT)
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await run(session, live)
        print(f"\n{GREEN}{BOLD}Demo complete.{RESET} "
              f"{DIM}Same server, same protocol Claude Code speaks.{RESET}\n")
        return 0
    finally:
        if stub is not None:
            stub.__exit__(None, None, None)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Watch the ICPAC agent answer a question.")
    ap.add_argument("--live", action="store_true",
                    help="use ICPAC_ENDPOINTS instead of the built-in stub feeds")
    raise SystemExit(asyncio.run(main(ap.parse_args().live)))
