"""Requests-based Ollama client."""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from .config import Settings

LOGGER = logging.getLogger(__name__)


class OllamaClientError(Exception):
    """Base exception for Ollama client failures."""


class OllamaConnectionError(OllamaClientError):
    """Raised when the client cannot connect to Ollama."""


class OllamaTimeoutError(OllamaClientError):
    """Raised when an Ollama request times out."""


class OllamaHTTPError(OllamaClientError):
    """Raised when Ollama returns a non-success HTTP response."""

    def __init__(self, status_code: int, message: str) -> None:
        """Store the HTTP status and a readable error message."""
        super().__init__(message)
        self.status_code = status_code


class OllamaMalformedResponseError(OllamaClientError):
    """Raised when Ollama returns an unexpected response shape."""


def extract_assistant_content(payload: dict[str, Any]) -> str:
    """Extract assistant message content from an Ollama chat response."""
    message = payload.get("message")
    if not isinstance(message, dict):
        raise OllamaMalformedResponseError("Ollama response is missing a valid 'message' object.")

    content = message.get("content")
    if not isinstance(content, str):
        raise OllamaMalformedResponseError("Ollama response is missing assistant text content.")
    return content


def extract_tool_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract any tool calls from an Ollama chat response."""
    message = payload.get("message")
    if not isinstance(message, dict):
        raise OllamaMalformedResponseError("Ollama response is missing a valid 'message' object.")

    tool_calls = message.get("tool_calls", [])
    if tool_calls is None:
        return []
    if not isinstance(tool_calls, list):
        raise OllamaMalformedResponseError("Ollama response contains invalid 'tool_calls' data.")
    return tool_calls


class OllamaClient:
    """Client wrapper for the Ollama chat API."""

    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        """Initialize the client with application settings and an optional session."""
        self._settings = settings
        self._session = session or requests.Session()

    @property
    def base_url(self) -> str:
        """Return the configured Ollama base URL."""
        return self._settings.ollama_base_url.rstrip("/")

    @property
    def model(self) -> str:
        """Return the configured Ollama model name."""
        return self._settings.ollama_model

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Send a chat request to Ollama and return the parsed JSON response."""
        endpoint = f"{self.base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if tools is not None:
            payload["tools"] = tools

        LOGGER.debug("Sending Ollama chat request to %s", endpoint)
        LOGGER.debug(
            "Ollama request shape: model=%s message_count=%s roles=%s tools=%s stream=%s",
            model,
            len(messages),
            [message.get("role", "<missing>") for message in messages],
            len(tools or []),
            False,
        )

        try:
            response = self._session.post(
                endpoint,
                json=payload,
                timeout=timeout or self._settings.request_timeout,
            )
        except requests.Timeout as exc:
            raise OllamaTimeoutError("Request to Ollama timed out.") from exc
        except requests.ConnectionError as exc:
            raise OllamaConnectionError("Could not connect to Ollama.") from exc
        except requests.RequestException as exc:
            raise OllamaClientError(f"Ollama request failed: {exc}") from exc

        LOGGER.debug("Ollama response status: %s", response.status_code)

        if response.status_code != 200:
            body = response.text.strip()
            detail = body[:200] if body else "No response body."
            raise OllamaHTTPError(
                response.status_code,
                f"Ollama returned HTTP {response.status_code}: {detail}",
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise OllamaMalformedResponseError("Ollama returned malformed JSON.") from exc

        if not isinstance(data, dict):
            raise OllamaMalformedResponseError("Ollama response root must be a JSON object.")

        return data

    def simple_chat(self, prompt: str, *, system_prompt: str | None = None, timeout: float | None = None) -> dict[str, Any]:
        """Send a simple non-tool chat request to Ollama."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(
            model=self.model,
            messages=messages,
            tools=None,
            timeout=timeout,
        )


__all__ = [
    "OllamaClient",
    "OllamaClientError",
    "OllamaConnectionError",
    "OllamaHTTPError",
    "OllamaMalformedResponseError",
    "OllamaTimeoutError",
    "extract_assistant_content",
    "extract_tool_calls",
]
