"""Weather provider isolated from tool orchestration."""

from __future__ import annotations

from dataclasses import dataclass

import requests


DEFAULT_TIMEOUT = 10.0
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_SUMMARIES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherProviderError(Exception):
    """Base error raised for weather provider failures."""


class LocationNotFoundError(WeatherProviderError):
    """Raised when no geocoding results match the requested city."""


class AmbiguousLocationError(WeatherProviderError):
    """Raised when geocoding returns multiple equally plausible matches."""


class WeatherProviderDataError(WeatherProviderError):
    """Raised when a provider responds with malformed data."""


@dataclass(frozen=True)
class GeocodedLocation:
    """Normalized location returned by the geocoding provider."""

    name: str
    latitude: float
    longitude: float
    country: str | None = None
    admin1: str | None = None

    @property
    def resolved_name(self) -> str:
        """Return a human-friendly resolved location label."""
        parts = [self.name]
        if self.admin1 and self.admin1 != self.name:
            parts.append(self.admin1)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


@dataclass(frozen=True)
class CurrentWeather:
    """Normalized weather reading returned by the forecast provider."""

    temperature: float
    unit: str
    description: str


def get_current_weather_for_city(city: str, unit: str, *, timeout: float = DEFAULT_TIMEOUT) -> tuple[GeocodedLocation, CurrentWeather]:
    """Resolve a city and fetch its current weather."""
    location = geocode_city(city, timeout=timeout)
    weather = fetch_current_weather(
        latitude=location.latitude,
        longitude=location.longitude,
        unit=unit,
        timeout=timeout,
    )
    return location, weather


def geocode_city(city: str, *, timeout: float = DEFAULT_TIMEOUT) -> GeocodedLocation:
    """Resolve a city name into a single normalized location."""
    payload = _get_json(
        GEOCODING_URL,
        params={"name": city, "count": 5, "language": "en", "format": "json"},
        timeout=timeout,
    )
    results = payload.get("results")
    if not isinstance(results, list):
        raise WeatherProviderDataError("Weather geocoding response did not include results.")
    if not results:
        raise LocationNotFoundError(f"Could not find a city matching '{city}'.")

    normalized_city = city.casefold()
    exact_matches = [entry for entry in results if _matches_city_name(entry, normalized_city)]
    if len(exact_matches) > 1:
        candidates = ", ".join(_format_candidate(entry) for entry in exact_matches[:3])
        raise AmbiguousLocationError(f"City lookup for '{city}' is ambiguous: {candidates}.")

    selected = exact_matches[0] if exact_matches else results[0]
    return _parse_location(selected)


def fetch_current_weather(
    *,
    latitude: float,
    longitude: float,
    unit: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> CurrentWeather:
    """Fetch current weather for a normalized coordinate pair."""
    payload = _get_json(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
            "temperature_unit": unit,
        },
        timeout=timeout,
    )

    current = payload.get("current")
    current_units = payload.get("current_units")
    if not isinstance(current, dict) or not isinstance(current_units, dict):
        raise WeatherProviderDataError("Weather provider response did not include current conditions.")

    raw_temperature = current.get("temperature_2m")
    raw_weather_code = current.get("weather_code")
    raw_unit_symbol = current_units.get("temperature_2m")

    try:
        temperature = float(raw_temperature)
    except (TypeError, ValueError) as exc:
        raise WeatherProviderDataError("Weather provider returned an invalid temperature value.") from exc

    if not isinstance(raw_weather_code, int):
        raise WeatherProviderDataError("Weather provider returned an invalid weather code.")
    if not isinstance(raw_unit_symbol, str) or not raw_unit_symbol:
        raise WeatherProviderDataError("Weather provider returned an invalid temperature unit.")

    description = WEATHER_CODE_SUMMARIES.get(raw_weather_code, "Unknown conditions")
    return CurrentWeather(
        temperature=temperature,
        unit=raw_unit_symbol,
        description=description,
    )


def _get_json(url: str, *, params: dict[str, object], timeout: float) -> dict[str, object]:
    """Execute an HTTP GET and return a decoded JSON object."""
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout as exc:
        raise WeatherProviderError("Weather provider timed out.") from exc
    except requests.RequestException as exc:
        raise WeatherProviderError("Weather provider request failed.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise WeatherProviderDataError("Weather provider returned malformed JSON.") from exc

    if not isinstance(payload, dict):
        raise WeatherProviderDataError("Weather provider returned an unexpected response.")
    return payload


def _matches_city_name(entry: object, normalized_city: str) -> bool:
    """Return whether a geocoder result exactly matches the requested city name."""
    if not isinstance(entry, dict):
        return False
    name = entry.get("name")
    return isinstance(name, str) and name.casefold() == normalized_city


def _parse_location(entry: object) -> GeocodedLocation:
    """Parse a geocoder entry into a normalized location."""
    if not isinstance(entry, dict):
        raise WeatherProviderDataError("Weather geocoding response included an invalid location entry.")

    name = entry.get("name")
    latitude = entry.get("latitude")
    longitude = entry.get("longitude")
    country = entry.get("country")
    admin1 = entry.get("admin1")

    if not isinstance(name, str) or not name:
        raise WeatherProviderDataError("Weather geocoding response did not include a valid location name.")
    try:
        parsed_latitude = float(latitude)
        parsed_longitude = float(longitude)
    except (TypeError, ValueError) as exc:
        raise WeatherProviderDataError("Weather geocoding response did not include valid coordinates.") from exc

    return GeocodedLocation(
        name=name,
        latitude=parsed_latitude,
        longitude=parsed_longitude,
        country=country if isinstance(country, str) and country else None,
        admin1=admin1 if isinstance(admin1, str) and admin1 else None,
    )


def _format_candidate(entry: object) -> str:
    """Build a concise ambiguity label for a geocoder entry."""
    if not isinstance(entry, dict):
        return "unknown"
    parts = []
    for key in ("name", "admin1", "country"):
        value = entry.get(key)
        if isinstance(value, str) and value and value not in parts:
            parts.append(value)
    return ", ".join(parts) or "unknown"
