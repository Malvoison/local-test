"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from toolcli.config import load_settings


def test_load_settings_defaults_when_env_file_missing(tmp_path: Path) -> None:
    """Load default values when no dotenv file exists."""
    settings = load_settings(tmp_path / ".env")
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "gemma4:e4b"
    assert settings.request_timeout == 30.0
    assert settings.log_level == "INFO"


def test_load_settings_reads_env_file(tmp_path: Path) -> None:
    """Read values from a provided dotenv file."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OLLAMA_BASE_URL=http://example.test:11434",
                "OLLAMA_MODEL=test-model",
                "NEWS_API_KEY=test-key",
                "REQUEST_TIMEOUT=12.5",
                "LOG_LEVEL=debug",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_settings(env_file)

    assert settings.ollama_base_url == "http://example.test:11434"
    assert settings.ollama_model == "test-model"
    assert settings.news_api_key == "test-key"
    assert settings.request_timeout == 12.5
    assert settings.log_level == "DEBUG"


def test_load_settings_prefers_environment_over_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prefer exported environment variables over dotenv file values."""
    env_file = tmp_path / ".env"
    env_file.write_text("OLLAMA_MODEL=file-model\nLOG_LEVEL=ERROR\n", encoding="utf-8")
    monkeypatch.setenv("OLLAMA_MODEL", "env-model")
    monkeypatch.setenv("LOG_LEVEL", "warning")

    settings = load_settings(env_file)

    assert settings.ollama_model == "env-model"
    assert settings.log_level == "WARNING"


def test_env_example_contains_expected_keys() -> None:
    """Ensure the example environment file documents required keys."""
    content = Path(".env.example").read_text(encoding="utf-8")

    for key in [
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "NEWS_API_KEY",
        "REQUEST_TIMEOUT",
        "LOG_LEVEL",
    ]:
        assert key in content
