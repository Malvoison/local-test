"""Primary CLI entry point."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Sequence
from typing import Any

from .config import ValidationError, load_settings, validate_settings
from .ollama_client import OllamaClient, OllamaClientError, extract_assistant_content
from .orchestrator import Orchestrator
from .schemas import OrchestrationResult, RuntimeOptions
from .tool_registry import ToolRegistry
from .ui import AppUI

LOGGER = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_FATAL = 1
EXIT_USAGE_ERROR = 2
EXIT_CONFIG_ERROR = 3
EXIT_OLLAMA_ERROR = 4
EXIT_PROVIDER_ERROR = 5


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="toolcli",
        description="CLI for Ollama-based tool calling.",
    )
    parser.add_argument("prompt", nargs="*", help="Prompt text to send to the application.")
    parser.add_argument("--model", help="Override the configured Ollama model.")
    parser.add_argument("--base-url", help="Override the configured Ollama base URL.")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print the response as JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging for this invocation.",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Disable tools and send the prompt directly to Ollama.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        help="Override the request timeout in seconds.",
    )
    parser.add_argument(
        "--max-tool-rounds",
        type=int,
        default=3,
        help="Maximum tool rounds to allow.",
    )
    parser.add_argument(
        "--system-prompt",
        help="Optional system prompt to include in the request.",
    )
    parser.add_argument(
        "--show-tools",
        action="store_true",
        help="Print registered tools and exit.",
    )
    return parser


def configure_logging(level_name: str) -> None:
    """Configure application logging."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )


def resolve_runtime_options(args: argparse.Namespace, settings=None) -> RuntimeOptions:
    """Merge CLI overrides with environment-backed settings."""
    settings = settings or load_settings()
    log_level = "DEBUG" if args.verbose else settings.log_level
    merged_settings = validate_settings(
        {
            "ollama_base_url": args.base_url or settings.ollama_base_url,
            "ollama_model": args.model or settings.ollama_model,
            "news_api_key": settings.news_api_key,
            "request_timeout": args.timeout if args.timeout is not None else settings.request_timeout,
            "log_level": log_level,
        }
    )
    return RuntimeOptions.model_validate(
        {
            "prompt": " ".join(args.prompt),
            "ollama_base_url": merged_settings.ollama_base_url,
            "ollama_model": merged_settings.ollama_model,
            "request_timeout": merged_settings.request_timeout,
            "log_level": merged_settings.log_level,
            "json_output": args.json_output,
            "tools_enabled": not args.no_tools,
            "max_tool_rounds": args.max_tool_rounds,
            "system_prompt": args.system_prompt,
        }
    )


def serialize_result(result: OrchestrationResult) -> dict[str, Any]:
    """Return the public JSON payload for a completed run."""
    tools_used = [
        {
            "name": activity.tool_name,
            "arguments": activity.arguments,
            "result": activity.result,
            "success": activity.ok,
            "error": activity.error,
        }
        for activity in result.tool_activities
    ]
    return {
        "success": result.success,
        "model": result.model,
        "prompt": result.prompt,
        "tools_used": tools_used,
        "final_answer": result.final_answer,
        "errors": result.errors,
    }


def determine_exit_code(result: OrchestrationResult) -> int:
    """Map orchestration outcomes to CLI exit codes."""
    if result.success:
        return EXIT_OK
    if any(error.get("type") == "execution_error" for error in result.errors):
        return EXIT_PROVIDER_ERROR
    return EXIT_FATAL


def run_without_tools(client: OllamaClient, options: RuntimeOptions) -> OrchestrationResult:
    """Send a direct non-tool request to Ollama."""
    response = client.simple_chat(
        options.prompt,
        system_prompt=options.system_prompt,
        timeout=options.request_timeout,
    )
    return OrchestrationResult(
        prompt=options.prompt,
        model=options.ollama_model,
        tools_used=[],
        final_answer=extract_assistant_content(response),
        errors=[],
        success=True,
        tool_activities=[],
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and send a simple chat request to Ollama."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if not args.show_tools and not args.prompt:
            parser.error("the following arguments are required: prompt")
        base_settings = load_settings()
        runtime_options = resolve_runtime_options(args, settings=base_settings)
    except ValidationError as exc:
        parser.exit(status=EXIT_CONFIG_ERROR, message=f"Configuration error: {exc}\n")

    configure_logging(runtime_options.log_level)
    LOGGER.debug(
        "Resolved runtime options: base_url=%s model=%s timeout=%s json=%s tools_enabled=%s max_tool_rounds=%s system_prompt_set=%s",
        runtime_options.ollama_base_url,
        runtime_options.ollama_model,
        runtime_options.request_timeout,
        runtime_options.json_output,
        runtime_options.tools_enabled,
        runtime_options.max_tool_rounds,
        runtime_options.system_prompt is not None,
    )

    settings = validate_settings(
        {
            "ollama_base_url": runtime_options.ollama_base_url,
            "ollama_model": runtime_options.ollama_model,
            "news_api_key": base_settings.news_api_key,
            "request_timeout": runtime_options.request_timeout,
            "log_level": runtime_options.log_level,
        }
    )
    registry = ToolRegistry.with_builtin_tools()
    client = OllamaClient(settings)
    orchestrator = Orchestrator(client=client, registry=registry)
    ui = AppUI()

    if not runtime_options.json_output:
        ui.print_banner()
    if args.show_tools:
        tool_payload = registry.list_for_model()
        if runtime_options.json_output:
            print(json.dumps({"tools": tool_payload}, indent=2))
        else:
            for tool in tool_payload:
                function = tool["function"]
                print(f"{function['name']}: {function['description']}")
        return EXIT_OK

    try:
        result = run_without_tools(client, runtime_options) if not runtime_options.tools_enabled else orchestrator.run(runtime_options)
    except OllamaClientError as exc:
        logging.getLogger(__name__).error("%s", exc)
        parser.exit(status=EXIT_OLLAMA_ERROR, message=f"Error: {exc}\n")

    payload = serialize_result(result)
    if runtime_options.json_output:
        print(json.dumps(payload, indent=2))
    else:
        if args.verbose:
            ui.print_tool_trace(payload["tools_used"])
        ui.print_response(result.final_answer, payload)
        if result.errors:
            ui.print_errors(result.errors)
    return determine_exit_code(result)
