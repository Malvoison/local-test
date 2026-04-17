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

## Beads Issue Tracking (MANDATORY WORKFLOW)

Beads is the single source of truth for all tasks in this repository. It is designed for parallel agent collaboration, deterministic tracking via hash-based IDs, and offline-first semantic dependencies. All agents (Codex, Copilot, Gemini) MUST use Beads to find, claim, and track work.

### Why and When to Use Beads
- **Why:** To prevent duplicate work, maintain a clear audit trail, and enable seamless handoffs between agents and human collaborators.
- **When:** 
  - **Start of Session:** Find available work that isn't blocked or claimed.
  - **During Work:** Claim an issue, create new issues for discovered bugs/tasks, and update progress.
  - **End of Session:** Ensure all task state is committed and pushed.

### How to Use Beads (Core Commands)
- **Find Ready Work:** `bd ready --json` (Lists issues with no blockers and no assignee).
- **Claim Work:** `bd update <issue-id> --status in_progress --assignee <agent_name>`
- **Create Discovered Work:** `bd create "Title" -t <type> -p <priority> --deps discovered-from:<parent-id>`
- **Close Work:** `bd close <issue-id> --reason "Completed"`

### Parallel Execution & Worktrees
**CRITICAL RULE:** Agents MUST NEVER modify source code directly in the main repository root. To enable parallel work and clean PR isolation, all tasks must be executed in a dedicated git worktree.

1. **Create Worktree:** `bd worktree create .worktrees/<issue-id> --branch <branch-name>`
2. **Navigate to Worktree:** `cd .worktrees/<issue-id>`
3. **Execute Task:** Perform all coding, testing, and committing within this isolated directory.
4. **Push Work:** Commit and push the branch from within the worktree.
5. **Clean Up:** Once the PR is merged or the task is complete, remove the worktree: `bd worktree remove .worktrees/<issue-id>`.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until all changes are pushed and the Beads state is synced.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up.
2. **Commit and Push from Worktree** - Ensure all code changes in your worktree are committed and the branch is pushed to the remote.
3. **Update issue status** - Close finished work in Beads, update in-progress items.
4. **Sync Beads Database** - In the main repository root:
   ```bash
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Remove the worktree if the task is finished: `bd worktree remove .worktrees/<issue-id>`.
6. **Verify** - All changes committed AND pushed, Beads state synced.
7. **Hand off** - Provide context for next session.

**CRITICAL RULES:**
- Work is NOT complete until `git push` (for both code and Beads state) succeeds.
- NEVER stop before pushing - that leaves work stranded locally.
- NEVER modify code in the main repo root; ALWAYS use `.worktrees/`.
