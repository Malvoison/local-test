# Code Review Checklist — Ollama Tool-Calling CLI Application

**Reviewer:**  
**Date:**  
**Repository / Commit:**  
**Overall Verdict:** ☐ Ready ☐ Mostly Ready ☐ Not Ready

## Review Instructions
For each item, mark one:
- ☐ Pass
- ☐ Partial
- ☐ Fail
- ☐ N/A

For every **Partial** or **Fail**, include:
- **Files reviewed:**  
- **Finding:**  
- **Why it matters:**  
- **Recommended fix:**  

---

# 1. Project Structure and Boundaries

## AC-1.1 Project is organized into clear modules
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - CLI entry point is separate from config, orchestration, and tool code.
  - Ollama client exists as its own module/class.
  - Tool implementations live in dedicated modules/package.
  - Tests are separated from runtime code.

## AC-1.2 Module responsibilities are separated cleanly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - CLI parses arguments and invokes services.
  - Config module loads and validates settings.
  - Ollama client only handles model API communication.
  - Orchestrator owns the model/tool loop.
  - Registry owns tool definitions and dispatch.
  - Tool modules encapsulate provider/API logic.
  - UI/output logic is not tangled into core orchestration.

## AC-1.3 New tools can be added without changing core orchestration
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Adding a new tool requires only a tool module and a small registration step.
  - No `if/elif` dispatch chain in orchestration for tool execution.
  - No edits required across multiple unrelated modules.

---

# 2. Configuration and Startup Behavior

## AC-2.1 Configuration is environment-driven
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Settings are loaded from environment variables and optionally `.env`.
  - Expected settings are present:
    - `OLLAMA_BASE_URL`
    - `OLLAMA_MODEL`
    - `NEWS_API_KEY`
    - `REQUEST_TIMEOUT`
    - `LOG_LEVEL`

## AC-2.2 Configuration has sensible defaults
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Non-secret settings have defaults.
  - Defaults are suitable for local Ollama usage.

## AC-2.3 Configuration is validated
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Invalid config values fail early and clearly.
  - Numeric and enum-like values are validated.

## AC-2.4 Secrets are handled safely
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - No hard-coded API keys in source.
  - No secrets in `.env.example`.
  - Logs and README do not expose secrets.

---

# 3. CLI Behavior

## AC-3.1 CLI supports required invocation patterns
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Positional prompt is supported.
  - These flags exist and work:
    - `--model`
    - `--base-url`
    - `--json`
    - `--verbose`
    - `--no-tools`
    - `--timeout`
    - `--max-tool-rounds`
    - `--system-prompt`
    - `--show-tools`

## AC-3.2 CLI overrides configuration cleanly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - CLI arguments override config values predictably.
  - Override behavior is visible in runtime behavior or documented.

## AC-3.3 CLI failure modes are human-readable
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Fatal errors print plain-English terminal messages.
  - Fatal failures return nonzero exit codes.
  - Default path does not dump raw stack traces.

## AC-3.4 `--show-tools` is a pure inspection mode
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - It lists tools and exits.
  - It does not call Ollama.
  - It does not execute any tools.

## AC-3.5 `--no-tools` genuinely disables tool use
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Tool schemas are not sent when this flag is set.
  - No local tool execution occurs.

---

# 4. Ollama Client

## AC-4.1 Dedicated Ollama client abstraction exists
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Ollama API communication is centralized.
  - No scattered raw HTTP calls to Ollama.

## AC-4.2 HTTP implementation is maintainable
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Uses `requests` or another intentional HTTP client.
  - Timeouts are explicit.

## AC-4.3 Client request payloads are constructed cleanly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Model, messages, tool definitions, and timeout are passed clearly.
  - Payload shape aligns with Ollama chat API expectations.

## AC-4.4 Client errors are normalized
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Connection, timeout, bad status, and malformed response errors are translated into useful app-level errors.

## AC-4.5 Response parsing is defensive
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Missing fields, malformed JSON, and absent content/tool-call fields are handled safely.

---

# 5. Tool Registry and Execution Boundaries

## AC-5.1 Tool execution is controlled by a formal registry
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Only registered tools can be executed.
  - Lookup is by explicit tool name.
  - No arbitrary function execution.

## AC-5.2 Each tool has a complete definition
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Each tool includes:
    - name
    - description
    - parameter schema
    - implementation callable
    - validation path

## AC-5.3 Tool argument validation is real
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Invalid or missing arguments are rejected before execution.
  - Validation errors are informative.

## AC-5.4 Tool execution is safely wrapped
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Tool failures are caught and surfaced cleanly.
  - One bad tool call does not crash the whole app unless the failure is truly fatal.

---

# 6. Orchestration Loop

## AC-6.1 Model → tool → model loop is implemented correctly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Initial request includes tool definitions when enabled.
  - Tool calls are detected.
  - Approved tools are executed.
  - Tool results are appended back into conversation history.
  - Final model synthesis occurs after tool execution.

## AC-6.2 Multiple tool rounds are supported and bounded
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Repeated tool rounds are supported.
  - Rounds are capped by config/CLI.
  - Infinite loops are prevented.

## AC-6.3 Unknown tool requests are handled safely
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Unknown tool names do not execute anything.
  - Errors are surfaced clearly.

## AC-6.4 Malformed tool calls are handled safely
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Missing arguments or wrong shapes do not crash the app.
  - The failure is reported clearly.

## AC-6.5 Orchestrator returns a coherent result object
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Structured result includes at least:
    - prompt
    - model
    - tools used
    - final answer
    - errors
    - success indicator

---

# 7. Individual Tools

## 7A. Time Tool

### AC-7A.1 Time tool validates timezone input
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Accepts valid IANA timezone names.
  - Rejects invalid timezone strings cleanly.

### AC-7A.2 Time tool returns structured and readable output
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Returns machine-usable data.
  - Returns a readable summary.

---

## 7B. Currency Tool

### AC-7B.1 Currency tool validates inputs
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Amount must be numeric and > 0.
  - Currency codes are normalized/validated.

### AC-7B.2 Currency tool isolates provider logic
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - HTTP/provider code is not mixed into orchestration or registry.

### AC-7B.3 Currency tool returns a complete conversion result
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Result includes:
    - original amount
    - source currency
    - target currency
    - exchange rate
    - converted amount
    - readable summary

---

## 7C. Weather Tool

### AC-7C.1 Weather tool validates required arguments
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - `city` is required and non-empty.
  - `unit` only allows supported values.

### AC-7C.2 Weather tool handles geocoding and weather retrieval cleanly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Geocoding logic is encapsulated.
  - Weather lookup logic is encapsulated.
  - City-not-found and provider failures are handled.

### AC-7C.3 Weather tool returns structured weather data
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Result includes meaningful structured fields and a friendly summary.

---

## 7D. News Tool

### AC-7D.1 News tool handles missing API key honestly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Missing `NEWS_API_KEY` produces a clear error.
  - No fake success result.

### AC-7D.2 News tool supports headlines and topic search
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - No-topic case returns general headlines.
  - Topic case returns filtered results.

### AC-7D.3 News tool limits and structures results sensibly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Results are capped reasonably.
  - Output is structured and summarized.
  - Raw provider payload is not leaked directly.

---

# 8. Output Modes and UX

## AC-8.1 Human-readable mode is restrained and useful
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Default output is concise and readable.
  - Verbose mode adds useful execution details without chaos.

## AC-8.2 JSON mode emits valid structured JSON
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Output is valid JSON.
  - Expected fields are present.
  - Tool usage and errors are explicit.

## AC-8.3 Logs and stdout contracts are separated
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Logs do not corrupt JSON stdout.
  - Machine-readable mode stays machine-readable.

---

# 9. Logging and Observability

## AC-9.1 Logging levels behave correctly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - INFO is default.
  - DEBUG is enabled by verbose mode or config.
  - ERROR is used for failures.

## AC-9.2 Logs are useful and not reckless
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Logs help trace request flow, tool activity, and failures.
  - Secrets and API keys are omitted or redacted.

---

# 10. Error Handling and Exit Behavior

## AC-10.1 Fatal failures exit nonzero
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Startup/config failures return nonzero.
  - Ollama unavailable returns nonzero.
  - Other fatal failures return nonzero.

## AC-10.2 Common failure modes are explicitly handled
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Deliberate handling exists for:
    - Ollama unavailable
    - timeout
    - malformed model response
    - unknown tool
    - invalid tool args
    - upstream provider failure
    - missing API key
    - invalid timezone
    - unsupported currency code

## AC-10.3 App fails honestly
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Error messages describe the actual failure.
  - No fabricated success on provider/model failure.

---

# 11. Testing

## AC-11.1 Core modules have automated tests
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Tests exist for:
    - config
    - registry
    - CLI smoke behavior
    - Ollama client
    - orchestrator
    - each tool or provider logic

## AC-11.2 Tests cover success and failure paths
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Happy paths are covered.
  - Representative error paths are covered.

## AC-11.3 Tests do not depend on live services by default
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Unit tests mock/fake HTTP calls.
  - Local Ollama is not required for ordinary test runs.

## AC-11.4 CLI output contracts are tested
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - JSON mode is tested.
  - Nonzero exit behavior is tested.
  - `--show-tools` and `--no-tools` are tested.

---

# 12. Documentation and Delivery Quality

## AC-12.1 README is complete and usable
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - README covers:
    - purpose
    - setup
    - env configuration
    - Ollama setup
    - pulling model
    - example commands
    - JSON mode
    - verbose mode
    - disabling tools
    - testing
    - adding a new tool

## AC-12.2 `.env.example` is accurate and safe
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Matches actual config surface.
  - Contains no real secrets.

## AC-12.3 Dependency metadata is coherent
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - `pyproject.toml` or equivalent contains required runtime/test dependencies.
  - Fresh setup should work without mystery packages.

---

# 13. Code Quality

## AC-13.1 Public interfaces are typed
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Public functions/classes have useful type hints.

## AC-13.2 Public code has useful docstrings
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Important public functions/classes explain purpose and behavior.

## AC-13.3 Code is readable and unsurprising
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - Logic is straightforward.
  - Functions are not absurdly large.
  - There is limited duplication.
  - The code is not trying to win a county fair for cleverness.

## AC-13.4 Final delivery contains no obvious placeholder leftovers
- ☐ Pass ☐ Partial ☐ Fail ☐ N/A  
  **Checks:**
  - No major scaffold stubs remain.
  - TODOs do not conceal missing core behavior.

---

# Summary

## Executive Summary
- **Overall readiness:** ☐ Ready ☐ Mostly Ready ☐ Not Ready
- **Top strengths:**
  1. 
  2. 
  3. 
  4. 
  5. 

- **Top risks:**
  1. 
  2. 
  3. 
  4. 
  5. 

## Defect List

### P0 — Must Fix Before Merge
- 

### P1 — Should Fix Soon
- 

### P2 — Polish / Maintainability
- 

## Test Gaps
- 
- 
- 

## Files / Evidence Reviewed
- 
- 
- 
