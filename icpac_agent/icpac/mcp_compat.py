"""Bridge over the MCP SDK rename.

MCP 2.x renamed ``FastMCP`` to ``MCPServer`` and moved the helpers. ICPAC
deployments will not all upgrade on the same day, so the server is written
once against this shim and runs on either.
"""

from __future__ import annotations

from typing import Any

SDK_MAJOR = 2

try:  # MCP 2.x
    from mcp.server.mcpserver import Image, MCPServer as _Server
except ImportError:  # pragma: no cover - MCP 1.x
    from mcp.server.fastmcp import FastMCP as _Server, Image  # type: ignore[no-redef]

    SDK_MAJOR = 1

Server = _Server
ImageContent = Image


def build_server(name: str, instructions: str, version: str) -> Any:
    """Construct the server object for whichever SDK is installed."""
    try:
        return Server(name=name, instructions=instructions, version=version)
    except TypeError:  # 1.x builds without a version kwarg
        return Server(name=name, instructions=instructions)


def run_server(server: Any, transport: str, host: str, port: int) -> None:
    """Start the server on the requested transport."""
    if transport == "stdio":
        server.run(transport="stdio")
        return

    # HTTP transports take their bind address from settings on both SDKs.
    for attribute, value in (("host", host), ("port", port)):
        holder = getattr(server, "settings", server)
        try:
            setattr(holder, attribute, value)
        except (AttributeError, ValueError):
            pass
    server.run(transport=transport)
