"""Placeholder time tool."""

from __future__ import annotations

from pydantic import BaseModel

from ..schemas import ToolDefinition


class TimeArguments(BaseModel):
    """Validated arguments for the time tool."""

    timezone: str


def get_current_time(timezone: str) -> dict[str, str]:
    """Return placeholder time data."""
    return {
        "timezone": timezone,
        "current_time": "1970-01-01T00:00:00Z",
    }


def get_tool_definition() -> ToolDefinition:
    """Return the time tool definition."""
    return ToolDefinition(
        name="get_current_time",
        description="Fetch the current time for an IANA timezone.",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone such as America/New_York.",
                }
            },
            "required": ["timezone"],
        },
        implementation=get_current_time,
        argument_model=TimeArguments,
    )
