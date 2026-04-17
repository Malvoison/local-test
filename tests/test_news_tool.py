"""Tests for the news tool."""

from __future__ import annotations

import pytest
import requests

from toolcli.tool_registry import ToolRegistry


class FakeResponse:
    """Minimal fake HTTP response for provider tests."""

    def __init__(self, payload, *, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self):
        """Return the configured payload."""
        return self._payload


def test_get_current_news_top_headlines(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return top headlines when no topic is provided."""
    monkeypatch.setattr("toolcli.providers.news.load_settings", lambda: _settings_with_key())

    def fake_get(url: str, *, params: dict[str, object], headers: dict[str, str], timeout: float) -> FakeResponse:
        assert "top-headlines" in url
        assert params["pageSize"] == 5
        assert params["country"] == "us"
        assert headers["X-Api-Key"] == "test-key"
        return FakeResponse(
            {
                "status": "ok",
                "articles": [
                    _article("Headline One", "Source One"),
                    _article("Headline Two", "Source Two"),
                ],
            }
        )

    monkeypatch.setattr("toolcli.providers.news.requests.get", fake_get)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_news", {})

    assert result.ok is True
    assert result.error is None
    assert result.result["topic"] is None
    assert result.result["count"] == 2
    assert result.result["headlines"][0]["title"] == "Headline One"
    assert "top headlines" in result.result["summary"]


def test_get_current_news_topic_search(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return topic-specific headlines when a topic is provided."""
    monkeypatch.setattr("toolcli.providers.news.load_settings", lambda: _settings_with_key())

    def fake_get(url: str, *, params: dict[str, object], headers: dict[str, str], timeout: float) -> FakeResponse:
        assert "everything" in url
        assert params["q"] == "ai"
        return FakeResponse(
            {
                "status": "ok",
                "articles": [
                    _article("AI Headline", "Tech Source"),
                ],
            }
        )

    monkeypatch.setattr("toolcli.providers.news.requests.get", fake_get)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_news", {"topic": "ai"})

    assert result.ok is True
    assert result.result["topic"] == "ai"
    assert result.result["count"] == 1
    assert result.result["headlines"][0]["source"] == "Tech Source"
    assert "about ai" in result.result["summary"]


def test_get_current_news_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail clearly when NEWS_API_KEY is not configured."""
    monkeypatch.setattr("toolcli.providers.news.load_settings", lambda: _settings_without_key())
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_news", {})

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "execution_error"
    assert result.error["message"] == "NEWS_API_KEY is not set. Add it to your environment or .env file."


def test_get_current_news_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Surface provider failures as readable execution errors."""
    monkeypatch.setattr("toolcli.providers.news.load_settings", lambda: _settings_with_key())

    def fake_get(url: str, *, params: dict[str, object], headers: dict[str, str], timeout: float) -> FakeResponse:
        raise requests.RequestException("boom")

    monkeypatch.setattr("toolcli.providers.news.requests.get", fake_get)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_news", {})

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "execution_error"
    assert result.error["message"] == "News lookup failed: News provider request failed."


def test_get_current_news_empty_result_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return a clean error when no articles are found."""
    monkeypatch.setattr("toolcli.providers.news.load_settings", lambda: _settings_with_key())

    def fake_get(url: str, *, params: dict[str, object], headers: dict[str, str], timeout: float) -> FakeResponse:
        return FakeResponse({"status": "ok", "articles": []})

    monkeypatch.setattr("toolcli.providers.news.requests.get", fake_get)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_news", {"topic": "obscure-topic"})

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "execution_error"
    assert result.error["message"] == "No news articles were found for topic 'obscure-topic'."


def _settings_with_key():
    """Return a settings-like object with a news API key."""
    class Settings:
        news_api_key = "test-key"
        request_timeout = 30.0

    return Settings()


def _settings_without_key():
    """Return a settings-like object without a news API key."""
    class Settings:
        news_api_key = None
        request_timeout = 30.0

    return Settings()


def _article(title: str, source: str) -> dict[str, object]:
    """Build a provider-shaped article payload for tests."""
    return {
        "title": title,
        "source": {"name": source},
        "url": "https://example.test/story",
        "publishedAt": "2026-04-16T12:00:00Z",
        "description": "Story description",
    }
