"""Compatibility exports for code that still imports ``toolcli.cli``."""

from .main import build_parser, main

__all__ = ["build_parser", "main"]
