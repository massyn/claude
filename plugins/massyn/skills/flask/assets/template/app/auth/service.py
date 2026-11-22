import re
import secrets

from flask import request, url_for, current_app
from app.db import query, execute


def get_remote_ip() -> str:
    return (
        request.headers.get('CF-Connecting-IP')
        or request.headers.get('X-Real-IP')
        or request.remote_addr
        or ''
    )


def get_oauth_redirect_uri() -> str:
    cf_visitor = request.headers.get('CF-Visitor', '')
    is_https = '"scheme":"https"' in cf_visitor or current_app.config.get('FORCE_HTTPS')
    scheme = 'https' if is_https else request.scheme

    trusted_hostnames = current_app.config.get('APP_HOSTNAMES', [])
    if trusted_hostnames:
        # request.host is attacker-controllable via the Host header, so only use it
        # if it matches an entry in the trusted allow-list; otherwise fall back to
        # the first configured hostname.
        hostname = request.host if request.host in trusted_hostnames else trusted_hostnames[0]
        return f'{scheme}://{hostname}{url_for("auth.callback")}'

    # No trusted hostnames configured - falls back to request.host, which is
    # attacker-controllable via the Host header. Set APP_HOSTNAME in production.
    return url_for('auth.callback', _external=True, _scheme=scheme)


def normalise_email(email: str | None) -> str:
    """Emails are compared, stored and configured in lower case."""
    return (email or '').strip().lower()


EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
EMAIL_MAX_LENGTH = 254


def is_valid_email(email: str) -> bool:
    return len(email) <= EMAIL_MAX_LENGTH and bool(EMAIL_PATTERN.match(email))


def is_admin_email(email: str | None) -> bool:
    """True for the ADMIN_USER breakglass email, which is always an admin."""
    admin = current_app.config.get('ADMIN_USER', '')
    return bool(admin) and normalise_email(email) == admin


def breakglass_user(email: str) -> dict:
    """The ADMIN_USER account. It has no users row (id is None) so it never appears in the table."""
    return {'id': None, 'name': email, 'email': email, 'role': 'admin'}


def can_sign_in(email: str) -> bool:
    """Whether a verified email may sign in: a known user, the breakglass admin, or open sign-up."""
    if is_admin_email(email):
        return True
    rows = query('user_by_email.sql', (email,))
    if rows:
        return not rows[0]['disabled']
    return current_app.config.get('ALLOW_SIGNUP', False)


def sign_in_user(
    email: str, name: str = '', google_id: str | None = None, create: bool = False
) -> dict | None:
    """The user a verified email belongs to, or None when that email may not sign in.

    Email is the identity: a Google account is linked to the user who already has that email, so
    Google, codes and passkeys all reach the same row. `create` lets an unknown email become a new
    user. Call it only once the email has been proven (a code, or Google's verified email).
    """
    email = normalise_email(email)
    rows = query('user_by_google_id.sql', (google_id,)) if google_id else []
    rows = rows or query('user_by_email.sql', (email,))
    if rows:
        user = rows[0]
        if user['disabled'] and not is_admin_email(email):
            return None
        if google_id and not user['google_id']:
            execute('user_set_google_id.sql', (google_id, user['id']))
        return user
    if is_admin_email(email):
        return breakglass_user(email)
    if not create:
        return None
    execute('user_insert.sql', (google_id, name or email.split('@')[0], email, new_passkey_handle()))
    return query('user_by_email.sql', (email,))[0]


def new_passkey_handle() -> str:
    # The WebAuthn user handle: random, so the user's id is never stored on their devices.
    return secrets.token_urlsafe(32)
