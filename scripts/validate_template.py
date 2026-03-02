#!/usr/bin/env python3
"""
Validate mcp.yaml against the JSON Schema and optional policy rules.
Exit 0 only if all checks pass; print errors to stderr and exit non-zero otherwise.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "PyYAML is required. Install dependencies first:\n"
        "  python3 -m venv .venv && source .venv/bin/activate\n"
        "  pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(2)

try:
    import jsonschema
except ImportError:
    print(
        "jsonschema is required. Install dependencies first:\n"
        "  pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(2)


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_schema(schema_dir: Path) -> dict:
    schema_path = schema_dir / "mcp-template.schema.json"
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def policy_checks(data: dict) -> list[str]:
    errors = []
    spec = data.get("spec") or {}

    # lifecycle.state in enum (schema already enforces; extra sanity check)
    state = spec.get("lifecycle", {}).get("state")
    if state and state not in ("draft", "review", "deployed", "deprecated"):
        errors.append(f"spec.lifecycle.state must be one of draft|review|deployed|deprecated, got: {state!r}")

    # auth.mode present
    auth = spec.get("security", {}).get("auth", {})
    if not auth.get("mode"):
        errors.append("spec.security.auth.mode is required")

    # transport list non-empty
    transports = spec.get("protocol", {}).get("transports") or []
    if not transports:
        errors.append("spec.protocol.transports must have at least one transport")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    yaml_path = repo_root / "mcp.yaml"
    schema_dir = repo_root / "schemas"

    if len(sys.argv) > 1:
        yaml_path = Path(sys.argv[1]).resolve()
    if not yaml_path.exists():
        print(f"File not found: {yaml_path}", file=sys.stderr)
        return 1

    if not (schema_dir / "mcp-template.schema.json").exists():
        print(f"Schema not found: {schema_dir / 'mcp-template.schema.json'}", file=sys.stderr)
        return 1

    try:
        data = load_yaml(yaml_path)
    except Exception as e:
        print(f"Failed to load YAML: {e}", file=sys.stderr)
        return 1

    try:
        schema = load_schema(schema_dir)
    except Exception as e:
        print(f"Failed to load schema: {e}", file=sys.stderr)
        return 1

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"Schema validation failed: {e}", file=sys.stderr)
        return 1

    policy_errors = policy_checks(data)
    if policy_errors:
        for err in policy_errors:
            print(f"Policy error: {err}", file=sys.stderr)
        return 1

    print("Validation passed.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
