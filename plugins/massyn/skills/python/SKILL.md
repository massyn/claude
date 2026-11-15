---
name: python
description: Python coding conventions - Python 3.10+, type hints, stdlib-first dependencies, python-dotenv configuration, logging in except blocks, black/ruff formatting, Makefile targets, and pytest testing. Use whenever writing, modifying, reviewing or testing Python code (.py files, requirements.txt, pyproject.toml, Makefile targets for a Python project), including Flask apps, scripts and CLIs - even if the user doesn't say "Python" explicitly.
---

# Python development

## Language and dependencies

- Target Python 3.10+ unless the project specifies otherwise.
- Prefer stdlib over third-party libraries unless there is a clear, justified reason.
- Use type hints on all function signatures.

## Configuration

- Add `from dotenv import load_dotenv` to all solutions, and call `load_dotenv()` in the entry point
  before any configuration is read.
- Create the virtual environment in `.venv/` (`python -m venv .venv`).
- Read file locations from the environment, with defaults from the repository layout in the devops
  skill: downloads, models and caches under `.cache/`, produced output under `data/`, committed
  configuration under `etc/` (e.g. `os.getenv("MODEL_DIR", ".cache/models")`).

## Error handling and logging

- In an `except` block, use `logger.exception(...)` (no `exc`/`%s` interpolation needed) instead of
  `logger.error(..., exc)` - it captures the full traceback automatically, which a formatted error
  message alone discards.

## Formatting, linting and build

- Format with `black`, lint with `ruff`.
- If a `Makefile` is present with `lint`, `format`, `test`, or `build` targets, run them after completing
  your task and confirm they pass - do not proceed if they fail.

## Testing

- Test conservatively. Not every function needs a test.
- The project's `CLAUDE.md` sets the testing regime - what gets tested, which commands run and when.
  Follow it.
- Where it sets none, test only logic where a bug would be costly or hard to spot: branching, parsing,
  calculations, security checks. No tests for configuration, documentation, plumbing or thin wrappers,
  and no throwaway check scripts - a check worth keeping is a real test.
- Use `pytest`. Do not write tests that trivially pass without asserting meaningful behaviour.
