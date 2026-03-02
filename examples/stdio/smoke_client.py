"""
Smoke test for the stdio MCP server.
Spawns the server as a subprocess, initializes, calls the echo tool, and asserts success.
Run from repo root: python examples/stdio/smoke_client.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure repo root is on path when running as script
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def get_server_params() -> StdioServerParameters:
    server_script = _repo_root / "examples" / "stdio" / "server.py"
    return StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        env=os.environ.copy(),
    )


async def run() -> None:
    server_params = get_server_params()
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("echo", arguments={"message": "smoke-test"})
            if not result.content:
                raise AssertionError("echo returned no content")
            text = getattr(result.content[0], "text", None) if result.content else None
            if text != "smoke-test":
                raise AssertionError(f"echo expected 'smoke-test', got {text!r}")
    print("stdio smoke test passed.", file=sys.stderr)


def main() -> int:
    try:
        asyncio.run(run())
        return 0
    except Exception as e:
        print(f"stdio smoke test failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
