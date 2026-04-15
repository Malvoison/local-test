"""Placeholder news tool."""

from __future__ import annotations

from pydantic import BaseModel

from ..schemas import ToolDefinition


class NewsArguments(BaseModel):
    """Validated arguments for the news tool."""

    topic: str | None = None


def get_current_news(topic: str | None = None) -> dict[str, object]:
    """Return placeholder news data."""
    return {
        "topic": topic,
        "headlines": [f"Placeholder headline for {topic or 'top stories'}"],
    }


def get_tool_definition() -> ToolDefinition:
    """Return the news tool definition."""
    return ToolDefinition(
        name="get_current_news",
        description="Fetch recent headlines, optionally filtered by topic.",
        parameters={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Optional news topic or query string.",
                }
            },
            "required": [],
        },
        implementation=get_current_news,
        argument_model=NewsArguments,
    )
