# Adding tools and functions to your MCP server

This guide explains how to add new tools (and functions) to your MCP server using the **FastMCP** API from the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), and how to keep the template contract (`mcp.yaml`) and contract snapshot in sync.

## Pattern: FastMCP + `@mcp.tool()`

1. **Create the server** with `FastMCP` and register tools with the `@mcp.tool()` decorator on **async** or sync functions.
2. **Typed parameters** define the tool’s input schema for clients (and the LLM).
3. **Docstring** is the tool description shown to the LLM.
4. **Return type** documents the tool’s output (e.g. `str`, `dict`, `List[dict]`).
5. **Logging**: use `print(..., file=sys.stderr)` so stdout stays strict JSON-RPC.

### Example

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server", json_response=True)

@mcp.tool()
def fetch_pr(repo_owner: str, repo_name: str, pr_number: int) -> dict:
    """Fetch changes from a GitHub pull request."""
    # ... call your logic ...
    return {"title": "...", "changes": [...]}

@mcp.tool()
async def create_notion_page(title: str, content: str) -> str:
    """Create a Notion page with the given title and content."""
    # ... async implementation ...
    return f"Created page: {title}"
```

See the [DataCamp MCP tutorial](https://www.datacamp.com/tutorial/mcp-model-context-protocol) for a full walkthrough (PR review server with GitHub + Notion).

## Steps after adding a tool

1. **Implement the tool** in your server (e.g. `examples/stdio/server.py` or your own module) using `@mcp.tool()`.
2. **Update `mcp.yaml`** under `spec.contractSnapshot.tools` with an entry for the new tool, e.g.:
   - `name`: tool name (must match the function name exposed to MCP).
   - `inputSchemaDialect`: e.g. `"2020-12"`.
   - `outputSchemaProvided`: `true` if you return structured data with a known shape.
   - `risk`: `"low"` | `"medium"` | `"high"` (align with `spec.surface.risk.humanInLoopRequiredFor` for high-risk tools).
3. **Regenerate the contract snapshot** (optional but recommended for diff-friendly review):
   ```bash
   python scripts/snapshot_contract.py
   ```
   This overwrites `contracts/contract.snapshot.json` from the running stdio example server.
4. **Validate and run smoke tests**:
   ```bash
   python scripts/validate_template.py mcp.yaml
   python examples/stdio/smoke_client.py
   python examples/streamable_http/smoke_client.py   # after starting the HTTP server
   ```

## Summary

| Step | Action |
|------|--------|
| 1 | Add the tool in code with `@mcp.tool()` (typed params + docstring). |
| 2 | Add or update the tool in `mcp.yaml` under `spec.contractSnapshot.tools`. |
| 3 | Run `snapshot_contract.py` to refresh `contracts/contract.snapshot.json`. |
| 4 | Run `validate_template.py` and smoke tests before opening a PR. |

This keeps your contract-first workflow consistent and makes tool changes reviewable via small diffs.
