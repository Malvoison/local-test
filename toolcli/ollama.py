"""Compatibility exports for code that still imports ``toolcli.ollama``."""

from .ollama_client import OllamaClient

__all__ = ["OllamaClient"]
