## General
- If ambiguity is minor and reversible, proceed with a sensible assumption and state it.
- Use British English spelling for all communication, comments, and code.
- NEVER perform a git commit or a git push.
- When completing tasks from a dev plan checklist, check off tasks as you complete them.

## Project Structure
- Group code by functional concern, not by type.
- A file should have one clear reason to exist — if you can't describe its purpose in a sentence, it needs splitting.
- Don't extract helper functions unless they are reused or genuinely simplify a complex body of logic. An inner function or inline expression is preferable to a private module-level function used in only one place.
- Entry points (app.py, main.py, cli.py) are wiring only — no business logic.
- Do not grow a single file to accommodate new concerns. Create a new file instead.
- Configuration must be externalised (env/config files), not hardcoded in business logic.
- Log meaningful events and errors at appropriate levels; avoid print debugging.

## Code Quality
- Implement actual functionality — no mock, placeholder, or stub code.
- Prefer simple, concise solutions. Favour designs that are easy to extend without major refactoring.
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

## Flask
- Use Jinja2 templates for all HTML — never construct HTML strings in Python or use `render_template_string` with raw markup.
- Use Bootstrap 5 for all styling; load via CDN unless the project specifies otherwise.
- Template inheritance: define a `base.html` with layout and navigation; all page templates extend it.
- Route handlers are thin: validate input, call service functions, return `render_template()`. No business logic in routes.
- Use `url_for()` for all internal links and static asset references — never hardcode paths.
- Flash messages via `flask.flash()` rendered in templates; do not return HTML strings from route handlers.
- Static files in `static/`; templates in `templates/`. Group templates by blueprint or feature if the app is large.
- Templates are for presentation only — no conditionals that encode business rules, no data transformation.

## SQL
- Never embed SQL in Python — all queries live in `.sql` Jinja template files, loaded and rendered at runtime.
- Target both SQLite and Postgres. Use `psycopg3` for Postgres; `sqlite3` (stdlib) for SQLite.
- Pass `dialect` (e.g. `"sqlite"` or `"postgres"`) into every SQL template so conditional blocks can handle differences.
- Use Jinja `{% if dialect == 'postgres' %}` blocks for dialect-specific syntax (e.g. `RETURNING`, `ILIKE`, type casts, `ON CONFLICT`).
- Parameter placeholders differ by driver — use `?` for SQLite and `%s` for psycopg3; emit the correct one via the template.
- Store SQL templates under `templates/sql/`, named by operation (e.g. `user_insert.sql`, `order_list.sql`).
- One file per logical query or operation — do not concatenate multiple statements in one template.
- Never use string formatting or f-strings to inject values into SQL; always use parameterised queries.

## Tools
- Prioritise using available tools over manual approaches whenever appropriate.
- Use `-q` (quiet) flags where available for package installation and similar commands. Only surface output if the command exits with an error.

## Communication
- Be concise in explanations. Do not narrate every step — summarise what you did and flag anything unexpected.
- Do not re-read files you have already read in this session unless the content may have changed.
- When given a bug report, just fix it — diagnose from logs and errors without asking for hand-holding.

Where appropriate, use the citadel MCP to manage knowledge across projects.

