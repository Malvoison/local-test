"""Time lookup tool."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, field_validator

from ..schemas import ToolDefinition


class TimeArguments(BaseModel):
    """Validated arguments for the time tool."""

    timezone: str

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Validate that the supplied timezone is a real IANA timezone."""
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unsupported IANA timezone: {value}") from exc
        return value


def get_current_time(timezone: str) -> dict[str, str | bool]:
    """Return current time data for a validated timezone."""
    current_time = datetime.now(ZoneInfo(timezone))
    offset = current_time.utcoffset()
    offset_seconds = int(offset.total_seconds()) if offset is not None else 0
    sign = "+" if offset_seconds >= 0 else "-"
    absolute_seconds = abs(offset_seconds)
    hours, remainder = divmod(absolute_seconds, 3600)
    minutes = remainder // 60
    offset_text = f"{sign}{hours:02d}:{minutes:02d}"
    summary = f"The current time in {timezone} is {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}."

    return {
        "timezone": timezone,
        "current_time": current_time.isoformat(),
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S"),
        "timezone_abbreviation": current_time.tzname() or timezone,
        "utc_offset": offset_text,
        "is_dst": bool(current_time.dst()),
        "summary": summary,
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
