# Repository Guidelines

## Project Structure & Module Organization
- `toolcli/` contains the application package.
- `toolcli/cli.py` handles argument parsing and terminal output.
- `toolcli/ollama.py` contains the local Ollama HTTP client.
- `toolcli/tools.py` defines the registered tool functions and tool schema.
- `prototype.py` is a compatibility wrapper for the original entry point.
- `pyproject.toml` defines package metadata and the `toolcli` console script.
- There is no `tests/` directory yet. Add new tests under `tests/` rather than mixing them into `toolcli/`.

## Build, Test, and Development Commands
- `python3 -m py_compile prototype.py toolcli/*.py`
  Checks syntax for the current codebase.
- `python3 -m toolcli --help`
  Verifies the packaged CLI entry point loads correctly.
- `python3 prototype.py --help`
  Verifies the legacy wrapper still works.
- `python3 -m toolcli "weather in Chicago"`
  Runs the CLI locally against Ollama and the registered tools.

## Coding Style & Naming Conventions
- Use Python 3.11+ features and type hints throughout.
- Use 4-space indentation and keep functions focused and small.
- Add docstrings to public functions and classes.
- Prefer straightforward standard-library solutions over new dependencies.
- Use `snake_case` for functions and variables, `UPPER_SNAKE_CASE` for module constants, and concise module names such as `cli.py` or `tools.py`.
- Avoid adding shell execution, dynamic code execution, or unrelated framework code.

## Testing Guidelines
- No formal test suite exists yet; add `pytest`-style tests in `tests/` for new behavior.
- Name test files `test_<module>.py` and test functions `test_<behavior>()`.
- Cover argument parsing, tool dispatch, and error handling before adding network-heavy integration tests.
- For now, run the syntax and `--help` commands above before opening a PR.

## Commit & Pull Request Guidelines
- Current history uses short, imperative commit messages such as `adding prototype`.
- Prefer concise imperative subjects, for example `add CLI package structure`.
- Keep commits scoped to one change set.
- PRs should explain the user-visible change, list validation commands run, and note any assumptions or follow-up work.

## Security & Configuration Tips
- Do not hardcode secrets. Set `NEWS_API_KEY` in the environment when testing news functionality.
- Treat external HTTP APIs and Ollama as runtime dependencies; handle failures with clear terminal errors.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
