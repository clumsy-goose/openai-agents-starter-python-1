"""
get_weather agent route — EdgeOne Makers
========================================

File path agents/get_weather/index.py maps to **POST /get_weather**.

Because `edgeone.json` sets `agents.mcp.enabled = true`, the runtime also
auto-registers this route as the MCP tool `get_weather`. This file exists
specifically to verify that auto-registration: no MCP-specific wiring is
written here, yet the tool shows up in the MCP client's tool list.

The behaviour itself lives in `agents/_tool_core.py` and is shared with the
in-agent tool used by /chat, so the two can never diverge.
"""

from .._tool_core import get_weather_def
from .._tool_route import create_tool_route

handler = create_tool_route(get_weather_def)
