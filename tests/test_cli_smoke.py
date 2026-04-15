"""Smoke tests for the CLI."""

from __future__ import annotations

import json

import pytest

from toolcli.main import main
from toolcli.ollama_client import OllamaConnectionError
from toolcli.schemas import OrchestrationResult, ToolActivity


def make_result(**overrides):
    """Create a structured orchestration result for CLI tests."""
    data = {
        "prompt": "hello",
        "model": "test-model",
        "tools_used": [],
        "final_answer": "reply",
        "errors": [],
        "success": True,
        "tool_activities": [],
    }
    data.update(overrides)
    return OrchestrationResult.model_validate(data)


def test_main_prints_assistant_response(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the CLI entry point and verify assistant output."""
    monkeypatch.setattr(
        "toolcli.main.Orchestrator.run",
        lambda self, options: make_result(final_answer=f"reply to {options.prompt}"),
    )

    exit_code = main(["hello", "world"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "reply to hello world" in captured.out


def test_main_supports_json_output(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Render assistant output as JSON."""
    monkeypatch.setattr(
        "toolcli.main.Orchestrator.run",
        lambda self, options: make_result(final_answer="json reply"),
    )

    exit_code = main(["hello", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["final_answer"] == "json reply"
    assert payload["success"] is True


def test_main_applies_cli_overrides(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Apply CLI runtime overrides in the Ollama request."""
    recorded: dict[str, object] = {}

    def fake_run(self, options):
        recorded["model"] = options.ollama_model
        recorded["base_url"] = options.ollama_base_url
        recorded["prompt"] = options.prompt
        recorded["system_prompt"] = options.system_prompt
        recorded["timeout"] = options.request_timeout
        return make_result(final_answer="override reply")

    monkeypatch.setattr("toolcli.main.Orchestrator.run", fake_run)

    exit_code = main(
        [
            "hello",
            "--model",
            "override-model",
            "--base-url",
            "http://example.test:11434",
            "--timeout",
            "9",
            "--max-tool-rounds",
            "5",
            "--system-prompt",
            "be concise",
            "--no-tools",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "override reply" in captured.out
    assert recorded["model"] == "override-model"
    assert recorded["base_url"] == "http://example.test:11434"
    assert recorded["prompt"] == "hello"
    assert recorded["system_prompt"] == "be concise"
    assert recorded["timeout"] == 9.0


def test_main_verbose_mode_enables_debug_logging(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable DEBUG logging when verbose mode is set."""
    monkeypatch.setattr(
        "toolcli.main.Orchestrator.run",
        lambda self, options: make_result(
            final_answer="debug reply",
            tool_activities=[
                ToolActivity(
                    tool_name="get_current_news",
                    arguments={"topic": "ai"},
                    ok=True,
                    result={"headlines": ["x"]},
                    error=None,
                )
            ],
        ),
    )

    exit_code = main(["hello", "--verbose"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "debug reply" in captured.out
    assert "tool get_current_news [ok]" in captured.out
    assert "DEBUG toolcli.main: Resolved runtime options" in captured.err


def test_main_exits_nonzero_on_client_error(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Exit nonzero with a readable message on Ollama errors."""
    def raise_error(self, options):
        raise OllamaConnectionError("Could not connect to Ollama.")

    monkeypatch.setattr("toolcli.main.Orchestrator.run", raise_error)

    with pytest.raises(SystemExit) as exc_info:
        main(["hello"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "Error: Could not connect to Ollama." in captured.err


def test_show_tools_prints_registered_tools_and_exits(capsys) -> None:
    """Print registered tools without requiring a prompt."""
    exit_code = main(["--show-tools"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "get_current_weather" in captured.out
    assert "convert_currency" in captured.out
