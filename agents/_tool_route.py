"""
Tool-route handler factory — private module (starts with _), not a route.

Turns a `ToolDef` into an EdgeOne Makers agent handler so that each tool can be
deployed as its own agent route (`agents/<tool>/index.py`). Because
`edgeone.json` enables `agents.mcp`, the runtime then auto-registers every
such route as an individual MCP tool — which is exactly what these routes are
here to demonstrate.

Why the response is SSE and not plain JSON
------------------------------------------
The MCP adapter aggregates an agent's SSE stream into the tool result's
`content.text`. A plain JSON return from an agent route is parsed as empty by
the adapter. So the payload is emitted as `text_delta` frames, which both the
MCP adapter and the browser SSE client understand.

Known limitation: MCP tool arguments
-------------------------------------
The runtime advertises the SAME fixed inputSchema for every auto-registered
agent route:

    { message: string, session_id?: string }

It does NOT introspect the handler to derive a per-tool schema. So an MCP
client following that schema sends `{ message: "Beijing" }`, which will fail
validation here because `get_weather` expects `{ city }`. Two ways to call a
tool successfully today:

  - direct HTTP POST with the structured body, e.g. {"city": "Beijing"}
  - over MCP by putting JSON in `message`, e.g. {"message": "{\\"city\\":\\"Beijing\\"}"}

Validation failures are reported through the SSE stream (not as HTTP 400) so
that the reason is visible to an MCP client instead of an empty tool result.
"""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Callable, Dict

from ._logger import create_logger
from ._sse import sse_event
from ._tool_core import ToolDef


def _resolve_args(raw_body: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise whatever the caller sent into this tool's argument object.

    1. `{ arguments: {...} }`  — some MCP clients nest tool arguments.
    2. `{ message: "<json>" }` — the MCP auto-generated schema. Only honoured
       when the string parses as a JSON object; free text is left alone so the
       validation error below names the field that is actually missing.
    3. the body itself         — a direct HTTP POST with structured args.
    """
    if not isinstance(raw_body, dict):
        return {}

    # 1. Unwrap `{ arguments: {...} }`.
    body = raw_body["arguments"] if isinstance(raw_body.get("arguments"), dict) else raw_body

    # 2. Accept structured args smuggled through `message` as JSON.
    msg = body.get("message")
    if isinstance(msg, str):
        try:
            parsed = json.loads(msg)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            # not JSON — fall through and let validation report the real problem
            pass

    # 3. Use the body as-is.
    return body


def create_tool_route(tool: ToolDef) -> Callable[[Any], AsyncGenerator[str, None]]:
    """Build an EdgeOne Makers agent handler (async generator) for a single tool."""
    logger = create_logger(tool.name)

    async def handler(context: Any) -> AsyncGenerator[str, None]:
        raw_body = context.request.body if isinstance(context.request.body, dict) else {}
        args = _resolve_args(raw_body)

        logger.log(f"[request] raw={json.dumps(raw_body, ensure_ascii=False)} "
                   f"resolved={json.dumps(args, ensure_ascii=False)}")

        ok, issues = tool.validate(args)
        if not ok:
            logger.error("[request] invalid arguments:", issues)
            # Report the failure through SSE rather than as an HTTP 400: the MCP
            # adapter only reads the aggregated stream, so a plain 400 body would
            # reach the client as an empty tool result with no explanation.
            yield sse_event("text_delta", {
                "delta": json.dumps({
                    "error": f"Invalid arguments for '{tool.name}'",
                    "tool": tool.name,
                    "issues": issues,
                    "received": args,
                }, ensure_ascii=False)
            })
            yield sse_event("done", {"stopped": False})
            return

        try:
            result = tool.execute(args)
            logger.log(f"[response] {str(result)[:120]}")
            # `tool_called` lets the browser UI light up the matching lamp; the
            # MCP adapter ignores it and only aggregates `text_delta` frames.
            yield sse_event("tool_called", {"tool": tool.name})
            yield sse_event("text_delta", {"delta": result})
        except Exception as e:  # noqa: BLE001
            logger.error(f"[response] error: {type(e).__name__}: {e}")
            yield sse_event("error", {"message": str(e), "name": type(e).__name__})
        finally:
            yield sse_event("done", {"stopped": False})

    return handler
