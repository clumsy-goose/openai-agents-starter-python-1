"""
Agent Tools — private module (starts with _), not mapped as a route.

Adapts the shared definitions in `_tool_core.py` into OpenAI Agents SDK
`function_tool` objects for the /chat agent.

There is intentionally no tool logic in this file. Each tool's behaviour lives
in `_tool_core.py` and is reused by two surfaces:

  - this module → tools callable by the agent during a /chat run
  - `agents/<tool>/index.py` → the same tool as a standalone agent route,
    which the runtime auto-registers as an individual MCP tool

To add a tool: define it in `_tool_core.py`, add it to `ALL_TOOL_DEFS`, and
create an `agents/<tool>/index.py` route if it should be exposed over MCP.
"""

from typing import Annotated

from agents import function_tool

from ._tool_core import (
    get_weather_def,
    get_clothing_advice_def,
    translate_text_def,
    text_statistics_def,
)


# Each function_tool below delegates to the shared _tool_core definition, so the
# behaviour can never drift from the standalone agent routes.

@function_tool
def get_weather(city: Annotated[str, "The city to get weather for"]) -> str:
    """Get the current weather for a specified city."""
    return get_weather_def.execute({"city": city})


@function_tool
def get_clothing_advice(
    weather: Annotated[str, "The weather description (JSON or plain text)"],
) -> str:
    """Give clothing advice based on weather conditions."""
    return get_clothing_advice_def.execute({"weather": weather})


@function_tool
def translate_text(
    text: Annotated[str, "The text to translate"],
    target_language: Annotated[str, "Target language code, e.g. en, ja, fr, ko, de"],
) -> str:
    """Translate text to the specified language."""
    return translate_text_def.execute({"text": text, "target_language": target_language})


@function_tool
def text_statistics(text: Annotated[str, "The text to analyze"]) -> str:
    """Analyze text and return statistics like character count and word count."""
    return text_statistics_def.execute({"text": text})
