# toolcli

`toolcli` is a Python CLI for Ollama-based tool calling. It sends a prompt to a local Ollama model, lets the model call registered tools when needed, executes those tools safely, and feeds structured tool results back into the model before printing a final answer.

The app currently includes:
- `get_current_time` for IANA timezone lookups
- `get_current_weather` for current weather by city
- `get_current_news` for top headlines or topic-specific news
- `convert_currency` for live currency conversion

**What The App Does**
`toolcli` gives you one command-line entry point for:
- direct chat with Ollama
- structured tool calling
- readable terminal output
- machine-readable JSON output
- isolated provider integrations for external APIs

**Architecture**
The application is intentionally split into small modules:
- `toolcli/main.py`: CLI argument parsing, exit codes, JSON serialization, and top-level flow
- `toolcli/ollama_client.py`: HTTP client for the Ollama chat API
- `toolcli/orchestrator.py`: tool-calling loop that sends messages, executes tools, and re-prompts Ollama
- `toolcli/tool_registry.py`: tool registration, lookup, and safe execution
- `toolcli/tools/`: user-facing tool implementations and argument validation
- `toolcli/providers/`: provider-specific HTTP logic and response normalization
- `toolcli/config.py`: `.env` and environment-backed settings
- `toolcli/ui.py`: restrained Rich-based terminal output
- `tests/`: pytest coverage for CLI behavior, orchestration, tools, config, and providers

The key boundary is:
- tools validate inputs and shape outputs
- providers own HTTP calls and provider response parsing
- the orchestrator remains generic and does not know provider-specific details

**Installation**
Requirements:
- Python 3.11+
- Ollama installed locally

Clone the repository, then create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

**Ollama Setup**
Install and start Ollama first. Then pull the default model used by this app:

```bash
ollama pull gemma4:e4b
```

If you want to verify Ollama is up:

```bash
ollama list
```

The CLI defaults to:
- base URL: `http://localhost:11434`
- model: `gemma4:e4b`

You can override either with CLI flags or `.env`.

**Environment Configuration**
Copy the example environment file and adjust values as needed:

```bash
cp .env.example .env
```

Supported settings:
- `OLLAMA_BASE_URL`: Ollama HTTP endpoint
- `OLLAMA_MODEL`: default model name
- `NEWS_API_KEY`: required only for the news tool
- `REQUEST_TIMEOUT`: request timeout in seconds
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`

Example `.env`:

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
NEWS_API_KEY=your_newsapi_key
REQUEST_TIMEOUT=30.0
LOG_LEVEL=INFO
```

**NEWS_API_KEY Setup**
The news tool uses NewsAPI and requires `NEWS_API_KEY`.

Set it in one of these ways:

```bash
export NEWS_API_KEY=your_newsapi_key
```

or:

```dotenv
NEWS_API_KEY=your_newsapi_key
```

If the key is missing:
- human-readable mode shows a clear failure message
- `--json` mode returns an `execution_error` entry in `errors`

**Running The CLI**
Basic examples:

```bash
toolcli "What time is it in America/Chicago?"
toolcli "What's the weather in Chicago right now?"
toolcli "Convert 25 USD to EUR"
toolcli "Top headlines right now"
toolcli "Latest news about AI"
```

You can also invoke the module directly:

```bash
python3 -m toolcli "What time is it in UTC?"
python3 prototype.py "Convert 10 USD to EUR"
```

**JSON Mode**
Use `--json` for machine-readable output:

```bash
toolcli --json "Latest news about AI"
```

Example shape:

```json
{
  "success": true,
  "model": "gemma4:e4b",
  "prompt": "Latest news about AI",
  "tools_used": [
    {
      "name": "get_current_news",
      "arguments": {
        "topic": "AI"
      },
      "result": {
        "topic": "AI",
        "headlines": [],
        "count": 0,
        "summary": ""
      },
      "success": true,
      "error": null
    }
  ],
  "final_answer": "Here are the latest AI headlines.",
  "errors": []
}
```

**Verbose Mode**
Use `--verbose` to keep normal human-readable output but also print a concise tool trace:

```bash
toolcli --verbose "What's the weather in Chicago right now?"
```

Verbose mode is useful when you want to see:
- which tools were called
- the arguments sent to each tool
- whether a tool call succeeded or failed

**Disabling Tools**
Use `--no-tools` to skip tool registration entirely and send the prompt directly to Ollama:

```bash
toolcli --no-tools "Explain daylight saving time in one paragraph."
```

In this mode:
- no tool definitions are sent
- the orchestrator is bypassed
- the response is a direct chat completion from Ollama

**Showing Registered Tools**
Use `--show-tools` to print the tool catalog and exit:

```bash
toolcli --show-tools
toolcli --json --show-tools
```

**How Tool Calling Works**
At a high level:
1. The CLI resolves config and builds runtime options.
2. The registry exposes tool definitions in the JSON schema format expected by Ollama.
3. The prompt and tool definitions are sent to Ollama.
4. If Ollama emits tool calls, the orchestrator validates arguments and executes the requested tools.
5. Tool results are appended as tool messages.
6. Ollama receives the updated conversation and produces a final answer.
7. The CLI renders either human-readable output or JSON.

Tool execution is safe by design:
- arguments are validated with Pydantic
- tool exceptions are converted into structured errors
- provider HTTP logic stays outside the orchestrator

**How To Add A New Tool**
Add a new tool in four steps:

1. Create a provider if external HTTP logic is needed.
   Example: `toolcli/providers/stocks.py`

2. Create the tool module in `toolcli/tools/`.
   The module should:
   - define a Pydantic argument model
   - validate and normalize inputs
   - call the provider or internal logic
   - return structured output plus a friendly summary

3. Register the tool in [toolcli/tools/__init__.py](/home/allawyer66/local-test/toolcli/tools/__init__.py).

4. Add tests under `tests/`.
   Prefer:
   - mocked provider/unit tests
   - registry execution tests
   - orchestrator or CLI coverage only where it adds value

Minimal shape:

```python
from pydantic import BaseModel

from ..schemas import ToolDefinition


class ExampleArguments(BaseModel):
    value: str


def run_example(value: str) -> dict[str, object]:
    return {
        "value": value,
        "summary": f"Example output for {value}.",
    }


def get_tool_definition() -> ToolDefinition:
    return ToolDefinition(
        name="run_example",
        description="Run the example tool.",
        parameters={
            "type": "object",
            "properties": {
                "value": {"type": "string", "description": "Input value."}
            },
            "required": ["value"],
        },
        implementation=run_example,
        argument_model=ExampleArguments,
    )
```

**Testing**
Run the full test suite:

```bash
pytest
```

Useful validation commands:

```bash
python3 -m py_compile prototype.py toolcli/*.py toolcli/tools/*.py toolcli/providers/*.py
python3 -m toolcli --help
python3 prototype.py --help
```

**Final Validation Checklist**
Run unit tests:

```bash
pytest
```

Run the CLI:

```bash
toolcli "What time is it in America/Chicago?"
```

Test a tool-enabled prompt:

```bash
toolcli "What's the weather in Chicago right now?"
```

Test JSON output:

```bash
toolcli --json "Latest news about AI"
```

**Exit Codes**
The CLI uses explicit exit codes:
- `0`: success
- `2`: invalid command usage
- `3`: config error
- `4`: Ollama/client failure
- `5`: upstream tool/provider failure that prevented completion

**Source Tree**
Core project tree:

```text
.
├── .env.example
├── README.md
├── prototype.py
├── pyproject.toml
├── tests/
│   ├── test_cli_smoke.py
│   ├── test_config.py
│   ├── test_currency_tool.py
│   ├── test_news_tool.py
│   ├── test_ollama_client.py
│   ├── test_orchestrator.py
│   ├── test_registry.py
│   ├── test_time_tool.py
│   └── test_weather_tool.py
└── toolcli/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── config.py
    ├── main.py
    ├── ollama.py
    ├── ollama_client.py
    ├── orchestrator.py
    ├── providers/
    │   ├── __init__.py
    │   ├── currency.py
    │   ├── news.py
    │   └── weather.py
    ├── schemas.py
    ├── tool_registry.py
    ├── tools/
    │   ├── __init__.py
    │   ├── currency.py
    │   ├── news.py
    │   ├── time_tool.py
    │   └── weather.py
    └── ui.py
```
