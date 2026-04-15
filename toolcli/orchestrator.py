"""Tool-calling orchestration loop."""

from __future__ import annotations

import json
import logging
from typing import Any

from .ollama_client import (
    OllamaClient,
    OllamaClientError,
    OllamaMalformedResponseError,
    extract_assistant_content,
    extract_tool_calls,
)
from .schemas import OrchestrationResult, RuntimeOptions, ToolActivity
from .tool_registry import ToolRegistry, UnknownToolError

LOGGER = logging.getLogger(__name__)


class Orchestrator:
    """Coordinate Ollama chat turns and registered tool execution."""

    def __init__(self, client: OllamaClient, registry: ToolRegistry) -> None:
        """Store collaborators used by the orchestration loop."""
        self._client = client
        self._registry = registry

    def run(self, options: RuntimeOptions) -> OrchestrationResult:
        """Run the tool-calling loop and return a structured result."""
        messages: list[dict[str, Any]] = []
        if options.system_prompt:
            messages.append({"role": "system", "content": options.system_prompt})
        messages.append({"role": "user", "content": options.prompt})

        tool_definitions = self._registry.list_for_model() if options.tools_enabled else None
        tool_activities: list[ToolActivity] = []
        errors: list[dict[str, Any]] = []
        tools_used: list[str] = []
        final_answer = ""

        for round_index in range(options.max_tool_rounds + 1):
            response = self._client.chat(
                model=options.ollama_model,
                messages=messages,
                tools=tool_definitions,
                timeout=options.request_timeout,
            )

            assistant_message = response.get("message")
            if not isinstance(assistant_message, dict):
                raise OllamaMalformedResponseError("Ollama response is missing a valid 'message' object.")

            content = extract_assistant_content(response)
            tool_calls = extract_tool_calls(response)
            final_answer = content
            messages.append(assistant_message)

            if not tool_calls:
                return OrchestrationResult(
                    prompt=options.prompt,
                    model=options.ollama_model,
                    tools_used=tools_used,
                    final_answer=final_answer,
                    errors=errors,
                    success=not errors,
                    tool_activities=tool_activities,
                )

            if round_index >= options.max_tool_rounds:
                errors.append(
                    {
                        "type": "max_rounds_reached",
                        "message": "Maximum tool rounds reached without a final answer.",
                    }
                )
                return OrchestrationResult(
                    prompt=options.prompt,
                    model=options.ollama_model,
                    tools_used=tools_used,
                    final_answer=final_answer,
                    errors=errors,
                    success=False,
                    tool_activities=tool_activities,
                )

            for tool_call in tool_calls:
                try:
                    tool_name, arguments = self._parse_tool_call(tool_call)
                except OllamaMalformedResponseError as exc:
                    errors.append({"type": "malformed_tool_call", "message": str(exc)})
                    return OrchestrationResult(
                        prompt=options.prompt,
                        model=options.ollama_model,
                        tools_used=tools_used,
                        final_answer=final_answer,
                        errors=errors,
                        success=False,
                        tool_activities=tool_activities,
                    )

                LOGGER.debug("Executing tool %s with arguments keys=%s", tool_name, sorted(arguments.keys()))
                try:
                    execution = self._registry.execute(tool_name, arguments)
                except UnknownToolError as exc:
                    error = {"type": "unknown_tool", "message": str(exc)}
                    errors.append(error)
                    activity = ToolActivity(
                        tool_name=tool_name,
                        arguments=arguments,
                        ok=False,
                        result=None,
                        error=error,
                    )
                    tool_activities.append(activity)
                    self._append_tool_message(messages, tool_name, activity.model_dump(mode="json"))
                    continue

                if tool_name not in tools_used:
                    tools_used.append(tool_name)

                activity = ToolActivity(
                    tool_name=tool_name,
                    arguments=arguments,
                    ok=execution.ok,
                    result=execution.result,
                    error=execution.error,
                )
                tool_activities.append(activity)
                if execution.error is not None:
                    errors.append(execution.error)
                self._append_tool_message(messages, tool_name, activity.model_dump(mode="json"))

        errors.append(
            {
                "type": "max_rounds_reached",
                "message": "Maximum tool rounds reached without a final answer.",
            }
        )
        return OrchestrationResult(
            prompt=options.prompt,
            model=options.ollama_model,
            tools_used=tools_used,
            final_answer=final_answer,
            errors=errors,
            success=False,
            tool_activities=tool_activities,
        )

    def _parse_tool_call(self, tool_call: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Validate and extract tool call name and arguments."""
        if not isinstance(tool_call, dict):
            raise OllamaMalformedResponseError("Tool call entry must be an object.")

        function = tool_call.get("function")
        if not isinstance(function, dict):
            raise OllamaMalformedResponseError("Tool call is missing a valid function object.")

        name = function.get("name")
        if not isinstance(name, str) or not name:
            raise OllamaMalformedResponseError("Tool call is missing a valid function name.")

        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise OllamaMalformedResponseError("Tool call arguments are not valid JSON.") from exc

        if not isinstance(arguments, dict):
            raise OllamaMalformedResponseError("Tool call arguments must be an object.")

        return name, arguments

    def _append_tool_message(self, messages: list[dict[str, Any]], tool_name: str, payload: dict[str, Any]) -> None:
        """Append a structured tool result message to the conversation."""
        messages.append(
            {
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(payload),
            }
        )
