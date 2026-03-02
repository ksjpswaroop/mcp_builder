#!/usr/bin/env python3
"""
Emit server.json (MCP Registry metadata) by mapping from mcp.yaml.
Overwrites server.json by default; does not merge with existing file.
Run from repo root: python scripts/generate_server_json.py [--output PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MCP_YAML = REPO_ROOT / "mcp.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "server.json"
SERVER_JSON_SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_server_json(spec: dict) -> dict:
    identity = spec.get("identity", {})
    deployment = spec.get("deployment", {})
    local = deployment.get("local", {})
    stdio_cfg = local.get("stdio", {})
    env_vars = []
    for name, value in (stdio_cfg.get("env") or {}).items():
        if isinstance(value, str) and value.startswith("${ENV:"):
            env_vars.append({
                "name": name,
                "description": f"Environment variable: {name}",
                "isRequired": True,
                "isSecret": "secret" in name.lower() or "key" in name.lower() or "token" in name.lower(),
                "format": "string",
            })
    repo = identity.get("repository", {})
    packages = []
    if stdio_cfg:
        # Stdio package entry
        pkg = {
            "registryType": "pypi",
            "identifier": identity.get("mcpName", "").replace("/", "-").split("/")[-1] or "mcp-server",
            "version": identity.get("version", "0.1.0"),
            "transport": {"type": "stdio"},
        }
        if env_vars:
            pkg["environmentVariables"] = env_vars
        packages.append(pkg)
    return {
        "$schema": SERVER_JSON_SCHEMA,
        "name": identity.get("mcpName", ""),
        "title": identity.get("title", ""),
        "description": identity.get("description", ""),
        "version": identity.get("version", "0.1.0"),
        "repository": {
            "url": repo.get("url", ""),
            "source": repo.get("source", "git"),
        },
        "packages": packages if packages else [
            {
                "registryType": "pypi",
                "identifier": "mcp-template-example",
                "version": identity.get("version", "0.1.0"),
                "transport": {"type": "stdio"},
            }
        ],
        "_meta": {
            "io.modelcontextprotocol.registry/publisher-provided": {
                "tool": "mcp-template",
                "version": "0.1.0",
            }
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate server.json from mcp.yaml")
    parser.add_argument("input", nargs="?", default=str(DEFAULT_MCP_YAML), help="Path to mcp.yaml")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help="Output path for server.json")
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1
    try:
        data = load_yaml(input_path)
    except Exception as e:
        print(f"Failed to load YAML: {e}", file=sys.stderr)
        return 1
    spec = data.get("spec") or {}
    server_json = build_server_json(spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(server_json, f, indent=2)
    print(f"Wrote {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
