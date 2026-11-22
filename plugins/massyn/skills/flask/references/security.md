# Security, auth and sessions

## Sign-in overview

Email is the identity. Every sign-in method (emailed code, passkey, optional Google) resolves to one
`users` row matched on the lower-cased email, so a person who signs in two ways is still one user.

| Method | Status | Notes |
|--------|--------|-------|
| Emailed one-time code | Default, always on | Needs Mailgun; see below |
| Passkeys | Always on | See the Passkeys section |
| Google OAuth | Optional | The button appears only when `GOOGLE_CLIENT_ID` is set |

Copy `assets/template/app/auth/`, `app/admin/` and the login templates into the project - do not
rewrite them. Update `app.*` imports to the project's package name.

| Route | Purpose |
|-------|---------|
| `GET /auth/login` | Email form, plus passkey (and Google) buttons; redirects home if already signed in |
| `POST /auth/login` | Emails a code, or signs in the `TEST_USER` email directly |
| `GET`/`POST /auth/code` | Enter the code |
| `POST /auth/code/resend` | A fresh code for the email already entered |
| `GET /auth/google`, `GET /auth/callback` | Optional Google sign-in (404 unless `GOOGLE_CLIENT_ID` is set) |
| `GET /auth/logout` | Clears the session and redirects home |

Protect routes with `@login_required`, and admin-only routes with `@admin_required`, both from
`auth/decorators.py`. They re-read the user on every request, so disabling or deleting a user ends
their session at once and a changed role applies at once.

Every sign-in method finishes the same way: `establish_session(user, method)` puts the user in
`session['user']` (`id`, `name`, `email`, `role`), records the sign-in on the row, and the route redirects
to `after_login_url()`. When sign-in must land somewhere other than home (e.g. the flask-mcp consent
page), change `after_login_url()`, never the individual routes.

## Emailed codes

`app/auth/otp.py` issues and checks six-digit codes; `app/auth/mailgun.py` sends them.

- **Mailgun.** `MAILGUN_API_KEY`, `MAILGUN_DOMAIN` and `MAILGUN_FROM` (plus `MAILGUN_BASE_URL` for EU
  accounts). When they are unset, the login page shows "Email sign-in isn't set up" and disables the form;
  nothing is sent. `mailgun.send` is the one function to replace to use another provider.
- **Short-lived and single use.** A code lasts `OTP_TTL_SECONDS` (600) and is deleted once used.
- **Brute-force limit.** Wrong guesses are counted per code and the code dies after `OTP_MAX_ATTEMPTS` (5).
  A new code resets that, so requests are rate-limited per email (5 an hour) and per IP (20 an hour).
- **Bound to the browser.** The code's request id lives in the requesting browser's session; the same
  digits typed elsewhere fail.
- **HMAC at rest.** Only `HMAC-SHA256(SECRET_KEY, request_id:code)` is stored. A plain hash of six digits
  could be reversed instantly, so rotating `SECRET_KEY` also voids outstanding codes.
- **No account enumeration.** Any valid-looking email reaches the "enter your code" page; an email that
  can't sign in just has no code behind it, and every failure shows the same message. Sending the email is
  slower than not sending it, so response timing can still hint at which emails exist: acceptable behind the
  rate limits, but keep it in mind for high-value apps.
- **No open sign-up by default.** Only people already in `users` (and `ADMIN_USER`) can sign in. Set
  `ALLOW_SIGNUP=true` to let any email that proves it owns its inbox create an account. A user an admin
  has added can add a passkey from the user dropdown once signed in, and use it instead of a code from then
  on. Creating an account with a passkey alone (`/auth/passkey/signup`, no email, no admin) is a separate
  opt-in: `PASSKEY_SIGNUP=true`, for apps that demand it. Off, the route is 404 and the login page hides the link.
- **Disabled users** get no code, are refused by every method, and lose any live session.

## Roles, `ADMIN_USER` and the admin screens

`users.role` is `user` or `admin`. Check it with `@admin_required`, not by reading the session in templates.

**`ADMIN_USER`** is the breakglass account. When a user signs in with this email (compared lower-case), they
are admin whatever their row says. It needs no row, and none is created: the session user has `id` of
`None`, so the account never appears in the user list, has no passkeys and cannot be disabled or deleted.
Because it signs in by emailed code like everyone else, a Mailgun outage locks it out too; keep a way to
reach the database for that case.

**Admin screens** (`app/admin/`, under `/admin/users`, admin only):

| Screen | Does |
|--------|------|
| List | Paginated and sortable; shows role, status, sign-in methods, last login and how, created. Rows open the edit screen |
| Add | Email, optional name, role. The person then signs in with an emailed code |
| Edit | Change name and role, disable or re-enable, see last login, method and passkeys. Delete is here, behind a modal confirm, and removes the user's passkeys with them |

You can't change your own role or status or delete yourself, and the `ADMIN_USER` row is always an
enabled admin; both are refused server-side as well as greyed out. Tables an app adds that reference
`users` need clearing in `delete_user`.

### `TEST_USER` bypass

`TEST_USER=<email>` in `.env_dev`: on the normal login form, entering that email signs in straight away
as that user (created if needed), with no code sent and no Mailgun needed. Any other email behaves as
usual. While it is set the login page shows a "TEST_USER active" warning so nobody forgets it; it never
refuses to start, so keep it out of production `.env` files and the deploy workflow.

## Passkeys

Passkeys (WebAuthn, via the `webauthn` package) sit beside the emailed code. Copy
`app/auth/passkeys.py`, `app/auth/passkey_routes.py`, `static/js/csrf.js`, `static/js/passkeys.js`,
`templates/passkey_signup.html`, `templates/passkeys.html` and the `passkey_*.sql` / `user_*.sql`
templates - do not rewrite the ceremonies. The routes register on the auth blueprint through the
import at the foot of `app/auth/__init__.py`.

| Route | Purpose |
|-------|---------|
| `GET /auth/passkey/signup` | Create an account with a passkey alone: name only, no email. 404 unless `PASSKEY_SIGNUP=true` |
| `POST /auth/passkey/register/options` | Creation options - for the signed-in user, or a new user named in the JSON body |
| `POST /auth/passkey/register` | Verifies and stores the passkey; creates and signs in a new user |
| `POST /auth/passkey/login/options` | Sign-in options with a fresh challenge |
| `POST /auth/passkey/login` | Verifies the signature and signs the user in |
| `GET /auth/passkeys` | Lists, adds and removes the user's passkeys (login required, linked from the user dropdown) |
| `POST /auth/passkey/<id>/delete` | Removes a passkey after a Bootstrap modal confirm |

Rules the implementation relies on:

- **Challenge in the session, used once.** Options store the challenge in the session; verification
  pops it, so a captured reply cannot be replayed.
- **Discoverable credentials** (`resident_key=REQUIRED`): sign-in needs no username.
- **Random user handle.** `users.passkey_handle` (`secrets.token_urlsafe(32)`, set when any user is
  created) is the WebAuthn user id on the device - never the database id. Sign-in checks the handle
  the device returns against the stored one.
- **Schema.** `users.google_id` and `users.email` are nullable; `users.passkey_handle` is `UNIQUE NOT NULL`. The
  `passkeys` table stores only `credential_id` and `public_key` (base64url), `sign_count`,
  `created_on`, `last_used`.
- **Atomic sign-up.** The new user and their first passkey go in one `execute_batch()` transaction.
- **No lock-out.** A user with neither an email nor a `google_id` cannot remove their last passkey.
- **Errors.** Expected failures raise `PasskeyError` with a message safe to show; the route returns it
  as `{"error": ...}` with status 400 and `passkeys.js` shows it in the `[data-passkey-status]` element.

### Relying party

- `PASSKEY_RP_ID` is the domain passkeys belong to; it also covers its subdomains. Unset, it is the
  first `APP_HOSTNAME` (or, with none, the host the page was loaded from). When `APP_HOSTNAME` lists
  `www.example.com` before `example.com`, set `PASSKEY_RP_ID=example.com`.
- Allowed origins are `https://<host>` for every `APP_HOSTNAME`. WebAuthn needs HTTPS, or
  `http://localhost` in development - not `127.0.0.1`.
- Changing `PASSKEY_RP_ID` after go-live orphans every existing passkey.
- `PASSKEY_RP_NAME` is the name shown when a passkey is created.

### Moving an existing app to emailed codes

**This is a schema migration, and it is the app's own Claude (its `CLAUDE.md` and session) that has to
plan it.** The skill can't do it blindly: every app's `users` table has drifted, and other tables may
reference it.

`CREATE TABLE IF NOT EXISTS` never alters an existing table, so copying the new files into a live app
does nothing to its `users` table and then fails at the first query that names a new column. Before
touching anything, the app's Claude should:

1. Read the app's current `users` schema and every table or query that references it (foreign keys,
   `google_id` lookups, `find_or_create_user` callers, anything keyed on `session['user']`).
2. Work out the gap: `role TEXT NOT NULL DEFAULT 'user'`, `disabled INTEGER NOT NULL DEFAULT 0`,
   `last_login`, `last_method`, a nullable `google_id`, and `email` stored lower case and unique
   (resolve duplicates and blank emails first). The `otp_codes` table is new, so `init_db` creates it.
3. Choose the mechanism. Postgres can mostly `ALTER TABLE`. SQLite can add plain columns but not change
   constraints, so a nullable `google_id` or a unique `email` means **recreating the table**: create the
   new table, copy the rows, drop the old one, rename, with `PRAGMA foreign_keys=OFF` and a backup first.
   If the app's table has diverged far enough, recreating it is the honest answer for either engine.
4. Put the plan in front of the user and **get a yes before changing a live database**, then run it as
   an idempotent step in `init_db` so every environment converges.

Users who only ever signed in with Google have an email already, so they can sign in by code straight
away. Existing admins keep working if `ADMIN_USER` is set to one of them; promote others through the
admin screen rather than by editing roles by hand.

### Adding passkeys to an existing app

A passkey page that posts JSON needs `<meta name="csrf-token" content="{{ csrf_token() }}">` in the base
layout (and on a standalone login page), because `static/js/csrf.js` reads the token from it. An app whose
auth blueprint sits outside a global login gate (CCM's does) needs `@account_required` on the passkey
routes that act for a signed-in user.

`users.passkey_handle` doesn't have to be `NOT NULL`. CCM adds it as a nullable column, makes it unique
with `CREATE UNIQUE INDEX`, and fills it on a user's first passkey, so an existing database needs only an
added column and an index, not a table rebuild. Apps built from an older template have `google_id NOT NULL`
and no `passkey_handle`. Migrate at
startup in `init_db` before copying the files: SQLite needs a `users` table rebuild (new table, copy
rows, drop, rename, with `PRAGMA foreign_keys=OFF`), giving each existing user a random
`passkey_handle`; Postgres can `ALTER COLUMN google_id DROP NOT NULL` and add the column. Ask before
changing the schema of a live app.

### Testing

Test the ceremonies with a software authenticator rather than mocking `webauthn`: generate a P-256
key per passkey, answer creation options with "none" attestation and sign
`authenticatorData + sha256(clientDataJSON)` for sign-in, using origin `http://localhost`
(Kickstand's `tests/soft_authenticator.py` is a working example). Cover sign-up, sign-in, replay
refusal, an unknown passkey, adding a passkey to a user who signs in by email, and the last-passkey lock-out.

The template's `tests/test_auth.py` covers the emailed code (expiry, reuse, the attempt limit, browser
binding, enumeration), `ADMIN_USER`, `TEST_USER`, disabled users and the admin screens, against SQLite
with a fake Mailgun. `tests/test_passkeys.py` runs the real passkey ceremonies with a software
authenticator (sign-in, replay, an unknown passkey, a disabled user, opt-in sign-up and the last-passkey
lock-out). Neither runs against Postgres.

## OAuth redirect URI behind a proxy

Flask runs behind Nginx (and usually Cloudflare), so `url_for(..., _external=True)` alone produces
`http://` URLs and builds the host from the client-supplied `Host` header - a Host-header-injection
risk that lets an attacker steer the OAuth redirect to their own domain.

- Do not use a `BASE_URL` setting - it hardcodes the domain.
- Do not rely on `ProxyFix` alone.
- Use `get_oauth_redirect_uri()` from `auth/service.py`, which:
  1. Picks the scheme from Cloudflare's `CF-Visitor` header, then `FORCE_HTTPS`, then Flask's own.
  2. Uses `request.host` only if it is in the `APP_HOSTNAME` allow-list, otherwise the first entry.

Set `APP_HOSTNAME` for every deployed app, comma-separated when several hostnames are valid
(e.g. `APP_HOSTNAME=bouts.co.za,www.bouts.co.za`).

## Client IP

Never use `request.remote_addr` directly - it is the proxy's address. Never trust
`X-Forwarded-For` - it is client-controlled.

```python
def get_remote_ip() -> str:
    return (
        request.headers.get('CF-Connecting-IP')
        or request.headers.get('X-Real-IP')
        or request.remote_addr
        or ''
    )
```

Use the same function as the key for anything per-client, including the rate limiter's `key_func`.

## Sessions

| App type | Policy |
|----------|--------|
| General | Persistent - `session.permanent = True`, 30-day `PERMANENT_SESSION_LIFETIME` |
| Sensitive (credentials, secrets, security configuration) | Non-persistent - do **not** set `session.permanent` |

`SESSION_COOKIE_SECURE` is derived from `FLASK_DEBUG` - `True` in production, `False` in local dev:

```python
SESSION_COOKIE_SECURE = os.environ.get('FLASK_DEBUG', 'False').lower() != 'true'
```

## CSRF

`flask-wtf` provides global CSRF protection, wired in the app factory with `csrf.init_app(app)`.

- Every POST form: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- Page scripts that POST: use `postJSON(url, body)` from `static/js/csrf.js`, which sends the token
  from the `<meta name="csrf-token">` tag in `base.html` as the `X-CSRFToken` header and resolves to
  `{ ok, status, data }`.
- Exempt only genuine machine endpoints (e.g. webhooks) with `@csrf.exempt`.

## Security headers (Flask-Talisman)

Add `flask-talisman` to `requirements.txt` and initialise it in the app factory after CSRF and OAuth.
Tie `force_https` and HSTS to `FORCE_HTTPS` so local dev is not forced onto HTTPS.

```python
from flask_talisman import Talisman

csp = {
    'default-src': ["'self'"],
    'style-src': ["'self'", 'https://cdn.jsdelivr.net'],
    'script-src': ["'self'", 'https://cdn.jsdelivr.net'],
    'connect-src': ["'self'", 'https://cdn.jsdelivr.net'],  # CDN source maps
    'font-src': ["'self'", 'data:', 'https://cdn.jsdelivr.net'],
    'img-src': ["'self'", 'data:', 'https://lh3.googleusercontent.com'],  # Google profile pictures
    'frame-ancestors': ["'none'"],
}

Talisman(
    app,
    force_https=app.config['FORCE_HTTPS'],
    strict_transport_security=app.config['FORCE_HTTPS'],
    frame_options='DENY',
    content_security_policy=csp,
)
```

- A strict CSP silently breaks Bootstrap and inline scripts - whitelist every third-party origin in the
  directive it is used for.
- Prefer moving inline `<script>`/`<style>` into static files. If an inline block is unavoidable, relax
  CSP on that route only with the `@talisman(content_security_policy=...)` decorator rather than adding
  `'unsafe-inline'` globally.
- Google tag (`GTAG_ID`) needs `https://www.googletagmanager.com` in `script-src`, plus
  `https://www.googletagmanager.com` and `https://www.google-analytics.com` in `connect-src`, and
  `'unsafe-inline'` (or a nonce) for its init block.
- Cloudflare Web Analytics needs `https://static.cloudflareinsights.com` in `script-src`.

## Rate limiting

The template wires `Flask-Limiter` with in-memory storage and default limits of 200/day and 50/hour,
and renders `error.html` for HTTP 429. Apply tighter limits to sensitive routes (login, form posts)
with `@limiter.limit(...)`.
