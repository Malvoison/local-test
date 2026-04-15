"""Placeholder weather tool."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ..schemas import ToolDefinition


class WeatherArguments(BaseModel):
    """Validated arguments for the weather tool."""

    city: str
    unit: Literal["celsius", "fahrenheit"] = "celsius"


def get_current_weather(city: str, unit: str = "celsius") -> dict[str, str]:
    """Return placeholder weather data."""
    return {
        "city": city,
        "unit": unit,
        "summary": f"Placeholder weather for {city} in {unit}.",
    }


def get_tool_definition() -> ToolDefinition:
    """Return the weather tool definition."""
    return ToolDefinition(
        name="get_current_weather",
        description="Fetch current weather information for a city.",
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name to look up.",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit.",
                },
            },
            "required": ["city"],
        },
        implementation=get_current_weather,
        argument_model=WeatherArguments,
    )
