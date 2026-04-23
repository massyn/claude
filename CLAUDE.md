## General
- Clarify ambiguities before starting — do not assume scope.
- Use British English spelling for all communication, comments, and code.
- NEVER perform a git commit or a git push.
- When completing tasks from a dev plan checklist, check off tasks as you complete them.

## Code Quality
- Implement actual functionality — no mock, placeholder, or stub code.
- Prefer simple, concise solutions. Avoid abstractions and over-engineering unless complexity genuinely warrants them.
- Ensure files do not exceed 800 lines — split into smaller modules if needed.
- Handle errors explicitly. Prefer returning errors or raising specific exceptions over silent failures or bare excepts.
- Variables should have sensible defaults but be parameterised and available as configuration options where appropriate.

## Python
- Target Python 3.10+ unless the project specifies otherwise.
- Prefer stdlib over third-party libraries unless there is a clear, justified reason.
- Use type hints on all function signatures.
- Format with `black`, lint with `ruff`. If a `Makefile` is present with `lint`, `format`, `test`, or `build` targets, run them after completing your task and confirm they pass — do not proceed if they fail.
- Write tests for non-trivial logic. Use `pytest`. Do not write tests that trivially pass without asserting meaningful behaviour.

## Tools
- Prioritise using available tools over manual approaches whenever appropriate.
- Use `-q` (quiet) flags where available for package installation and similar commands. Only surface output if the command exits with an error.
