"""Tests for the weather tool."""

from __future__ import annotations

import pytest
import requests

from toolcli.tool_registry import ToolRegistry


class FakeResponse:
    """Minimal fake HTTP response for provider tests."""

    def __init__(self, payload, *, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        """Raise an HTTP error when the status code is not successful."""
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        """Return the configured payload."""
        return self._payload


def test_get_current_weather_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return normalized weather data from mocked geocoding and forecast calls."""

    def fake_get(url: str, *, params: dict[str, object], timeout: float) -> FakeResponse:
        assert timeout == 10.0
        if "geocoding-api" in url:
            assert params["name"] == "Chicago"
            return FakeResponse(
                {
                    "results": [
                        {
                            "name": "Chicago",
                            "latitude": 41.8781,
                            "longitude": -87.6298,
                            "country": "United States",
                            "admin1": "Illinois",
                        }
                    ]
                }
            )
        if "api.open-meteo.com" in url:
            assert params["temperature_unit"] == "celsius"
            return FakeResponse(
                {
                    "current": {
                        "temperature_2m": 19.4,
                        "weather_code": 2,
                    },
                    "current_units": {
                        "temperature_2m": "C",
                    },
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("toolcli.providers.weather.requests.get", fake_get)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_weather", {"city": "Chicago", "unit": "celsius"})

    assert result.ok is True
    assert result.error is None
    assert result.result == {
        "resolved_location": "Chicago, Illinois, United States",
        "latitude": 41.8781,
        "longitude": -87.6298,
        "temperature": 19.4,
        "unit": "celsius",
        "weather_description": "Partly cloudy",
        "summary": "It is currently 19.4C in Chicago, Illinois, United States with partly cloudy.",
    }


def test_get_current_weather_city_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Surface city lookup misses as readable execution errors."""

    def fake_get(url: str, *, params: dict[str, object], timeout: float) -> FakeResponse:
        return FakeResponse({"results": []})

    monkeypatch.setattr("toolcli.providers.weather.requests.get", fake_get)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_weather", {"city": "Atlantis", "unit": "celsius"})

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "execution_error"
    assert "Could not find a city matching 'Atlantis'." == result.error["message"]


def test_get_current_weather_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Surface provider request failures as readable execution errors."""

    def fake_get(url: str, *, params: dict[str, object], timeout: float) -> FakeResponse:
        raise requests.Timeout("timed out")

    monkeypatch.setattr("toolcli.providers.weather.requests.get", fake_get)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_weather", {"city": "Chicago", "unit": "celsius"})

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "execution_error"
    assert result.error["message"] == "Weather lookup failed: Weather provider timed out."


def test_get_current_weather_invalid_unit() -> None:
    """Reject unsupported temperature units cleanly."""
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute("get_current_weather", {"city": "Chicago", "unit": "kelvin"})

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "validation_error"
    assert "Unit must be either 'celsius' or 'fahrenheit'." in result.error["details"][0]["msg"]
