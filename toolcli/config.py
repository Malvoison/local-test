"""Configuration loading for the CLI application."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

try:
    from dotenv import dotenv_values
except ModuleNotFoundError:
    def dotenv_values(path: str | Path) -> dict[str, str]:
        """Read a simple dotenv file when python-dotenv is unavailable."""
        env_values: dict[str, str] = {}
        file_path = Path(path)
        if not file_path.exists():
            return env_values

        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_values[key.strip()] = value.strip()
        return env_values


class Settings(BaseModel):
    """Application settings loaded from the environment and optional dotenv file."""

    model_config = ConfigDict(frozen=True)

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:e4b"
    news_api_key: str | None = None
    request_timeout: float = Field(default=30.0, gt=0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Normalize the logging level before validation."""
        return value.upper()


def load_settings(env_file: str | Path = ".env") -> Settings:
    """Load settings with environment variables taking precedence over dotenv values."""
    env_path = Path(env_file)
    file_values = dotenv_values(env_path) if env_path.exists() else {}

    def get_value(name: str, default: str | None = None) -> str | None:
        return os.environ.get(name, file_values.get(name, default))

    return Settings.model_validate(
        {
            "ollama_base_url": get_value("OLLAMA_BASE_URL", "http://localhost:11434"),
            "ollama_model": get_value("OLLAMA_MODEL", "gemma4:e4b"),
            "news_api_key": get_value("NEWS_API_KEY"),
            "request_timeout": get_value("REQUEST_TIMEOUT", "30.0"),
            "log_level": get_value("LOG_LEVEL", "INFO") or "INFO",
        }
    )


def validate_settings(data: dict[str, object]) -> Settings:
    """Validate merged runtime settings data."""
    return Settings.model_validate(data)


__all__ = ["Settings", "ValidationError", "load_settings", "validate_settings"]
