"""
Smoke test for the Streamable HTTP MCP server.
Connects to http://localhost:8000/mcp, initializes, calls echo tool, asserts success.
Start the server first in another terminal: python examples/streamable_http/server.py
Run from repo root: python examples/streamable_http/smoke_client.py
"""
from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

DEFAULT_URL = "http://localhost:8000/mcp"


async def run(url: str = DEFAULT_URL) -> None:
    async with streamable_http_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("echo", arguments={"message": "smoke-test-http"})
            if not result.content:
                raise AssertionError("echo returned no content")
            text = getattr(result.content[0], "text", None) if result.content else None
            if text != "smoke-test-http":
                raise AssertionError(f"echo expected 'smoke-test-http', got {text!r}")
    print("streamable HTTP smoke test passed.", file=sys.stderr)


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    try:
        asyncio.run(run(url))
        return 0
    except Exception as e:
        print(
            f"streamable HTTP smoke test failed: {e}\n"
            "Ensure the server is running: python examples/streamable_http/server.py",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
