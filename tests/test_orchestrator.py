"""Tests for the tool-calling orchestrator."""

from __future__ import annotations

from typing import Any

import pytest

from toolcli.orchestrator import Orchestrator
from toolcli.schemas import RuntimeOptions, ToolDefinition
from toolcli.tool_registry import ToolRegistry
from toolcli.tools.news import NewsArguments


class FakeClient:
    """Minimal fake Ollama client with queued responses."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "model": model,
                "messages": messages,
                "tools": tools,
                "timeout": timeout,
            }
        )
        return self.responses.pop(0)


def make_options(**overrides: Any) -> RuntimeOptions:
    """Create runtime options for orchestrator tests."""
    data = {
        "prompt": "hello",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "test-model",
        "request_timeout": 10.0,
        "log_level": "INFO",
        "json_output": False,
        "tools_enabled": True,
        "max_tool_rounds": 3,
        "system_prompt": None,
    }
    data.update(overrides)
    return RuntimeOptions.model_validate(data)


def test_orchestrator_no_tool_called() -> None:
    """Return the assistant response directly when no tool is requested."""
    client = FakeClient([{"message": {"role": "assistant", "content": "final answer"}}])
    registry = ToolRegistry.with_builtin_tools()

    result = Orchestrator(client=client, registry=registry).run(make_options())

    assert result.success is True
    assert result.final_answer == "final answer"
    assert result.tools_used == []


def test_orchestrator_single_tool_called() -> None:
    """Execute one tool call and re-query Ollama."""
    client = FakeClient(
        [
            {
                "message": {
                    "role": "assistant",
                    "content": "calling tool",
                    "tool_calls": [
                        {"function": {"name": "get_current_news", "arguments": {"topic": "ai"}}}
                    ],
                }
            },
            {"message": {"role": "assistant", "content": "final answer"}},
        ]
    )
    registry = ToolRegistry.with_builtin_tools()

    result = Orchestrator(client=client, registry=registry).run(make_options())

    assert result.success is True
    assert result.final_answer == "final answer"
    assert result.tools_used == ["get_current_news"]
    assert len(result.tool_activities) == 1
    assert len(client.calls) == 2


def test_orchestrator_multiple_tool_calls() -> None:
    """Execute multiple tool calls from one model turn."""
    client = FakeClient(
        [
            {
                "message": {
                    "role": "assistant",
                    "content": "calling tools",
                    "tool_calls": [
                        {"function": {"name": "get_current_time", "arguments": {"timezone": "UTC"}}},
                        {
                            "function": {
                                "name": "convert_currency",
                                "arguments": {
                                    "amount": 10,
                                    "from_currency": "usd",
                                    "to_currency": "eur",
                                },
                            }
                        },
                    ],
                }
            },
            {"message": {"role": "assistant", "content": "done"}},
        ]
    )

    result = Orchestrator(client=client, registry=ToolRegistry.with_builtin_tools()).run(make_options())

    assert result.success is True
    assert result.tools_used == ["get_current_time", "convert_currency"]
    assert len(result.tool_activities) == 2


def test_orchestrator_unknown_tool() -> None:
    """Record an error when Ollama requests an unknown tool."""
    client = FakeClient(
        [
            {
                "message": {
                    "role": "assistant",
                    "content": "calling tool",
                    "tool_calls": [{"function": {"name": "missing_tool", "arguments": {}}}],
                }
            },
            {"message": {"role": "assistant", "content": "fallback answer"}},
        ]
    )

    result = Orchestrator(client=client, registry=ToolRegistry.with_builtin_tools()).run(make_options())

    assert result.success is False
    assert result.final_answer == "fallback answer"
    assert result.errors[0]["type"] == "unknown_tool"


def test_orchestrator_tool_validation_failure() -> None:
    """Record validation errors from tool execution."""
    client = FakeClient(
        [
            {
                "message": {
                    "role": "assistant",
                    "content": "calling tool",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "convert_currency",
                                "arguments": {"amount": "bad", "from_currency": "USD"},
                            }
                        }
                    ],
                }
            },
            {"message": {"role": "assistant", "content": "fallback answer"}},
        ]
    )

    result = Orchestrator(client=client, registry=ToolRegistry.with_builtin_tools()).run(make_options())

    assert result.success is False
    assert result.errors[0]["type"] == "validation_error"


def test_orchestrator_tool_execution_exception() -> None:
    """Record execution errors from tool implementations."""
    def boom(topic: str | None = None) -> dict[str, Any]:
        raise RuntimeError("boom")

    broken_tool = ToolDefinition(
        name="get_current_news",
        description="Broken tool",
        parameters={"type": "object", "properties": {}, "required": []},
        implementation=boom,
        argument_model=NewsArguments,
    )
    registry = ToolRegistry.with_builtin_tools()
    registry.register(broken_tool)
    client = FakeClient(
        [
            {
                "message": {
                    "role": "assistant",
                    "content": "calling tool",
                    "tool_calls": [{"function": {"name": "get_current_news", "arguments": {}}}],
                }
            },
            {"message": {"role": "assistant", "content": "fallback answer"}},
        ]
    )

    result = Orchestrator(client=client, registry=registry).run(make_options())

    assert result.success is False
    assert result.errors[0]["type"] == "execution_error"


def test_orchestrator_max_rounds_reached() -> None:
    """Fail when the tool loop exceeds the configured round cap."""
    client = FakeClient(
        [
            {
                "message": {
                    "role": "assistant",
                    "content": "round one",
                    "tool_calls": [{"function": {"name": "get_current_news", "arguments": {}}}],
                }
            },
            {
                "message": {
                    "role": "assistant",
                    "content": "round two",
                    "tool_calls": [{"function": {"name": "get_current_news", "arguments": {}}}],
                }
            },
        ]
    )

    result = Orchestrator(client=client, registry=ToolRegistry.with_builtin_tools()).run(
        make_options(max_tool_rounds=1)
    )

    assert result.success is False
    assert result.errors[-1]["type"] == "max_rounds_reached"
