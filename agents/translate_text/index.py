"""
translate_text agent route — EdgeOne Makers
========================================

File path agents/translate_text/index.py maps to **POST /translate_text**.

Because `edgeone.json` sets `agents.mcp.enabled = true`, the runtime also
auto-registers this route as the MCP tool `translate_text`. No MCP-specific
wiring is written here, yet the tool shows up in the MCP client's tool list.

The behaviour lives in `agents/_tool_core.py` and is shared with the in-agent
tool used by /chat, so the two can never diverge.
"""

from .._tool_core import translate_text_def
from .._tool_route import create_tool_route

handler = create_tool_route(translate_text_def)
