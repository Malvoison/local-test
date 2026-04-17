Add carefully scoped optional enhancements to the existing application without breaking current behavior.

Possible enhancements:
- retry with backoff for upstream HTTP requests
- response caching during a single run
- REPL mode for multi-turn chat
- dry-run mode to show proposed tool calls without executing them
- optional streaming output if practical with Ollama

Rules:
- keep each enhancement isolated
- do not rewrite core architecture
- preserve existing CLI behavior
- add tests for each enhancement implemented

Before coding, state which enhancements you are implementing.
Then provide updated source, tests, and README changes.
