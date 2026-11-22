---
name: flask
description: Conventions, golden template and deployment contract for Flask web apps - app factory and blueprints, Jinja2 + Bootstrap 5 templates, SQL held in Jinja .sql templates for SQLite and Postgres, emailed-code sign-in (Mailgun) with passkeys, optional Google OAuth and a user admin screen, security headers, and the flask-deploy (Gunicorn + Nginx + systemd) contract. Use whenever creating, modifying, reviewing or deploying a Flask app - adding routes, blueprints, templates, SQL queries, auth, or touching run.py, config.py, requirements.txt, .env files or the GitHub Actions deploy workflow in a Flask project - even if the user doesn't say "Flask" explicitly.
---

# Flask development

Every Flask app in this portfolio follows one pattern so that it deploys with
[flask-deploy](https://github.com/massyn/flask-deploy) and behaves consistently behind Nginx + Cloudflare.
General Python conventions (typing, logging, formatting, testing) come from the `python` skill - apply
both. For an installable, phone-first app, the `flask-pwa` skill adds the PWA layer on top of this one.

## Starting point

- **New app:** copy `assets/template/` (the golden template) into the new repo, rename the `app/`
  package to the project name, and update the `from app...` imports to match. Do not rewrite auth,
  `db.py` or `config.py` from scratch.
- **Existing app:** follow the rules below; consult the reference files for detail before adding a
  feature that one of them covers.
- **Existing app adopting the emailed-code auth:** its `users` table must be migrated (new columns, unique
  lower-case email, possibly a full table rebuild on SQLite). Read "Moving an existing app to emailed
  codes" in `references/security.md`, inspect the app's own schema, and get the user's yes before touching
  a live database.

## Hard rules

### Structure

- Root holds only `run.py`, `config.py`, `requirements.txt`, `.env*` files, `templates/` and `static/`.
  App code lives in a package named after the project, built by a `create_app()` factory.
- `run.py` exposes a module-level `app` (Gunicorn runs `run:app`) and loads dotenv **before** importing
  config. It contains wiring only.
- `requirements.txt` must list `gunicorn`.
- One blueprint per feature area, registered in the app factory.
- `DATABASE_URL` has no default - `config.py` raises `RuntimeError` if it is missing.
- All configuration comes from env vars via `config.py`; nothing hardcoded in business logic.

### Routes and templates

- Use Jinja2 templates for all HTML - never construct HTML strings in Python or use
  `render_template_string` with raw markup.
- Use Bootstrap 5 for all styling, loaded via CDN unless the project specifies otherwise.
- Template inheritance: `base.html` defines layout and navigation; all page templates extend it.
- Route handlers are thin: validate input, call service functions, return `render_template()`.
  No business logic in routes.
- Use `url_for()` for all internal links and static asset references - never hardcode paths.
- Flash messages via `flask.flash()`, rendered in `base.html`; never return HTML strings from routes.
- Static files in `static/`; templates in `templates/`. Group templates by blueprint or feature if the
  app is large.
- Templates are for presentation only - no conditionals that encode business rules, no data
  transformation.

### SQL

- Never embed SQL in Python - all queries live in `templates/sql/` as Jinja `.sql` files, rendered at
  runtime via `db.py`.
- Target both SQLite (`sqlite3`) and Postgres (`psycopg3`).
- Pass `dialect` (`"sqlite"` or `"postgres"`) into every SQL template; use
  `{% if dialect == 'postgres' %}` blocks for dialect-specific syntax (`RETURNING`, `ILIKE`, casts,
  `ON CONFLICT`).
- Placeholders: `?` for SQLite, `%s` for psycopg3 - emitted by the template.
- Name files by operation (`user_insert.sql`, `order_list.sql`); one file per logical query, never
  multiple statements in one template.
- Never use f-strings or string formatting to inject values; always use parameterised queries.

### Security

- Never trust `request.remote_addr` or `X-Forwarded-For` for the client IP - use `get_remote_ip()`.
- Never build OAuth redirect URIs from the raw `Host` header - use `get_oauth_redirect_uri()` with the
  `APP_HOSTNAME` allow-list.
- Sign-in is an emailed one-time code by default (Mailgun), never a clickable link, with passkeys beside
  it. Google is optional, not the way: its button shows only when `GOOGLE_CLIENT_ID` is set. Email,
  lower-cased, is the identity every method resolves to. Never hand-roll the code or WebAuthn checks.
- Passkeys come with the template (`app/auth/passkeys.py`) - never hand-roll WebAuthn verification.
  Every sign-in method finishes with `establish_session(user, method)` and redirects to `after_login_url()`.
- `ADMIN_USER` is the breakglass admin: always admin, no `users` row. `TEST_USER` is a dev-only email that
  skips the code and never goes in a deploy workflow.
- CSRF protection (`flask-wtf`) on every app; every POST form carries `csrf_token`.
- Security headers via Flask-Talisman, with every CDN origin whitelisted in the CSP.
- Never delete on GET - destructive actions POST to a dedicated route after a Bootstrap modal confirm.

## Reference files

Read the relevant file before working in that area:

| File | Read when |
|------|-----------|
| `references/deploy.md` | Touching `run.py`, `.env*`, `requirements.txt`, `.gitignore`, the GitHub Actions workflow, or deploying a new site |
| `references/security.md` | Auth (emailed codes, roles, admin, `ADMIN_USER`/`TEST_USER`), sessions, Google OAuth, passkeys, client IP, CSRF, Talisman/CSP, rate limiting |
| `references/ui.md` | Templates, navbar, theming/CSS, list views, pagination, sorting, footer, analytics tag |
| `references/sql.md` | Adding queries or schema, or working with `db.py` |

## Golden template contents (`assets/template/`)

| Path | Purpose |
|------|---------|
| `run.py` | Entry point - dotenv loading, `app = create_app()`, dev server block |
| `config.py` | `Config` class; every value from env vars |
| `app/__init__.py` | App factory - CSRF, rate limiter, OAuth, blueprints, error handlers, context processor |
| `app/db.py` | Connection handling (SQLite / Postgres), SQL template rendering, `execute_batch`, `SCHEMA_FILES` |
| `app/main.py` | Public routes blueprint |
| `app/auth/` | Auth blueprint: emailed codes (`otp.py`, `otp_routes.py`, `mailgun.py`), optional Google, `sign_in_user`, `get_remote_ip`, `get_oauth_redirect_uri`, `login_required`, `admin_required` |
| `app/admin/` | User admin screens: list, add, edit (role, disable, delete), last login |
| `tests/conftest.py`, `tests/test_auth.py`, `tests/test_passkeys.py` | pytest checks for codes, `ADMIN_USER`, `TEST_USER`, disabled users, the admin screens and the passkey ceremonies (software authenticator) |
| `app/auth/passkeys.py`, `passkey_routes.py` | Passkey (WebAuthn) sign-up, sign-in and management |
| `templates/` | `base.html`, page templates (incl. `passkey_signup.html`, `passkeys.html`), `sql/` query templates |
| `static/js/csrf.js` | `postJSON()` - page scripts POST JSON with the CSRF token from the `csrf-token` meta tag |
| `static/js/passkeys.js` | Drives `data-passkey="login"` / `data-passkey="register"` buttons |
| `static/theme.css` | Colour variables - the single source of truth for the palette |
| `.env.example` | Documents every environment variable |
| `.gitattributes` | Stores and checks out every text file with LF endings (see the `devops` skill) |
| `.editorconfig` | Editor settings - LF, UTF-8, final newline, 4-space indent |
