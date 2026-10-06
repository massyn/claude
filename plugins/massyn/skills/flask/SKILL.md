---
name: flask
description: Conventions, golden template and deployment contract for Flask web apps — app factory and blueprints, Jinja2 + Bootstrap 5 templates, SQL held in Jinja .sql templates for SQLite and Postgres, Google OAuth, security headers, and the flask-deploy (Gunicorn + Nginx + systemd) contract. Use whenever creating, modifying, reviewing or deploying a Flask app — adding routes, blueprints, templates, SQL queries, auth, or touching run.py, config.py, requirements.txt, .env files or the GitHub Actions deploy workflow in a Flask project — even if the user doesn't say "Flask" explicitly.
---

# Flask development

Every Flask app in this portfolio follows one pattern so that it deploys with
[flask-deploy](https://github.com/massyn/flask-deploy) and behaves consistently behind Nginx + Cloudflare.
General Python conventions (typing, logging, formatting, testing) come from the `python` skill — apply
both. For an installable, phone-first app, the `flask-pwa` skill adds the PWA layer on top of this one.

## Starting point

- **New app:** copy `assets/template/` (the golden template) into the new repo, rename the `app/`
  package to the project name, and update the `from app...` imports to match. Do not rewrite auth,
  `db.py` or `config.py` from scratch.
- **Existing app:** follow the rules below; consult the reference files for detail before adding a
  feature that one of them covers.

## Hard rules

### Structure

- Root holds only `run.py`, `config.py`, `requirements.txt`, `.env*` files, `templates/` and `static/`.
  App code lives in a package named after the project, built by a `create_app()` factory.
- `run.py` exposes a module-level `app` (Gunicorn runs `run:app`) and loads dotenv **before** importing
  config. It contains wiring only.
- `requirements.txt` must list `gunicorn`.
- One blueprint per feature area, registered in the app factory.
- `DATABASE_URL` has no default — `config.py` raises `RuntimeError` if it is missing.
- All configuration comes from env vars via `config.py`; nothing hardcoded in business logic.

### Routes and templates

- Use Jinja2 templates for all HTML — never construct HTML strings in Python or use
  `render_template_string` with raw markup.
- Use Bootstrap 5 for all styling, loaded via CDN unless the project specifies otherwise.
- Template inheritance: `base.html` defines layout and navigation; all page templates extend it.
- Route handlers are thin: validate input, call service functions, return `render_template()`.
  No business logic in routes.
- Use `url_for()` for all internal links and static asset references — never hardcode paths.
- Flash messages via `flask.flash()`, rendered in `base.html`; never return HTML strings from routes.
- Static files in `static/`; templates in `templates/`. Group templates by blueprint or feature if the
  app is large.
- Templates are for presentation only — no conditionals that encode business rules, no data
  transformation.

### SQL

- Never embed SQL in Python — all queries live in `templates/sql/` as Jinja `.sql` files, rendered at
  runtime via `db.py`.
- Target both SQLite (`sqlite3`) and Postgres (`psycopg3`).
- Pass `dialect` (`"sqlite"` or `"postgres"`) into every SQL template; use
  `{% if dialect == 'postgres' %}` blocks for dialect-specific syntax (`RETURNING`, `ILIKE`, casts,
  `ON CONFLICT`).
- Placeholders: `?` for SQLite, `%s` for psycopg3 — emitted by the template.
- Name files by operation (`user_insert.sql`, `order_list.sql`); one file per logical query, never
  multiple statements in one template.
- Never use f-strings or string formatting to inject values; always use parameterised queries.

### Security

- Never trust `request.remote_addr` or `X-Forwarded-For` for the client IP — use `get_remote_ip()`.
- Never build OAuth redirect URIs from the raw `Host` header — use `get_oauth_redirect_uri()` with the
  `APP_HOSTNAME` allow-list.
- CSRF protection (`flask-wtf`) on every app; every POST form carries `csrf_token`.
- Security headers via Flask-Talisman, with every CDN origin whitelisted in the CSP.
- Never delete on GET — destructive actions POST to a dedicated route after a Bootstrap modal confirm.

## Reference files

Read the relevant file before working in that area:

| File | Read when |
|------|-----------|
| `references/deploy.md` | Touching `run.py`, `.env*`, `requirements.txt`, `.gitignore`, the GitHub Actions workflow, or deploying a new site |
| `references/security.md` | Auth, sessions, OAuth, client IP, CSRF, Talisman/CSP, rate limiting |
| `references/ui.md` | Templates, navbar, theming/CSS, list views, pagination, sorting, footer, analytics tag |
| `references/sql.md` | Adding queries or schema, or working with `db.py` |

## Golden template contents (`assets/template/`)

| Path | Purpose |
|------|---------|
| `run.py` | Entry point — dotenv loading, `app = create_app()`, dev server block |
| `config.py` | `Config` class; every value from env vars |
| `app/__init__.py` | App factory — CSRF, rate limiter, OAuth, blueprints, error handlers, context processor |
| `app/db.py` | Connection handling (SQLite / Postgres) and SQL template rendering |
| `app/main.py` | Public routes blueprint |
| `app/auth/` | Google OAuth blueprint, `find_or_create_user`, `get_remote_ip`, `get_oauth_redirect_uri`, `login_required` |
| `templates/` | `base.html`, page templates, `sql/` query templates |
| `static/theme.css` | Colour variables — the single source of truth for the palette |
| `.env.example` | Documents every environment variable |
