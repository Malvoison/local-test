"""Tests for the time tool."""

from __future__ import annotations

from toolcli.tool_registry import ToolRegistry


def test_get_current_time_valid_timezone() -> None:
    """Return structured time data for a valid timezone."""
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_time", {"timezone": "America/Chicago"})

    assert result.ok is True
    assert result.error is None
    assert result.result["timezone"] == "America/Chicago"
    assert "summary" in result.result
    assert result.result["timezone_abbreviation"]


def test_get_current_time_invalid_timezone() -> None:
    """Reject invalid IANA timezones cleanly."""
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_time", {"timezone": "Mars/Olympus_Mons"})

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "validation_error"
    assert "Unsupported IANA timezone" in result.error["details"][0]["msg"]
