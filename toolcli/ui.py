"""Terminal UI helpers built on Rich."""

from __future__ import annotations

import json

try:
    from rich.console import Console
    from rich.panel import Panel
except ModuleNotFoundError:
    Console = None
    Panel = None


class AppUI:
    """Render terminal output for the CLI."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the UI with an optional Rich console."""
        self._console = console or (Console() if Console is not None else None)

    def print_banner(self) -> None:
        """Print a small startup banner."""
        if self._console is None:
            print("toolcli placeholder scaffold")
            return
        self._console.print("[bold cyan]toolcli[/bold cyan] placeholder scaffold")

    def print_response(self, content: str, payload: dict[str, object], *, as_json: bool = False) -> None:
        """Render the placeholder response content."""
        if as_json:
            formatted = json.dumps(payload, indent=2)
            if self._console is None:
                print(formatted)
                return
            self._console.print(formatted)
            return

        if self._console is None or Panel is None:
            print("Response")
            print(content)
            return
        self._console.print(Panel(content, title="Response"))
