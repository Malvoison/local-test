"""Primary CLI entry point for the scaffolded application."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Sequence

from .config import ValidationError, load_settings, validate_settings
from .ollama_client import OllamaClient, OllamaClientError
from .orchestrator import Orchestrator
from .schemas import RuntimeOptions
from .tool_registry import ToolRegistry
from .ui import AppUI

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the placeholder CLI."""
    parser = argparse.ArgumentParser(
        prog="toolcli",
        description="Placeholder CLI scaffold for Ollama-based tool calling.",
    )
    parser.add_argument("prompt", nargs="*", help="Prompt text to send to the application.")
    parser.add_argument("--model", help="Override the configured Ollama model.")
    parser.add_argument("--base-url", help="Override the configured Ollama base URL.")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print the placeholder response as JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging for this invocation.",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Disable tools in the resolved runtime options.",
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
        help="Maximum placeholder tool rounds to report.",
    )
    parser.add_argument(
        "--system-prompt",
        help="Optional system prompt to carry in the placeholder runtime options.",
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
        parser.exit(status=2, message=f"Configuration error: {exc}\n")

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
            print(json.dumps(tool_payload, indent=2))
        else:
            for tool in tool_payload:
                function = tool["function"]
                print(f"{function['name']}: {function['description']}")
        return 0

    try:
        result = orchestrator.run(runtime_options)
    except OllamaClientError as exc:
        logging.getLogger(__name__).error("%s", exc)
        parser.exit(status=1, message=f"Error: {exc}\n")

    if runtime_options.json_output:
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        if args.verbose and result.tool_activities:
            for activity in result.tool_activities:
                status = "ok" if activity.ok else "error"
                print(f"tool {activity.tool_name} [{status}] args={activity.arguments}")
                if activity.error is not None:
                    print(f"  error: {activity.error['message']}")
        ui.print_response(
            result.final_answer,
            result.model_dump(mode="json"),
        )
    return 0 if result.success else 1
