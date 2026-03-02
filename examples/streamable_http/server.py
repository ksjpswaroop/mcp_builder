"""
Minimal Streamable HTTP MCP server using FastMCP.
Same tools as stdio example; serves at http://localhost:8000/mcp.
Run: python -m examples.streamable_http.server  or  python examples/streamable_http/server.py
Then run smoke client in another terminal.
"""
from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example-weather-http", json_response=True)


@mcp.tool()
def get_weather_data(location: str, unit: str = "celsius") -> dict:
    """Get weather data for a location. Returns placeholder data for demo."""
    print(f"get_weather_data called: location={location!r}, unit={unit!r}", file=sys.stderr)
    return {
        "location": location,
        "unit": unit,
        "temperature": 22.0,
        "conditions": "sunny",
        "humidity": 45,
    }


@mcp.tool()
def echo(message: str) -> str:
    """Echo back the message. Useful for smoke tests."""
    print(f"echo called: {message!r}", file=sys.stderr)
    return message


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
