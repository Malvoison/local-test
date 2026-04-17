# toolcli

Minimal Python CLI for Ollama-style tool calling, with structured tool results and isolated provider integrations.

## Structure
- `toolcli/main.py`: CLI entry point
- `toolcli/config.py`: environment-backed settings
- `toolcli/ollama_client.py`: Ollama HTTP client
- `toolcli/orchestrator.py`: prompt and tool-calling orchestration
- `toolcli/tool_registry.py`: builtin tool registration and execution
- `toolcli/schemas.py`: shared Pydantic models
- `toolcli/providers/`: external service integrations kept outside tool orchestration
- `toolcli/tools/`: tool definitions and argument validation
- `tests/`: pytest coverage for registry, orchestration, CLI, and tools

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
export NEWS_API_KEY=your_newsapi_key
```

You can also place `NEWS_API_KEY=your_newsapi_key` in `.env`.

## Run
```bash
toolcli "What time is it in America/Chicago?"
toolcli "Convert 25 USD to EUR"
toolcli "What's the weather in Chicago right now?"
toolcli "Top headlines right now"
toolcli "Latest news about AI"
python3 -m toolcli --show-tools
```

## Usage Examples
News tool for top headlines:
```json
{
  "name": "get_current_news",
  "arguments": {}
}
```

News tool for a topic search:
```json
{
  "name": "get_current_news",
  "arguments": {
    "topic": "ai"
  }
}
```

Successful result shape:
```json
{
  "topic": "ai",
  "headlines": [
    {
      "title": "AI Headline",
      "source": "Tech Source",
      "url": "https://example.test/story",
      "published_at": "2026-04-16T12:00:00Z",
      "description": "Story description"
    }
  ],
  "count": 1,
  "summary": "Here are 1 headlines about ai: AI Headline."
}
```

Weather tool:
```json
{
  "name": "get_current_weather",
  "arguments": {
    "city": "Chicago",
    "unit": "celsius"
  }
}
```

Successful result shape:
```json
{
  "resolved_location": "Chicago, Illinois, United States",
  "latitude": 41.8781,
  "longitude": -87.6298,
  "temperature": 19.4,
  "unit": "celsius",
  "weather_description": "Partly cloudy",
  "summary": "It is currently 19.4C in Chicago, Illinois, United States with partly cloudy."
}
```

Time tool:
```json
{
  "name": "get_current_time",
  "arguments": {
    "timezone": "America/Chicago"
  }
}
```

Successful result shape:
```json
{
  "timezone": "America/Chicago",
  "current_time": "2026-04-16T12:34:56-05:00",
  "date": "2026-04-16",
  "time": "12:34:56",
  "timezone_abbreviation": "CDT",
  "utc_offset": "-05:00",
  "is_dst": true,
  "summary": "The current time in America/Chicago is 2026-04-16 12:34:56 CDT."
}
```

Currency tool:
```json
{
  "name": "convert_currency",
  "arguments": {
    "amount": 25,
    "from_currency": "usd",
    "to_currency": "eur"
  }
}
```

Successful result shape:
```json
{
  "original_amount": 25.0,
  "source_currency": "USD",
  "target_currency": "EUR",
  "exchange_rate": 0.92,
  "converted_amount": 23.0,
  "summary": "25.00 USD is 23.00 EUR at an exchange rate of 0.920000."
}
```

## Test
```bash
pytest
python3 -m py_compile prototype.py toolcli/*.py toolcli/tools/*.py toolcli/providers/*.py
python3 -m toolcli --help
python3 prototype.py --help
```

## Architecture Note
The registry and orchestrator stay generic: they validate tool arguments, execute tool functions, and pass structured results back into the model loop. Provider-specific HTTP logic lives under `toolcli/providers/`, so tools can focus on validation, normalization, and shaping readable summaries without embedding networking code into orchestration layers.

Weather provider note: weather geocoding uses the Open-Meteo geocoding API and current conditions use the Open-Meteo forecast API.
News provider note: news lookups use NewsAPI for both US top headlines and topic-based article search.

Missing `NEWS_API_KEY` behavior: in normal CLI mode the run fails with a readable tool error in the assistant/orchestrator result path, and in `--json` mode the structured payload includes an `execution_error` entry with the missing-key message.
