# Changelog

All notable changes to this template are documented here.

## [Unreleased]

## [0.1.0] - 2026-03-02

### Added

- Initial MCP server template with contract-first `mcp.yaml`.
- JSON Schema for template validation (`schemas/mcp-template.schema.json`).
- Scripts: `validate_template.py`, `snapshot_contract.py`, `generate_server_json.py`.
- Stdio and Streamable HTTP example servers (FastMCP + `@mcp.tool()`).
- Smoke tests for both transports.
- CI workflow (validate + smoke tests) and optional publish workflow for MCP Registry.
- Docs: Adding tools guide (`docs/adding-tools.md`).
