"""
get_clothing_advice agent route — EdgeOne Makers
========================================

File path agents/get_clothing_advice/index.py maps to **POST /get_clothing_advice**.

Because `edgeone.json` sets `agents.mcp.enabled = true`, the runtime also
auto-registers this route as the MCP tool `get_clothing_advice`. No MCP-specific
wiring is written here, yet the tool shows up in the MCP client's tool list.

The behaviour lives in `agents/_tool_core.py` and is shared with the in-agent
tool used by /chat, so the two can never diverge.
"""

from .._tool_core import get_clothing_advice_def
from .._tool_route import create_tool_route

handler = create_tool_route(get_clothing_advice_def)
