# Security, auth and sessions

## Google OAuth

Copy `assets/template/app/auth/` and `templates/login.html` into the project - do not rewrite them.
Update `app.*` imports to the project's package name.

| Route | Purpose |
|-------|---------|
| `GET /auth/login` | Renders `login.html`; redirects home if already signed in |
| `GET /auth/google` | Starts the Google OAuth redirect (or the test callback when `TEST_USER` is set) |
| `GET /auth/callback` | Handles the Google callback and establishes the session |
| `GET /auth/logout` | Clears the session and redirects home |

Protect routes with `@login_required` from `auth/decorators.py`.

Every sign-in method (Google, `TEST_USER`, passkeys) finishes the same way: `establish_session(user)`
puts the user row in `session['user']`, and the route redirects to `after_login_url()`. When sign-in
must land somewhere other than home (e.g. the flask-mcp consent page), change `after_login_url()`,
never the individual routes.

### `TEST_USER` bypass

Set `TEST_USER=<name>` in `.env_dev` to skip Google during development. `/auth/google` redirects to
`/auth/test-callback`, which signs in with the fake Google ID `test:<name>`. When `TEST_USER` is unset
the test route redirects to login and the code path is inert.

## Passkeys

Passkeys (WebAuthn, via the `webauthn` package) sit beside Google sign-in. Copy
`app/auth/passkeys.py`, `app/auth/passkey_routes.py`, `static/js/csrf.js`, `static/js/passkeys.js`,
`templates/passkey_signup.html`, `templates/passkeys.html` and the `passkey_*.sql` / `user_*.sql`
templates - do not rewrite the ceremonies. The routes register on the auth blueprint through the
import at the foot of `app/auth/__init__.py`.

| Route | Purpose |
|-------|---------|
| `GET /auth/passkey/signup` | Create an account with a passkey alone: name only, no Google, no email |
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
- **Schema.** `users.google_id` is nullable; `users.passkey_handle` is `UNIQUE NOT NULL`. The
  `passkeys` table stores only `credential_id` and `public_key` (base64url), `sign_count`,
  `created_on`, `last_used`.
- **Atomic sign-up.** The new user and their first passkey go in one `execute_batch()` transaction.
- **No lock-out.** A user without `google_id` cannot remove their last passkey.
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

### Adding passkeys to an existing app

Apps built from an older template have `google_id NOT NULL` and no `passkey_handle`. Migrate at
startup in `init_db` before copying the files: SQLite needs a `users` table rebuild (new table, copy
rows, drop, rename, with `PRAGMA foreign_keys=OFF`), giving each existing user a random
`passkey_handle`; Postgres can `ALTER COLUMN google_id DROP NOT NULL` and add the column. Ask before
changing the schema of a live app.

### Testing

Test the ceremonies with a software authenticator rather than mocking `webauthn`: generate a P-256
key per passkey, answer creation options with "none" attestation and sign
`authenticatorData + sha256(clientDataJSON)` for sign-in, using origin `http://localhost`
(Kickstand's `tests/soft_authenticator.py` is a working example). Cover sign-up, sign-in, replay
refusal, an unknown passkey, adding a passkey to a Google user, and the last-passkey lock-out.

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
