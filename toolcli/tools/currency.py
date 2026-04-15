"""Placeholder currency conversion tool."""

from __future__ import annotations

from pydantic import BaseModel

from ..schemas import ToolDefinition


class CurrencyArguments(BaseModel):
    """Validated arguments for the currency tool."""

    amount: float
    from_currency: str
    to_currency: str


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict[str, object]:
    """Return placeholder currency conversion data."""
    return {
        "amount": amount,
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "converted_amount": amount,
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
