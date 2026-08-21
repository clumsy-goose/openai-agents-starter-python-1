"""
text_statistics agent route — EdgeOne Makers
========================================

File path agents/text_statistics/index.py maps to **POST /text_statistics**.

Because `edgeone.json` sets `agents.mcp.enabled = true`, the runtime also
auto-registers this route as the MCP tool `text_statistics`. No MCP-specific
wiring is written here, yet the tool shows up in the MCP client's tool list.

The behaviour lives in `agents/_tool_core.py` and is shared with the in-agent
tool used by /chat, so the two can never diverge.
"""

from .._tool_core import text_statistics_def
from .._tool_route import create_tool_route

handler = create_tool_route(text_statistics_def)
