"""Shared schemas for CLI configuration, tools, and orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ToolDefinition(BaseModel):
    """Describe an executable tool exposed to the orchestration layer."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str
    description: str
    parameters: dict[str, Any]
    implementation: Callable[..., Any]
    argument_model: type[BaseModel]

    def list_for_model(self) -> dict[str, Any]:
        """Return the model-facing tool definition payload."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def validate_arguments(self, arguments: dict[str, Any]) -> BaseModel:
        """Validate incoming tool arguments."""
        return self.argument_model.model_validate(arguments)

    def safe_execute(self, arguments: dict[str, Any]) -> "ToolExecutionResult":
        """Validate and execute the tool implementation safely."""
        try:
            validated = self.validate_arguments(arguments)
        except ValidationError as exc:
            return ToolExecutionResult(
                ok=False,
                tool_name=self.name,
                result=None,
                error={
                    "type": "validation_error",
                    "message": "Invalid tool arguments.",
                    "details": exc.errors(),
                },
            )

        try:
            result = self.implementation(**validated.model_dump())
        except Exception as exc:
            return ToolExecutionResult(
                ok=False,
                tool_name=self.name,
                result=None,
                error={
                    "type": "execution_error",
                    "message": str(exc),
                    "details": [],
                },
            )

        return ToolExecutionResult(
            ok=True,
            tool_name=self.name,
            result=result,
            error=None,
        )


class ToolExecutionResult(BaseModel):
    """Represent the outcome of a safe tool execution."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    tool_name: str
    result: Any = None
    error: dict[str, Any] | None = None


class ToolActivity(BaseModel):
    """Record a single tool invocation observed during orchestration."""

    model_config = ConfigDict(frozen=True)

    tool_name: str
    arguments: dict[str, Any]
    ok: bool
    result: Any = None
    error: dict[str, Any] | None = None


class OrchestrationResult(BaseModel):
    """Structured result returned by the orchestration loop."""

    model_config = ConfigDict(frozen=True)

    prompt: str
    model: str
    tools_used: list[str]
    final_answer: str
    errors: list[dict[str, Any]]
    success: bool
    tool_activities: list[ToolActivity] = Field(default_factory=list)


class RuntimeOptions(BaseModel):
    """Resolved runtime options after CLI overrides are applied."""

    model_config = ConfigDict(frozen=True)

    prompt: str
    ollama_base_url: str
    ollama_model: str
    request_timeout: float = Field(gt=0)
    log_level: str
    json_output: bool = False
    tools_enabled: bool = True
    max_tool_rounds: int = Field(default=3, ge=0)
    system_prompt: str | None = None
