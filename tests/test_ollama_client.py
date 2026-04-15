"""Tests for the Ollama client."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from toolcli.config import Settings
from toolcli.ollama_client import (
    OllamaClient,
    OllamaHTTPError,
    OllamaMalformedResponseError,
    OllamaTimeoutError,
    extract_assistant_content,
    extract_tool_calls,
)


def make_client(session: Mock | None = None) -> OllamaClient:
    """Create a client with test settings."""
    return OllamaClient(
        Settings(
            ollama_base_url="http://localhost:11434",
            ollama_model="test-model",
            request_timeout=15.0,
            log_level="INFO",
        ),
        session=session,
    )


def test_chat_successful_request() -> None:
    """Return parsed JSON for a successful request."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"message": {"content": "hello"}}

    session = Mock()
    session.post.return_value = response

    client = make_client(session)
    payload = client.simple_chat("hi")

    assert payload["message"]["content"] == "hello"
    session.post.assert_called_once()


def test_chat_timeout_raises_application_error() -> None:
    """Raise a timeout-specific exception."""
    session = Mock()
    session.post.side_effect = requests.Timeout("timed out")

    client = make_client(session)

    with pytest.raises(OllamaTimeoutError):
        client.simple_chat("hi")


def test_chat_non_200_response_raises_http_error() -> None:
    """Raise an HTTP error for non-success responses."""
    response = Mock()
    response.status_code = 500
    response.text = "server exploded"

    session = Mock()
    session.post.return_value = response

    client = make_client(session)

    with pytest.raises(OllamaHTTPError) as exc_info:
        client.simple_chat("hi")

    assert exc_info.value.status_code == 500
    assert "HTTP 500" in str(exc_info.value)


def test_chat_malformed_json_raises_error() -> None:
    """Raise a malformed-response error when JSON parsing fails."""
    response = Mock()
    response.status_code = 200
    response.json.side_effect = ValueError("bad json")

    session = Mock()
    session.post.return_value = response

    client = make_client(session)

    with pytest.raises(OllamaMalformedResponseError):
        client.simple_chat("hi")


def test_extract_assistant_content_requires_expected_fields() -> None:
    """Raise a malformed-response error when message content is missing."""
    with pytest.raises(OllamaMalformedResponseError):
        extract_assistant_content({"done": True})


def test_extract_tool_calls_returns_list_when_present() -> None:
    """Extract tool calls from the response message."""
    tool_calls = extract_tool_calls(
        {"message": {"content": "hello", "tool_calls": [{"function": {"name": "x"}}]}}
    )

    assert tool_calls == [{"function": {"name": "x"}}]
