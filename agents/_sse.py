"""
SSE streaming helper — private module (starts with _), not mapped as a route.

Provides the small boilerplate for formatting Server-Sent Events frames so
handlers only need to `yield` the formatted string.

EdgeOne Makers Python agent handlers are async generators that yield SSE
strings; the runtime pipes each yielded string into the HTTP response body.

Usage:
    async def handler(context):
        yield sse_event("text_delta", {"delta": "..."})
        yield sse_event("tool_called", {"tool": "get_weather"})
        yield sse_event("done", {"stopped": False})
"""

import json
from typing import Any


def sse_event(event: str, data: Any) -> str:
    """Format a single SSE event frame: `event: <name>\\ndata: <json>\\n\\n`."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
