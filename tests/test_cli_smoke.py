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
        lambda self, options: make_result(
            final_answer="json reply",
            tool_activities=[
                ToolActivity(
                    tool_name="get_current_time",
                    arguments={"timezone": "UTC"},
                    ok=True,
                    result={"timezone": "UTC"},
                    error=None,
                )
            ],
        ),
    )

    exit_code = main(["hello", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["final_answer"] == "json reply"
    assert payload["success"] is True
    assert payload["prompt"] == "hello"
    assert payload["model"] == "test-model"
    assert payload["tools_used"] == [
        {
            "name": "get_current_time",
            "arguments": {"timezone": "UTC"},
            "result": {"timezone": "UTC"},
            "success": True,
            "error": None,
        }
    ]
    assert payload["errors"] == []


def test_main_applies_cli_overrides(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Apply CLI runtime overrides in the Ollama request."""
    recorded: dict[str, object] = {}

    def fake_simple_chat(self, prompt: str, *, system_prompt: str | None = None, timeout: float | None = None):
        recorded["model"] = self.model
        recorded["base_url"] = self.base_url
        recorded["prompt"] = prompt
        recorded["system_prompt"] = system_prompt
        recorded["timeout"] = timeout
        return {"message": {"role": "assistant", "content": "override reply"}}

    monkeypatch.setattr("toolcli.main.OllamaClient.simple_chat", fake_simple_chat)

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
    assert "Tool Trace" in captured.out
    assert "get_current_news" in captured.out
    assert "DEBUG toolcli.main: Resolved runtime options" in captured.err


def test_main_exits_nonzero_on_client_error(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Exit nonzero with a readable message on Ollama errors."""
    def raise_error(self, options):
        raise OllamaConnectionError("Could not connect to Ollama.")

    monkeypatch.setattr("toolcli.main.Orchestrator.run", raise_error)

    with pytest.raises(SystemExit) as exc_info:
        main(["hello"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 4
    assert "Error: Could not connect to Ollama." in captured.err


def test_show_tools_prints_registered_tools_and_exits(capsys) -> None:
    """Print registered tools without requiring a prompt."""
    exit_code = main(["--show-tools"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "get_current_weather" in captured.out
    assert "convert_currency" in captured.out


def test_main_returns_nonzero_on_provider_failure(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Return a provider-specific nonzero exit code when tool execution fails."""
    monkeypatch.setattr(
        "toolcli.main.Orchestrator.run",
        lambda self, options: make_result(
            success=False,
            final_answer="I could not complete that request.",
            errors=[{"type": "execution_error", "message": "News lookup failed.", "details": []}],
        ),
    )

    exit_code = main(["hello"])

    captured = capsys.readouterr()

    assert exit_code == 5
    assert "I could not complete that request." in captured.out
    assert "News lookup failed." in captured.out


def test_main_no_tools_uses_direct_ollama_path(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Bypass the orchestrator and tools when --no-tools is set."""
    recorded: dict[str, object] = {}

    def fail_run(self, options):
        raise AssertionError("orchestrator should not run")

    def fake_simple_chat(self, prompt: str, *, system_prompt: str | None = None, timeout: float | None = None):
        recorded["prompt"] = prompt
        recorded["system_prompt"] = system_prompt
        recorded["timeout"] = timeout
        return {"message": {"role": "assistant", "content": "direct reply"}}

    monkeypatch.setattr("toolcli.main.Orchestrator.run", fail_run)
    monkeypatch.setattr("toolcli.main.OllamaClient.simple_chat", fake_simple_chat)

    exit_code = main(["hello", "--no-tools", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert recorded == {"prompt": "hello", "system_prompt": None, "timeout": 30.0}
    assert payload["tools_used"] == []
    assert payload["final_answer"] == "direct reply"
