---
name: python
description: Python coding conventions — Python 3.10+, type hints, stdlib-first dependencies, python-dotenv configuration, logging in except blocks, black/ruff formatting, Makefile targets, and pytest testing. Use whenever writing, modifying, reviewing or testing Python code (.py files, requirements.txt, pyproject.toml, Makefile targets for a Python project), including Flask apps, scripts and CLIs — even if the user doesn't say "Python" explicitly.
---

# Python development

## Language and dependencies

- Target Python 3.10+ unless the project specifies otherwise.
- Prefer stdlib over third-party libraries unless there is a clear, justified reason.
- Use type hints on all function signatures.

## Configuration

- Add `from dotenv import load_dotenv` to all solutions, and call `load_dotenv()` in the entry point
  before any configuration is read.

## Error handling and logging

- In an `except` block, use `logger.exception(...)` (no `exc`/`%s` interpolation needed) instead of
  `logger.error(..., exc)` — it captures the full traceback automatically, which a formatted error
  message alone discards.

## Formatting, linting and build

- Format with `black`, lint with `ruff`.
- If a `Makefile` is present with `lint`, `format`, `test`, or `build` targets, run them after completing
  your task and confirm they pass — do not proceed if they fail.

## Testing

- Write tests for non-trivial logic. Use `pytest`.
- Do not write tests that trivially pass without asserting meaningful behaviour.
