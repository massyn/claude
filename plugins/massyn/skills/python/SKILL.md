---
name: python
description: Python coding conventions - Python 3.10+, type hints, stdlib-first dependencies, python-dotenv configuration, a run.sh that builds the .venv and starts the app, logging in except blocks, black/ruff formatting, Makefile targets, and pytest testing. Use whenever writing, modifying, reviewing or testing Python code (.py files, requirements.txt, pyproject.toml, Makefile targets for a Python project), including Flask apps, scripts and CLIs - even if the user doesn't say "Python" explicitly.
---

# Python development

## Language and dependencies

- Target Python 3.10+ unless the project specifies otherwise.
- Prefer stdlib over third-party libraries unless there is a clear, justified reason.
- Use type hints on all function signatures.

## Configuration

- Add `from dotenv import load_dotenv` to all solutions, and call `load_dotenv()` in the entry point
  before any configuration is read.
- **NEVER read `.env` - ever.** No Read tool, `cat`, `grep`, `head`, `python`, or any other way of
  opening or printing it. Checking that it exists (`[ -f .env ]`) is the limit. Use `.env.example`
  to see which keys are expected, and ask the user to check a value if debugging needs one.
- Read file locations from the environment, with defaults from the repository layout in the devops
  skill: downloads, models and caches under `.cache/`, produced output under `data/`, committed
  configuration under `etc/` (e.g. `os.getenv("MODEL_DIR", ".cache/models")`).

## Virtual environment and run script

- The virtual environment lives in `.venv/`. Do not create it by hand - give every runnable project a
  `run.sh` at the repository root that builds it on first run, installs dependencies and starts the
  entry point. It works on Linux, macOS and Windows (Git Bash):

  ```bash
  #!/usr/bin/env bash
  # Create the virtual environment if needed, install dependencies and start the app.
  set -euo pipefail

  cd "$(dirname "$0")"

  VENV_DIR="${VENV_DIR:-.venv}"
  PYTHON="${PYTHON:-python3}"
  command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python

  if [ ! -d "$VENV_DIR" ]; then
      echo "Creating virtual environment in $VENV_DIR"
      "$PYTHON" -m venv "$VENV_DIR"
  fi

  # Linux/macOS use bin/, Windows (Git Bash) uses Scripts/
  if [ -x "$VENV_DIR/bin/python" ]; then
      VENV_PYTHON="$VENV_DIR/bin/python"
  else
      VENV_PYTHON="$VENV_DIR/Scripts/python"
  fi

  "$VENV_PYTHON" -m pip install -q --upgrade pip
  "$VENV_PYTHON" -m pip install -q -r requirements.txt

  exec "$VENV_PYTHON" app.py "$@"
  ```

- Change only the last line to suit the project: the entry point (`app.py`, `run.py`, `main.py`), or
  `-m package` for an installable package (install it with `pip install -q -e .` in place of the
  `requirements.txt` line). Keep the rest as is.
- Call the venv's interpreter directly (`$VENV_PYTHON -m pip`, `$VENV_PYTHON app.py`) - never rely on
  `activate` or on whichever `python`/`pip` is first on `PATH`.
- Commit it executable with LF line endings (`git update-index --chmod=+x run.sh` on Windows).
- Use the same `.venv/bin/python` / `.venv/Scripts/python` interpreter for any other commands you
  run in the project (tests, linters, one-off scripts).

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
