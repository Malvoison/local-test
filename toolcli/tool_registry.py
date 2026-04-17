"""Tool registration and lookup."""

from __future__ import annotations

from typing import Any

from .schemas import ToolDefinition, ToolExecutionResult
from .tools import load_builtin_tools


class UnknownToolError(Exception):
    """Raised when a requested tool name is not registered."""


class ToolRegistry:
    """Store and expose registered tools for orchestration."""

    def __init__(self, tools: list[ToolDefinition] | None = None) -> None:
        """Initialize the registry with an optional list of tools."""
        self._tools: dict[str, ToolDefinition] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition by name."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Return a tool definition by name if present."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tools in insertion order."""
        return list(self._tools.values())

    def list_for_model(self) -> list[dict[str, Any]]:
        """Return all tools formatted for model tool declarations."""
        return [tool.list_for_model() for tool in self.list_tools()]

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolExecutionResult:
        """Safely execute a registered tool by name."""
        tool = self.get(name)
        if tool is None:
            raise UnknownToolError(f"Unknown tool: {name}")
        return tool.safe_execute(arguments)

    @classmethod
    def with_builtin_tools(cls) -> "ToolRegistry":
        """Create a registry preloaded with the builtin tools."""
        return cls(load_builtin_tools())
