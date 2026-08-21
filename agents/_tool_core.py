"""
Tool core logic — private module (starts with _), not mapped as a route.

Single source of truth for what each tool actually *does*. Both consumers
share these definitions, so behaviour can never drift between them:

  1. `_tools.py`        wraps them as OpenAI Agents SDK `function_tool` objects,
                        so the /chat agent can call them during a run.
  2. `agents/<name>/`   route handlers expose each one as a standalone agent
                        route, which the EdgeOne Makers runtime then
                        auto-registers as an individual MCP tool.

Replacing mock data with a real implementation means editing only the
`execute` body here — both surfaces pick the change up automatically.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple


@dataclass
class ToolParam:
    """A single tool parameter descriptor."""
    name: str
    description: str
    required: bool = True


@dataclass
class ToolDef:
    """Definition of a tool shared by the in-agent tool and the standalone route."""
    # Tool name — also the MCP tool name once exposed as a route.
    name: str
    description: str
    params: List[ToolParam]
    execute: Callable[[Dict[str, Any]], str]

    def validate(self, args: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]]]:
        """Validate incoming args against required params.

        Returns (ok, issues). issues is a list of {path, message}.
        """
        issues: List[Dict[str, str]] = []
        for p in self.params:
            if p.required:
                val = args.get(p.name)
                if val is None or (isinstance(val, str) and val.strip() == ""):
                    issues.append({
                        "path": p.name,
                        "message": f"'{p.name}' is required",
                    })
        return (len(issues) == 0, issues)


# ========== Tool: Get Weather ==========
def _get_weather(args: Dict[str, Any]) -> str:
    """Get the current weather for a specified city."""
    # TODO: Replace with real weather API (e.g. OpenWeatherMap, wttr.in)
    city = args.get("city", "")
    mock_weather = {
        "city": city,
        "condition": "Sunny",
        "temperature": {"min": 18, "max": 25, "unit": "°C"},
        "wind": "Light breeze",
    }
    return json.dumps(mock_weather, ensure_ascii=False)


get_weather_def = ToolDef(
    name="get_weather",
    description="Get the current weather for a specified city.",
    params=[ToolParam("city", "The city to get weather for")],
    execute=_get_weather,
)


# ========== Tool: Get Clothing Advice ==========
def _get_clothing_advice(args: Dict[str, Any]) -> str:
    """Give clothing advice based on weather conditions."""
    # TODO: Replace with more sophisticated logic or an external service
    weather = args.get("weather", "")
    if re.search(r"(3[0-9]|4[0-9])\s*°", weather):
        return "Hot weather — wear short sleeves, shorts, and stay hydrated."
    if re.search(r"(-\d|[0-9])(?=\s*°)", weather):
        return "Cold weather — wear a down jacket or heavy coat with scarf and gloves."
    return "Moderate weather — a light jacket with casual pants and sneakers works well."


get_clothing_advice_def = ToolDef(
    name="get_clothing_advice",
    description="Give clothing advice based on weather conditions.",
    params=[ToolParam("weather", "The weather description (JSON or plain text)")],
    execute=_get_clothing_advice,
)


# ========== Tool: Translate Text ==========
def _translate_text(args: Dict[str, Any]) -> str:
    """Translate text to the specified language."""
    # TODO: Replace with real translation API (e.g. DeepL, Google Translate)
    text = args.get("text", "")
    target_language = args.get("target_language", "")
    language_names = {
        "en": "English",
        "ja": "日本語",
        "fr": "Français",
        "ko": "한국어",
        "de": "Deutsch",
        "es": "Español",
        "ru": "Русский",
    }
    lang_name = language_names.get(target_language, target_language)
    return f"[Mock translation to {lang_name}]: {text}"


translate_text_def = ToolDef(
    name="translate_text",
    description="Translate text to the specified language.",
    params=[
        ToolParam("text", "The text to translate"),
        ToolParam("target_language", "Target language code, e.g. en, ja, fr, ko, de"),
    ],
    execute=_translate_text,
)


# ========== Tool: Text Statistics ==========
def _text_statistics(args: Dict[str, Any]) -> str:
    """Analyze text and return statistics like character count and word count."""
    text = args.get("text", "")
    char_count = len(text)
    word_count = len([w for w in text.split() if w])
    line_count = len(text.split("\n"))
    return json.dumps(
        {"charCount": char_count, "wordCount": word_count, "lineCount": line_count}
    )


text_statistics_def = ToolDef(
    name="text_statistics",
    description="Analyze text and return statistics like character count and word count.",
    params=[ToolParam("text", "The text to analyze")],
    execute=_text_statistics,
)


# Every tool definition, in a stable order.
ALL_TOOL_DEFS: Tuple[ToolDef, ...] = (
    get_weather_def,
    get_clothing_advice_def,
    translate_text_def,
    text_statistics_def,
)
