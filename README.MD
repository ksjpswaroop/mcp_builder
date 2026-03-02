
# MCP Template

## Executive summary

This repository is a **cursor-friendly template** for designing, implementing, validating, and releasing **Model Context Protocol (MCP)** servers using an opinionated `mcp.yaml` contract-first workflow. It is optimized for **incremental edits** (small diffs, fast feedback) and supports both **local stdio** servers and **remote Streamable HTTP** servers, with built-in guidance for security/privacy, observability, CI/CD, and rollback.

Primary references: **MCP Specification**, **MCP Registry docs**, **MCP Inspector**, **Semantic Versioning**, **OpenTelemetry/OTLP**, **SLSA**, and **SPDX** (linked at the end).

---

## Project purpose and scope

**Purpose**
- Provide a **single source of truth** (`mcp.yaml`) for your MCP server’s *contract*, *security posture*, *release policy*, and *deployment targets*.
- Make it easy to spin up new MCP servers that expose **tools**, **resources**, and/or **prompts** while staying aligned with MCP lifecycle, version negotiation, and transport rules.

**In scope**
- Contract-first design (schemas, risk tags, data classes)
- Local stdio + Streamable HTTP examples
- Contract snapshots + automated validation gates
- CI/CD + release + registry publishing patterns
- Security/privacy mitigations (e.g., Origin validation, no secrets in logs)

**Out of scope / unspecified constraints (you must decide)**
- Host UX (how tool consent is displayed and enforced)
- Secrets manager (env vars vs vault vs KMS)
- Container/orchestrator (Docker/Kubernetes/serverless)
- Enterprise IdP + OAuth provider configuration
- Multi-tenant identity model (tenant IDs, RBAC model, audit retention)

---

## Quickstart

### Prerequisites
- **Python 3.10+** (required by the `mcp` package). We recommend using **[uv](https://docs.astral.sh/uv/)** to create the venv and install dependencies (uv will use a suitable Python if installed).
- Node.js (for Inspector). The official Inspector currently requires **Node.js ^22.7.5**.
- Optional: Docker (Inspector container), GitHub Actions (CI/CD)

### Install uv (recommended)
One-line install (macOS/Linux):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`  
See [uv installation](https://docs.astral.sh/uv/getting-started/installation/) for other options.

### Install dependencies (Python)
**With uv (recommended):** From the repo root, uv creates a venv and installs dependencies (Python 3.10+ is used automatically if available).
```bash
uv sync
```
Then activate the venv and run commands:
```bash
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
python scripts/validate_template.py mcp.yaml
python examples/stdio/smoke_client.py
```
Or run without activating: `uv run python scripts/validate_template.py mcp.yaml`.

**With pip:** Requires Python 3.10+ on your PATH. Create a venv and install from `requirements.txt`:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

**If you see an SSL error** when using pip, try a different network or use uv instead. With uv you can also use `uv pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt` on trusted networks only.

### Run the local stdio example (fully automated smoke test)
This runs the stdio server **as a subprocess** and calls a tool.
```bash
uv run python examples/stdio/smoke_client.py
# or, with venv activated: python examples/stdio/smoke_client.py
```

### Run the Streamable HTTP example (server + smoke test)
Terminal A (start server):
```bash
uv run python -m examples.streamable_http.server
```

Terminal B (call a tool over HTTP):
```bash
uv run python examples/streamable_http/smoke_client.py
```

By default, the example serves MCP at:
- `http://localhost:8000/mcp`

### Run Inspector smoke tests

**Inspect the stdio server (Inspector launches the process):**
```bash
npx @modelcontextprotocol/inspector uv run python examples/stdio/server.py
```

**Inspect the Streamable HTTP server (server runs separately):**
```bash
# Terminal A
uv run python -m examples.streamable_http.server

# Terminal B (opens the UI; connect to streamable-http URL in the sidebar)
npx @modelcontextprotocol/inspector
```
Then in the Inspector UI, choose **Transport: streamable-http** and set:
- URL: `http://localhost:8000/mcp`

---

## File layout

```text
.
├─ pyproject.toml                   # Project and dependencies (uv/pip)
├─ requirements.txt                 # Pip fallback; kept in sync with pyproject.toml
├─ mcp.yaml                         # Primary contract and governance template
├─ server.json                      # Registry metadata (generated/mapped from mcp.yaml)
├─ schemas/
│  └─ mcp-template.schema.json      # JSON Schema for validating mcp.yaml
├─ contracts/
│  └─ contract.snapshot.json        # Generated snapshot from tools/resources/prompts listings
├─ examples/
│  ├─ stdio/
│  │  ├─ server.py                  # Minimal stdio server
│  │  └─ smoke_client.py            # Subprocess client smoke test
│  └─ streamable_http/
│     ├─ server.py                  # Minimal Streamable HTTP server
│     └─ smoke_client.py            # HTTP client smoke test
├─ scripts/
│  ├─ validate_template.py          # Validates mcp.yaml against JSON Schema + policy rules
│  ├─ snapshot_contract.py          # Produces contracts/contract.snapshot.json
│  └─ generate_server_json.py       # Emits server.json (optional: merged with manual fields)
└─ .github/workflows/
   ├─ ci.yml                        # Lint + unit + contract + integration gates
   └─ publish-mcp.yml               # Optional: publish artifact + server.json to MCP Registry
```

---

## Core developer loop (cursor-style incremental edits)

1. **Edit `mcp.yaml` in small diffs** (one tool/resource/prompt at a time).
2. **Validate locally**:
   ```bash
   uv run python scripts/validate_template.py mcp.yaml
   ```
3. **Run smoke tests** (stdio + HTTP as relevant):
   ```bash
   uv run python examples/stdio/smoke_client.py
   uv run python examples/streamable_http/smoke_client.py
   ```
4. **Refresh contract snapshot** (commit it for reviewable diffs):
   ```bash
   uv run python scripts/snapshot_contract.py
   ```
5. **PR review** (security + contract checks).
6. **Release** with SemVer + publish (artifact first, then registry metadata if used).

### Adding tools

Use the **FastMCP** API and the `@mcp.tool()` decorator on your server (see [DataCamp MCP tutorial](https://www.datacamp.com/tutorial/mcp-model-context-protocol)). For each new tool: (1) implement it in code with typed parameters and a docstring; (2) add an entry under `spec.contractSnapshot.tools` in `mcp.yaml`; (3) run `python scripts/snapshot_contract.py` to refresh `contracts/contract.snapshot.json`; (4) run `validate_template.py` and the smoke tests. Full steps and examples: [docs/adding-tools.md](docs/adding-tools.md).

---

## Scenario playbook (summary)

### Transport vs recommended auth (quick table)

| Transport | Best for | Recommended auth | Key hard rules |
|---|---|---|---|
| **stdio** | Local tools/resources (per-user process) | env-based creds | Never write non-protocol output to stdout; log to stderr |
| **Streamable HTTP** | Remote/shared servers (multi-client) | OAuth-based (or equivalent) | Validate `Origin` to prevent DNS rebinding; authenticate; handle `MCP-Protocol-Version` |

### Capability choices
- **Tools**: “do something” (side effects possible). Use strict input schemas + human-in-the-loop tags for risky tools.
- **Resources**: “read context” (browseable content + templates). Validate resource URIs and enforce ACLs.
- **Prompts**: “interaction templates” (govern like code; version them).

### Progress vs tasks
- Use **progress** for long tool calls that still complete in one request-response flow.
- Use **tasks** (experimental in newer MCP revisions) for durable, pollable, deferred results—bind task access to the caller’s authorization context.

### Multitenancy + data classification
- Decide a classification vocabulary (e.g., `public/internal/confidential` + tags `pii/secrets`).
- Enforce it consistently in tool execution, resource reads, logging, and task access controls.

---

## CI/CD and release guidance

### Versioning rules (SemVer)
- **MAJOR**: breaking contract changes (rename tools, incompatible schema changes)
- **MINOR**: backward-compatible additions (new tools/resources/fields)
- **PATCH**: bugfixes / no contract change

### Registry publishing notes
- Registry versions are **immutable** per version string; update by publishing a new version.
- Unpublish/delete may not be supported (plan rollback via version pinning).

### GitHub Actions snippet (registry publishing)
Minimal skeleton (see MCP Registry “GitHub Actions” docs for full examples):
```yaml
name: Publish to MCP Registry
on:
  push:
    tags: ["v*"]
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v5
      - name: Install mcp-publisher
        run: |
          curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher
      - name: Login (OIDC)
        run: ./mcp-publisher login github-oidc
      - name: Publish server.json
        run: ./mcp-publisher publish
```

Supply-chain recommendations:
- Emit **SLSA provenance** and an **SPDX SBOM** during build (store alongside releases).

---

## Security and privacy controls

Minimum controls to implement and validate:
- **No secrets/PII in logs** (enforce redaction; treat tool outputs as untrusted input).
- **Origin validation** for HTTP (DNS rebinding mitigation) and bind to localhost when running locally.
- **Strict input validation** for tools; reject additionalProperties where appropriate.
- **URI validation + ACLs** for resources and templates.
- Avoid “token passthrough” patterns; use proper OAuth flows and consent when proxying.

---

## Observability and telemetry

Recommended baseline:
- Implement MCP **logging capability** and honor client log level control.
- Implement **progress notifications** for long operations.
- Export telemetry via **OpenTelemetry** with **OTLP** (traces/metrics/logs) for production.

---

## Rollback, migration, and testing/validation checklist

**Rollback**
- Prefer “revert to previous version” (package pin or deployment rollback).
- For registry: publish a new fixed version; mark broken versions deprecated in your own changelog.

**Migration**
- Keep old tools for one minor cycle when possible; deprecate before removing.
- Provide a short migration note in `CHANGELOG.md` for breaking changes.

**Validation checklist (run in CI)**
- `mcp.yaml` passes JSON Schema + policy rules
- Contract snapshot updated and reviewed
- stdio smoke test runs (no stdout pollution)
- HTTP smoke test runs (Origin validation + auth strategy documented)
- Logs are redaction-safe
- SemVer bump matches contract diff severity

---

## Contributing

- Use small PRs: one contract edit + implementation + snapshot update.
- Include/adjust tests for every new tool/resource.
- Run Inspector smoke tests before requesting review.

---

## License

Choose a license (e.g., Apache-2.0 or MIT) for the template and examples. Add `LICENSE` and ensure `server.json` reflects it if publishing.

---

## Primary references (by name)

- **MCP Specification** (Architecture, Lifecycle, Transports, Tools/Resources/Prompts, Logging, Pagination, Tasks)
- **MCP Inspector** (official visual testing tool)
- **MCP Registry** (About, FAQ, Versioning, GitHub Actions publishing)
- **Semantic Versioning 2.0.0**
- **OpenTelemetry** and **OTLP Specification**
- **SLSA v1.2 Specification**
- **SPDX (ISO/IEC 5962:2021) Overview**
```