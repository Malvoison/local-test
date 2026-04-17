"""Builtin tool definitions."""

from __future__ import annotations

from ..schemas import ToolDefinition
from .currency import get_tool_definition as get_currency_tool
from .news import get_tool_definition as get_news_tool
from .time_tool import get_tool_definition as get_time_tool
from .weather import get_tool_definition as get_weather_tool


def load_builtin_tools() -> list[ToolDefinition]:
    """Return the builtin tool definitions."""
    return [
        get_weather_tool(),
        get_news_tool(),
        get_time_tool(),
        get_currency_tool(),
    ]
