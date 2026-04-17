# GEMINI.md

## Project Overview
`toolcli` is a Python-based CLI application designed to facilitate tool-calling with the Ollama model runtime. It features a structured orchestration loop that handles multiple turns of model responses and tool executions, returning structured results to the user.

The project is organized into several key modules:
- **`toolcli/main.py`**: The primary CLI entry point.
- **`toolcli/orchestrator.py`**: The core logic for coordinating LLM chat turns and tool execution.
- **`toolcli/tool_registry.py`**: Manages registered tools and their execution.
- **`toolcli/ollama_client.py`**: An HTTP client for communicating with the Ollama API.
- **`toolcli/schemas.py`**: Pydantic models for data validation and consistency across the application.
- **`toolcli/providers/`**: Isolated integrations for external services (e.g., Open-Meteo for weather).
- **`toolcli/tools/`**: Definitions and argument validation for individual tools.

## Key Technologies
- **Python 3.11+**
- **Pydantic v2**: For data validation and settings management.
- **Requests**: For HTTP communication with Ollama and external providers.
- **Rich**: For enhanced terminal UI and response formatting.
- **Pytest**: For unit and integration testing.

## Building and Running

### Setup
Ensure you have a Python 3.11+ environment. It is recommended to use a virtual environment.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

### Running the CLI
The CLI can be run directly using the `toolcli` command or via `python3 -m toolcli`.
```bash
# Basic usage
toolcli "What is the weather in Chicago?"

# JSON output
toolcli "Convert 100 USD to EUR" --json

# List registered tools
toolcli --show-tools

# CLI options
toolcli --help
```

### Configuration
The application uses environment-backed settings. You can configure it via a `.env` file (see `.env.example`).
- `OLLAMA_BASE_URL`: The URL for the Ollama server (default: `http://localhost:11434`).
- `OLLAMA_MODEL`: The model to use for tool calling (default: `llama3`).
- `NEWS_API_KEY`: API key required for the news tool.

## Development Conventions

### Coding Style
- **Typing**: Rigorous use of Python 3.11+ type hints is required.
- **Naming**: Follow PEP 8: `snake_case` for functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- **Docstrings**: All public functions, classes, and modules should have descriptive docstrings.
- **Simplicity**: Prefer standard library solutions over adding new dependencies.

### Testing
- **Framework**: Use `pytest` for all tests.
- **Structure**: Tests are located in the `tests/` directory and should be named `test_*.py`.
- **Validation**: New features or bug fixes must include corresponding tests.
```bash
pytest
```

### Tool Implementation
- Tools should be defined in `toolcli/tools/` and registered in `toolcli/tools/__init__.py`.
- External service logic should reside in `toolcli/providers/` to keep tool definitions focused on validation and result shaping.
- Use Pydantic models for tool arguments and return values.

## Key Files
- `pyproject.toml`: Project metadata, dependencies, and entry points.
- `AGENTS.md`: Repository-specific guidelines and instructions.
- `prototype.py`: A legacy/compatibility wrapper for the CLI.
- `toolcli/config.py`: Centralized configuration management using Pydantic.
