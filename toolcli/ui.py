"""Terminal UI helpers built on Rich."""

from __future__ import annotations

import json
from typing import Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ModuleNotFoundError:
    Console = None
    Panel = None
    Table = None


class AppUI:
    """Render terminal output for the CLI."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the UI with an optional Rich console."""
        self._console = console or (Console() if Console is not None else None)

    def print_banner(self) -> None:
        """Print a small startup banner."""
        if self._console is None:
            print("toolcli")
            return
        self._console.print("[bold cyan]toolcli[/bold cyan]")

    def print_response(self, content: str, payload: dict[str, object], *, as_json: bool = False) -> None:
        """Render the final response content."""
        if as_json:
            formatted = json.dumps(payload, indent=2)
            if self._console is None:
                print(formatted)
                return
            self._console.print(formatted)
            return

        if self._console is None or Panel is None:
            print(content)
            return
        self._console.print(Panel(content, title="Answer", border_style="cyan"))

    def print_tool_trace(self, tools_used: list[dict[str, Any]]) -> None:
        """Render a concise tool trace for verbose mode."""
        if not tools_used:
            return
        if self._console is None or Table is None:
            for entry in tools_used:
                status = "ok" if entry["success"] else "error"
                print(f"tool {entry['name']} [{status}] args={entry['arguments']}")
                if entry.get("error"):
                    print(f"  error: {entry['error']['message']}")
            return

        table = Table(title="Tool Trace", show_header=True, header_style="bold")
        table.add_column("Tool", style="cyan")
        table.add_column("Status")
        table.add_column("Arguments", overflow="fold")
        table.add_column("Message", overflow="fold")
        for entry in tools_used:
            table.add_row(
                entry["name"],
                "ok" if entry["success"] else "error",
                json.dumps(entry["arguments"]),
                entry["error"]["message"] if entry.get("error") else "",
            )
        self._console.print(table)

    def print_errors(self, errors: list[dict[str, Any]]) -> None:
        """Render structured errors in a readable way."""
        if not errors:
            return
        primary = errors[0].get("message", "Unknown error.")
        if self._console is None or Panel is None:
            print(f"Error: {primary}")
            return
        self._console.print(Panel(primary, title="Error", border_style="red"))
