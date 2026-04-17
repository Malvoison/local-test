"""Currency conversion tool."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, Field, field_validator

from ..providers.currency import CurrencyProviderError, UnsupportedCurrencyError, get_exchange_rate
from ..schemas import ToolDefinition


class CurrencyArguments(BaseModel):
    """Validated arguments for the currency tool."""

    amount: float = Field(gt=0)
    from_currency: str
    to_currency: str

    @field_validator("from_currency", "to_currency")
    @classmethod
    def normalize_currency_code(cls, value: str) -> str:
        """Normalize and validate ISO-style three-letter currency codes."""
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency codes must be three alphabetic characters.")
        return normalized


def _format_decimal(value: Decimal, places: str) -> float:
    """Quantize decimal values for stable JSON-friendly output."""
    return float(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict[str, object]:
    """Convert a currency amount using an isolated rate provider."""
    if from_currency == to_currency:
        amount_decimal = Decimal(str(amount))
        converted_amount = _format_decimal(amount_decimal, "0.01")
        summary = f"{converted_amount:.2f} {from_currency} equals {converted_amount:.2f} {to_currency}."
        return {
            "original_amount": converted_amount,
            "source_currency": from_currency,
            "target_currency": to_currency,
            "exchange_rate": 1.0,
            "converted_amount": converted_amount,
            "summary": summary,
        }

    try:
        quote = get_exchange_rate(from_currency, to_currency)
    except UnsupportedCurrencyError as exc:
        raise ValueError(str(exc)) from exc
    except CurrencyProviderError as exc:
        raise RuntimeError(f"Currency conversion failed: {exc}") from exc

    original_amount = Decimal(str(amount))
    converted_amount = original_amount * quote.rate
    exchange_rate = _format_decimal(quote.rate, "0.000001")
    rounded_original_amount = _format_decimal(original_amount, "0.01")
    rounded_converted_amount = _format_decimal(converted_amount, "0.01")
    summary = (
        f"{rounded_original_amount:.2f} {from_currency} is "
        f"{rounded_converted_amount:.2f} {to_currency} at an exchange rate of {exchange_rate:.6f}."
    )

    return {
        "original_amount": rounded_original_amount,
        "source_currency": from_currency,
        "target_currency": to_currency,
        "exchange_rate": exchange_rate,
        "converted_amount": rounded_converted_amount,
        "summary": summary,
    }


def get_tool_definition() -> ToolDefinition:
    """Return the currency tool definition."""
    return ToolDefinition(
        name="convert_currency",
        description="Convert an amount between two currencies.",
        parameters={
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Amount to convert.",
                },
                "from_currency": {
                    "type": "string",
                    "description": "Three-letter source currency code.",
                },
                "to_currency": {
                    "type": "string",
                    "description": "Three-letter target currency code.",
                },
            },
            "required": ["amount", "from_currency", "to_currency"],
        },
        implementation=convert_currency,
        argument_model=CurrencyArguments,
    )
