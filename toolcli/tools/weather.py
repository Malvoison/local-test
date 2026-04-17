"""Current weather lookup tool."""

from __future__ import annotations

from pydantic import BaseModel, field_validator

from ..providers.weather import (
    AmbiguousLocationError,
    LocationNotFoundError,
    WeatherProviderDataError,
    WeatherProviderError,
    get_current_weather_for_city,
)
from ..schemas import ToolDefinition


class WeatherArguments(BaseModel):
    """Validated arguments for the weather tool."""

    city: str
    unit: str = "celsius"

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        """Require a non-empty city name."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("City is required.")
        return normalized

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        """Normalize and validate supported temperature units."""
        normalized = value.strip().lower()
        if normalized not in {"celsius", "fahrenheit"}:
            raise ValueError("Unit must be either 'celsius' or 'fahrenheit'.")
        return normalized


def get_current_weather(city: str, unit: str = "celsius") -> dict[str, object]:
    """Return current weather data for a city using isolated providers."""
    try:
        location, weather = get_current_weather_for_city(city, unit)
    except LocationNotFoundError as exc:
        raise ValueError(str(exc)) from exc
    except AmbiguousLocationError as exc:
        raise ValueError(str(exc)) from exc
    except WeatherProviderDataError as exc:
        raise RuntimeError(f"Weather provider returned malformed data: {exc}") from exc
    except WeatherProviderError as exc:
        raise RuntimeError(f"Weather lookup failed: {exc}") from exc

    summary = (
        f"It is currently {weather.temperature:.1f}{weather.unit} in {location.resolved_name} "
        f"with {weather.description.lower()}."
    )

    return {
        "resolved_location": location.resolved_name,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "temperature": weather.temperature,
        "unit": unit,
        "weather_description": weather.description,
        "summary": summary,
    }


def get_tool_definition() -> ToolDefinition:
    """Return the weather tool definition."""
    return ToolDefinition(
        name="get_current_weather",
        description="Fetch current weather information for a city.",
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name to look up.",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit.",
                },
            },
            "required": ["city"],
        },
        implementation=get_current_weather,
        argument_model=WeatherArguments,
    )
