"""Tests for the formal tool registry."""

from __future__ import annotations

import pytest

from toolcli.tool_registry import ToolRegistry, UnknownToolError


def test_registry_lookup_by_name() -> None:
    """Lookup a registered tool by name."""
    registry = ToolRegistry.with_builtin_tools()

    tool = registry.get("get_current_news")

    assert tool is not None
    assert tool.name == "get_current_news"


def test_registry_returns_none_for_unknown_tool() -> None:
    """Return None for an unknown tool lookup."""
    registry = ToolRegistry.with_builtin_tools()

    assert registry.get("missing_tool") is None


def test_registry_valid_execution() -> None:
    """Execute a registered tool with valid arguments."""
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_weather", {"city": "Chicago", "unit": "celsius"})

    assert result.ok is True
    assert result.error is None
    assert result.result["city"] == "Chicago"


def test_registry_invalid_arguments_return_structured_error() -> None:
    """Return structured validation errors for invalid arguments."""
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("convert_currency", {"amount": "bad", "from_currency": "USD"})

    assert result.ok is False
    assert result.result is None
    assert result.error is not None
    assert result.error["type"] == "validation_error"
    assert result.error["details"]


def test_registry_execute_unknown_tool_raises() -> None:
    """Raise a dedicated error for unknown tool execution."""
    registry = ToolRegistry.with_builtin_tools()

    with pytest.raises(UnknownToolError):
        registry.execute("missing_tool", {})


def test_list_for_model_returns_expected_tool_definitions() -> None:
    """Return the expected model-facing tool definitions."""
    registry = ToolRegistry.with_builtin_tools()

    tool_definitions = registry.list_for_model()
    tool_names = [tool["function"]["name"] for tool in tool_definitions]

    assert tool_names == [
        "get_current_weather",
        "get_current_news",
        "get_current_time",
        "convert_currency",
    ]
    assert tool_definitions[0]["function"]["parameters"]["type"] == "object"
