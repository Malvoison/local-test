# Copilot Instructions for toolcli

## Beads & Parallel Workflows
All work in this repository is managed through **Beads** and MUST be performed in parallel git worktrees located at `.worktrees/<issue-id>`.

- **NEVER** modify source code in the main repository root.
- **ALWAYS** check `AGENTS.md` for the mandatory Beads issue-tracking and worktree workflow.
- **ALWAYS** claim an issue in Beads before starting work.
- **ALWAYS** sync the Beads state (`bd sync && git push`) when finishing a session.

## Quick Start Commands

### Build & Validation
- **Syntax check**: `python3 -m py_compile prototype.py toolcli/*.py toolcli/tools/*.py toolcli/providers/*.py`
- **Full test suite**: `pytest`
- **Single test**: `pytest tests/test_<module>.py::test_<function_name> -xvs`
- **Module help**: `python3 -m toolcli --help` or `python3 prototype.py --help`

### Running the CLI
- **Basic**: `toolcli "weather in Chicago"`
- **With options**: `toolcli --json "Convert 100 USD to EUR"` or `toolcli --verbose "Top news"`
- **Direct via module**: `python3 -m toolcli "What time is it?"`
- **Legacy wrapper**: `python3 prototype.py "..."` (for backwards compatibility)

### Testing Individual Tools
Test tool definitions and registration without full orchestration:
```bash
pytest tests/test_weather_tool.py -xvs
pytest tests/test_currency_tool.py::test_conversion -xvs
```

## Architecture

### Core Data Flow
1. **CLI entry** (`toolcli/main.py`): Parses args, loads config, handles output formatting
2. **Orchestration loop** (`toolcli/orchestrator.py`): Manages multi-turn chat with Ollama
   - Sends prompt + tool definitions to Ollama
   - Extracts tool calls from model response
   - Validates & executes tools via registry
   - Appends results back into conversation for next turn
3. **Tool registry** (`toolcli/tool_registry.py`): Registers, validates, and executes tools safely
4. **Ollama client** (`toolcli/ollama_client.py`): HTTP wrapper for Ollama chat API

### Module Organization
```
toolcli/
├── main.py              # CLI entry, arg parsing, exit codes
├── cli.py               # Argument parsing (legacy, see main.py)
├── orchestrator.py      # Multi-turn tool-calling loop
├── tool_registry.py     # Tool lookup and execution dispatch
├── ollama_client.py     # HTTP client + response parsing
├── schemas.py           # Pydantic models (RuntimeOptions, ToolActivity, etc.)
├── config.py            # Settings management (.env, environment variables)
├── ui.py                # Rich-based terminal output (logging, formatting)
├── tools/               # Tool implementations & validation
│   ├── __init__.py      # Tool registration
│   ├── weather.py       # get_current_weather tool
│   ├── currency.py      # convert_currency tool
│   ├── time_tool.py     # get_current_time tool
│   └── news.py          # get_current_news tool
└── providers/           # External API integrations
    ├── weather.py       # Open-Meteo HTTP client
    ├── currency.py      # Currency API HTTP client
    └── news.py          # NewsAPI HTTP client
```

### Key Boundaries
- **Tools** define input validation (Pydantic models) and output shaping; they call providers but never make HTTP requests directly
- **Providers** own HTTP logic, response parsing, and error handling for external APIs
- **Orchestrator** is generic and provider-agnostic; it doesn't know about specific APIs or tools
- **Schemas** centralize all Pydantic models to prevent circular imports and ensure consistency

## Key Conventions

### Tool Implementation Pattern
Every tool follows this structure:
1. Define a Pydantic `ArgumentModel` class for input validation
2. Implement a `run_<tool_name>()` function that returns `dict[str, object]` with `summary` field
3. Create a `get_tool_definition()` function returning a `ToolDefinition` that includes the Pydantic model
4. Register in `toolcli/tools/__init__.py`

Example:
```python
from pydantic import BaseModel
from ..schemas import ToolDefinition

class MyArguments(BaseModel):
    param: str

def run_my_tool(param: str) -> dict[str, object]:
    result = do_work(param)
    return {
        "param": param,
        "result": result,
        "summary": f"Processed {param}.",
    }

def get_tool_definition() -> ToolDefinition:
    return ToolDefinition(
        name="run_my_tool",
        description="Does something.",
        parameters={"type": "object", "properties": {...}, "required": [...]},
        implementation=run_my_tool,
        argument_model=MyArguments,
    )
```

### Pydantic & Validation
- Use Pydantic v2 (available as `BaseModel` import)
- All tool arguments must be validated with a Pydantic model
- Return types are always `dict[str, object]`; include a `summary` field for human-readable output
- Provider functions can raise `Exception`; orchestrator converts to structured errors

### Error Handling
- Tool exceptions are caught, logged, and converted to `execution_error` in JSON output
- Provider HTTP failures should include clear error messages (user sees them in both text and JSON modes)
- Configuration errors raise `ValidationError` and exit with code 3
- Ollama connection failures exit with code 4

### Testing
- Use `pytest` (installed via `[dev]` extra)
- Prefer **unit tests** with mocked providers over integration tests
- Test tool execution via registry, not the full orchestrator, unless the behavior is orchestrator-specific
- Provider tests should mock HTTP responses
- CLI tests use `test_cli_smoke.py` for end-to-end validation

### Configuration
- All runtime settings use `.env` or environment variables
- See `.env.example` for all available settings
- `NEWS_API_KEY` is required only for the news tool; other tools work without it
- `OLLAMA_BASE_URL` defaults to `http://localhost:11434`
- `OLLAMA_MODEL` defaults to `gemma4:e4b` (per README)

### Exit Codes
- `0`: Success
- `2`: Invalid command usage
- `3`: Configuration error (missing/invalid settings)
- `4`: Ollama/client failure (connection, response parsing)
- `5`: Tool/provider failure that prevented completion

### Output Modes
- **Human-readable** (default): Rich-formatted text with tool trace if `--verbose`
- **JSON** (`--json`): Structured output with `success`, `tools_used`, `final_answer`, `errors` fields
- **No tools** (`--no-tools`): Direct chat with Ollama, skip orchestration
- **Show tools** (`--show-tools`): Dump registered tool definitions and exit

## Before Adding a New Tool

1. **Decide if you need a provider**
   - If the tool makes external HTTP calls, create `toolcli/providers/<name>.py`
   - Internal-only tools (e.g., timezone lookups) don't need providers

2. **Implement the tool** in `toolcli/tools/<name>.py`
   - Define a Pydantic argument model
   - Implement `run_<name>()` function
   - Create `get_tool_definition()` with proper JSON schema

3. **Register in** `toolcli/tools/__init__.py`
   - Import and call `get_tool_definition()` in the registry builder

4. **Add tests** in `tests/test_<name>_tool.py`
   - Mock provider HTTP calls if present
   - Test registry execution, not just the provider
   - Cover error cases (invalid args, API failures)

5. **Update `.env.example`** if new environment variables are needed

## Language Server & Type Checking

This repository uses **Pyright** for Python type checking and LSP support. Pyright is configured to strict mode and installed during setup.

### Using the Python LSP

When Copilot starts, Pyright LSP is available for:
- **Symbol lookup**: Jump to tool definitions, provider implementations, and model classes
- **Type diagnostics**: Hover for type information; errors shown inline
- **Go-to-definition**: Navigate from tool registry calls to implementations, from providers to APIs
- **Refactoring**: Rename symbols across the codebase with confidence

### Type Checking Workflow

Run type checks locally before committing:
```bash
pyright
```

Pyright is strict and catches:
- Type mismatches in function arguments (especially Pydantic models)
- Missing `Optional[]` annotations on fields that can be `None`
- Incorrect return type annotations
- Unused imports

When adding tools or providers, ensure:
- Pydantic models inherit from `BaseModel`
- Tool functions have explicit return type: `dict[str, object]`
- Provider functions specify return types
- All function parameters are type-hinted

## Common Debugging Tips

- **"Tool not found"**: Check tool is registered in `toolcli/tools/__init__.py`
- **Pydantic validation error**: Verify argument names match tool definition and Pydantic model
- **NEWS_API_KEY required**: Set via `.env` or `export NEWS_API_KEY=...` before running
- **Ollama not responding**: Ensure `ollama` is running and `OLLAMA_BASE_URL` is correct
- **Empty tool results**: Check that `run_<tool>()` returns a dict with a `summary` field
- **Test suite fails**: Run `python3 -m py_compile` first to catch syntax errors
- **Pyright errors on Pydantic**: Ensure Pydantic models use `from pydantic import BaseModel` and proper type hints

## Related Documentation

- **README.md**: User-facing overview and running examples
- **AGENTS.md**: Legacy guidelines (superseded by this file for Copilot)
- **GEMINI.md**: Architecture and tech stack overview
- **pyproject.toml**: Package dependencies and entry points
