# Security, auth and sessions

## Google OAuth

Copy `assets/template/app/auth/` and `templates/login.html` into the project — do not rewrite them.
Update `app.*` imports to the project's package name.

| Route | Purpose |
|-------|---------|
| `GET /auth/login` | Renders `login.html`; redirects home if already signed in |
| `GET /auth/google` | Starts the Google OAuth redirect (or the test callback when `TEST_USER` is set) |
| `GET /auth/callback` | Handles the Google callback and establishes the session |
| `GET /auth/logout` | Clears the session and redirects home |

Protect routes with `@login_required` from `auth/decorators.py`.

### `TEST_USER` bypass

Set `TEST_USER=<name>` in `.env_dev` to skip Google during development. `/auth/google` redirects to
`/auth/test-callback`, which signs in with the fake Google ID `test:<name>`. When `TEST_USER` is unset
the test route redirects to login and the code path is inert.

## OAuth redirect URI behind a proxy

Flask runs behind Nginx (and usually Cloudflare), so `url_for(..., _external=True)` alone produces
`http://` URLs and builds the host from the client-supplied `Host` header — a Host-header-injection
risk that lets an attacker steer the OAuth redirect to their own domain.

- Do not use a `BASE_URL` setting — it hardcodes the domain.
- Do not rely on `ProxyFix` alone.
- Use `get_oauth_redirect_uri()` from `auth/service.py`, which:
  1. Picks the scheme from Cloudflare's `CF-Visitor` header, then `FORCE_HTTPS`, then Flask's own.
  2. Uses `request.host` only if it is in the `APP_HOSTNAME` allow-list, otherwise the first entry.

Set `APP_HOSTNAME` for every deployed app, comma-separated when several hostnames are valid
(e.g. `APP_HOSTNAME=bouts.co.za,www.bouts.co.za`).

## Client IP

Never use `request.remote_addr` directly — it is the proxy's address. Never trust
`X-Forwarded-For` — it is client-controlled.

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
| General | Persistent — `session.permanent = True`, 30-day `PERMANENT_SESSION_LIFETIME` |
| Sensitive (credentials, secrets, security configuration) | Non-persistent — do **not** set `session.permanent` |

`SESSION_COOKIE_SECURE` is derived from `FLASK_DEBUG` — `True` in production, `False` in local dev:

```python
SESSION_COOKIE_SECURE = os.environ.get('FLASK_DEBUG', 'False').lower() != 'true'
```

## CSRF

`flask-wtf` provides global CSRF protection, wired in the app factory with `csrf.init_app(app)`.

- Every POST form: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- AJAX: send the header `X-CSRFToken`.
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

- A strict CSP silently breaks Bootstrap and inline scripts — whitelist every third-party origin in the
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
