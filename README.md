# toolcli

Minimal scaffold for a maintainable Python CLI that will later support Ollama-based tool calling.

## Structure
- `toolcli/main.py`: CLI entry point
- `toolcli/config.py`: environment-backed settings
- `toolcli/ollama_client.py`: placeholder Ollama client
- `toolcli/orchestrator.py`: placeholder prompt orchestration
- `toolcli/tool_registry.py`: builtin tool registration
- `toolcli/schemas.py`: shared Pydantic models
- `toolcli/ui.py`: terminal rendering with Rich
- `toolcli/tools/`: placeholder tool modules
- `tests/`: basic scaffold tests

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
```

## Run
```bash
toolcli "hello from the scaffold"
```

## Test
```bash
pytest
```

The current CLI prints a placeholder response only. Real Ollama calls and tool execution are intentionally not implemented in this phase.
