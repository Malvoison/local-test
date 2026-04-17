"""Tests for the currency conversion tool."""

from __future__ import annotations

from decimal import Decimal

import pytest

from toolcli.providers.currency import CurrencyProviderError, ExchangeRateQuote, UnsupportedCurrencyError
from toolcli.tool_registry import ToolRegistry


def test_convert_currency_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Convert a currency amount using a mocked provider."""

    def fake_get_exchange_rate(from_currency: str, to_currency: str) -> ExchangeRateQuote:
        assert from_currency == "USD"
        assert to_currency == "EUR"
        return ExchangeRateQuote(from_currency="USD", to_currency="EUR", rate=Decimal("0.92"))

    monkeypatch.setattr("toolcli.tools.currency.get_exchange_rate", fake_get_exchange_rate)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute(
        "convert_currency",
        {"amount": 10, "from_currency": "usd", "to_currency": "eur"},
    )

    assert result.ok is True
    assert result.error is None
    assert result.result == {
        "original_amount": 10.0,
        "source_currency": "USD",
        "target_currency": "EUR",
        "exchange_rate": 0.92,
        "converted_amount": 9.2,
        "summary": "10.00 USD is 9.20 EUR at an exchange rate of 0.920000.",
    }


def test_convert_currency_invalid_amount() -> None:
    """Reject amounts that are not greater than zero."""
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute(
        "convert_currency",
        {"amount": 0, "from_currency": "USD", "to_currency": "EUR"},
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "validation_error"


def test_convert_currency_unsupported_currency(monkeypatch: pytest.MonkeyPatch) -> None:
    """Surface unsupported currency codes as a readable execution error."""

    def fake_get_exchange_rate(from_currency: str, to_currency: str) -> ExchangeRateQuote:
        raise UnsupportedCurrencyError("Unsupported currency code for USD or XYZ.")

    monkeypatch.setattr("toolcli.tools.currency.get_exchange_rate", fake_get_exchange_rate)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute(
        "convert_currency",
        {"amount": 10, "from_currency": "USD", "to_currency": "XYZ"},
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "execution_error"
    assert "Unsupported currency code" in result.error["message"]


def test_convert_currency_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Surface provider outages as readable execution errors."""

    def fake_get_exchange_rate(from_currency: str, to_currency: str) -> ExchangeRateQuote:
        raise CurrencyProviderError("Currency provider is unavailable.")

    monkeypatch.setattr("toolcli.tools.currency.get_exchange_rate", fake_get_exchange_rate)
    registry = ToolRegistry.with_builtin_tools()

    result = registry.execute(
        "convert_currency",
        {"amount": 10, "from_currency": "USD", "to_currency": "EUR"},
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error["type"] == "execution_error"
    assert result.error["message"] == "Currency conversion failed: Currency provider is unavailable."
