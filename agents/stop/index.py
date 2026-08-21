"""
Stop handler — EdgeOne Makers
========================================

The file path agents/stop/index.py is auto-mapped to **POST /stop**.

Given a conversation_id, this triggers the platform runtime's abort flow:
  1. Set the target conversation's cancel signal (asyncio.Event.set()).
  2. Cancel the corresponding asyncio.Task (raises CancelledError).
  3. The streaming loop in chat/index.py observes the signal and stops
     the LLM call.

Because `edgeone.json` sets `agents.mcp.enabled = true`, the runtime exposes
this route as the MCP tool `cancel_run`.

The LLM call is genuinely interrupted — we don't just close the SSE connection.

IMPORTANT: The stop request must NOT carry the same `makers-conversation-id`
header as the chat request, otherwise the runtime overwrites the chat's signal.
The target conversation_id is passed only via the request body.
"""

from .._logger import create_logger

logger = create_logger("stop")


async def handler(context):
    """Abort the running agent for this conversation."""
    body = context.request.body or {}
    conversation_id = body.get("conversation_id")
    logger.log(f"conversation_id: {conversation_id}")

    if not conversation_id:
        logger.error("conversation_id is required")
        return {
            "status_code": 400,
            "body": {
                "status": "error",
                "message": "conversation_id is required",
            },
        }

    # Trigger platform runtime abort — this actually interrupts the LLM call.
    result = context.utils.abort_active_run(conversation_id)
    logger.log("abort_active_run result:", {
        "aborted": result.aborted,
        "conversation_id": result.conversation_id,
        "run_id": result.run_id,
    })

    return {
        "status": "aborting" if result.aborted else "idle",
        "conversationId": result.conversation_id or conversation_id,
        "runId": result.run_id,
        "aborted": result.aborted,
    }
