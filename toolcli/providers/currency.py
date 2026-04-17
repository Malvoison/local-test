"""Currency rate provider isolated from tool orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


DEFAULT_TIMEOUT = 10.0
FRANKFURTER_LATEST_URL = "https://api.frankfurter.app/latest"


class CurrencyProviderError(Exception):
    """Base error raised for currency provider failures."""


class UnsupportedCurrencyError(CurrencyProviderError):
    """Raised when the provider rejects one or more currency codes."""


@dataclass(frozen=True)
class ExchangeRateQuote:
    """Normalized exchange-rate quote returned by the provider."""

    from_currency: str
    to_currency: str
    rate: Decimal


def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> ExchangeRateQuote:
    """Fetch a live exchange rate from the Frankfurter public API."""
    query = urlencode({"from": from_currency, "to": to_currency, "amount": "1"})
    url = f"{FRANKFURTER_LATEST_URL}?{query}"

    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code in {400, 404}:
            raise UnsupportedCurrencyError(
                f"Unsupported currency code for {from_currency} or {to_currency}."
            ) from exc
        raise CurrencyProviderError("Currency provider returned an HTTP error.") from exc
    except URLError as exc:
        raise CurrencyProviderError("Currency provider is unavailable.") from exc
    except json.JSONDecodeError as exc:
        raise CurrencyProviderError("Currency provider returned malformed JSON.") from exc

    if not isinstance(payload, dict):
        raise CurrencyProviderError("Currency provider returned an unexpected response.")

    rates = payload.get("rates")
    if not isinstance(rates, dict):
        message = payload.get("message")
        if isinstance(message, str) and message:
            lowered = message.lower()
            if "invalid" in lowered or "not found" in lowered or "unknown" in lowered:
                raise UnsupportedCurrencyError(
                    f"Unsupported currency code for {from_currency} or {to_currency}."
                )
        raise CurrencyProviderError("Currency provider response did not include exchange rates.")

    raw_rate = rates.get(to_currency)
    if raw_rate is None:
        raise UnsupportedCurrencyError(f"Unsupported currency code: {to_currency}.")

    try:
        rate = Decimal(str(raw_rate))
    except Exception as exc:  # pragma: no cover - defensive parsing
        raise CurrencyProviderError("Currency provider returned an invalid exchange rate.") from exc

    return ExchangeRateQuote(
        from_currency=from_currency,
        to_currency=to_currency,
        rate=rate,
    )
