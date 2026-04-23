## General
- Clarify ambiguities before starting — do not assume scope.
- Use British English spelling for all communication, comments, and code.
- NEVER perform a git commit or a git push.
- When completing tasks from a dev plan checklist, check off tasks as you complete them.

## Project Structure
- Group code by functional concern, not by type. 
- A file should have one clear reason to exist — if you can't describe its purpose in a sentence, it needs splitting.
- Entry points (app.py, main.py, cli.py) are wiring only — no business logic.
- Do not grow a single file to accommodate new concerns. Create a new file instead.
- If you're unsure where something belongs, ask before placing it.

## Code Quality
- Implement actual functionality — no mock, placeholder, or stub code.
- Prefer simple, concise solutions. Avoid abstractions and over-engineering unless complexity genuinely warrants them.
- If a file exceeds 400 lines, treat it as a signal to reconsider structure — not a hard limit to write up to.
- Handle errors explicitly. Prefer returning errors or raising specific exceptions over silent failures or bare excepts.
- Variables should have sensible defaults but be parameterised and available as configuration options where appropriate.
- Find root causes. No temporary fixes. Senior developer standards.
- For non-trivial changes, pause and ask "is there a more elegant way?" — skip this for simple, obvious fixes.
- If a solution feels hacky, step back and implement the elegant one instead.

## Python
- Target Python 3.10+ unless the project specifies otherwise.
- Prefer stdlib over third-party libraries unless there is a clear, justified reason.
- Use type hints on all function signatures.
- Format with `black`, lint with `ruff`. If a `Makefile` is present with `lint`, `format`, `test`, or `build` targets, run them after completing your task and confirm they pass — do not proceed if they fail.
- Write tests for non-trivial logic. Use `pytest`. Do not write tests that trivially pass without asserting meaningful behaviour.

## Tools
- Prioritise using available tools over manual approaches whenever appropriate.
- Use `-q` (quiet) flags where available for package installation and similar commands. Only surface output if the command exits with an error.

## Communication
- Be concise in explanations. Do not narrate every step — summarise what you did and flag anything unexpected.
- Do not re-read files you have already read in this session unless the content may have changed.
- When given a bug report, just fix it — diagnose from logs and errors without asking for hand-holding.
