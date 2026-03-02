#!/usr/bin/env python3
"""
Produce contracts/contract.snapshot.json from the stdio server's tools/list
(and optionally resources/list, prompts/list). Drives the local stdio server
so no separate server process is needed.
Run from repo root: python scripts/snapshot_contract.py
"""
from __future__ import annotations

import json
import os
import sys
import asyncio
from datetime import datetime, timezone
from pathlib import Path

# Repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def get_server_params() -> StdioServerParameters:
    server_script = REPO_ROOT / "examples" / "stdio" / "server.py"
    return StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        env=os.environ.copy(),
    )


def tool_to_snapshot_entry(tool: object) -> dict:
    """Convert MCP Tool to contractSnapshot tools[] entry."""
    name = getattr(tool, "name", None) or ""
    description = getattr(tool, "description", None) or ""
    input_schema = getattr(tool, "inputSchema", None) or {}
    schema_dialect = (
        input_schema.get("$schema")
        or input_schema.get("schema", {}).get("$schema")
        or "2020-12"
    )
    if isinstance(schema_dialect, str) and "2020-12" in schema_dialect:
        dialect = "2020-12"
    else:
        dialect = "2020-12"
    return {
        "name": name,
        "description": description,
        "inputSchemaDialect": dialect,
        "outputSchemaProvided": True,
        "risk": "medium",
    }


async def collect_snapshot() -> dict:
    server_params = get_server_params()
    snapshot = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tools": [],
        "resources": [],
        "prompts": [],
    }
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            if tools_result and getattr(tools_result, "tools", None):
                snapshot["tools"] = [
                    tool_to_snapshot_entry(t) for t in tools_result.tools
                ]
            # Optional: list resources and prompts if server supports them
            try:
                res = await session.list_resources()
                if res and getattr(res, "resources", None):
                    snapshot["resources"] = [
                        {"uri": getattr(r, "uri", ""), "name": getattr(r, "name", "")}
                        for r in res.resources
                    ]
            except Exception:
                pass
            try:
                pr = await session.list_prompts()
                if pr and getattr(pr, "prompts", None):
                    snapshot["prompts"] = [
                        {"name": getattr(p, "name", "")} for p in pr.prompts
                    ]
            except Exception:
                pass
    return snapshot


def main() -> int:
    try:
        snapshot = asyncio.run(collect_snapshot())
    except Exception as e:
        print(f"Failed to collect contract snapshot: {e}", file=sys.stderr)
        return 1
    out_dir = REPO_ROOT / "contracts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "contract.snapshot.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
