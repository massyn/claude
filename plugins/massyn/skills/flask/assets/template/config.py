import os
from datetime import timedelta

_database_url = os.environ.get('DATABASE_URL', '')
if not _database_url:
    raise RuntimeError(
        'DATABASE_URL is required - set it in your .env file. No default is provided.'
    )


def _email(name: str) -> str:
    """An email address from the environment, always trimmed and lower case."""
    return os.environ.get(name, '').strip().lower()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-please-change')
    DATABASE_URL = _database_url

    # Email one-time codes are the default sign-in. Mailgun delivers them; with these unset the
    # login page says email sign-in is not configured.
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', '')
    MAILGUN_FROM = os.environ.get('MAILGUN_FROM', '')
    # https://api.eu.mailgun.net for EU-region accounts.
    MAILGUN_BASE_URL = os.environ.get('MAILGUN_BASE_URL', 'https://api.mailgun.net')
    OTP_TTL_SECONDS = int(os.environ.get('OTP_TTL_SECONDS', '600'))
    OTP_MAX_ATTEMPTS = int(os.environ.get('OTP_MAX_ATTEMPTS', '5'))
    # False: only people already in the users table (and ADMIN_USER) can sign in.
    ALLOW_SIGNUP = os.environ.get('ALLOW_SIGNUP', 'false').lower() == 'true'
    # True: a visitor can create an account with a passkey alone (no email, no admin). Off by default;
    # users an admin has added can still add a passkey once signed in.
    PASSKEY_SIGNUP = os.environ.get('PASSKEY_SIGNUP', 'false').lower() == 'true'
    # Breakglass: this email is always admin and may sign in without a users row.
    ADMIN_USER = _email('ADMIN_USER')
    # Dev only: this email signs in without a code. Never set it in production.
    TEST_USER = _email('TEST_USER')

    # Google sign-in is optional: the button appears only when GOOGLE_CLIENT_ID is set.
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'false').lower() == 'true'
    APP_HOSTNAMES = [
        h.strip() for h in os.environ.get('APP_HOSTNAME', '').split(',') if h.strip()
    ]
    # Passkeys belong to this domain (it also covers its subdomains, such as www). Unset, the first
    # APP_HOSTNAME is used, or in development the host the page was loaded from.
    PASSKEY_RP_ID = os.environ.get('PASSKEY_RP_ID', '')
    PASSKEY_RP_NAME = os.environ.get('PASSKEY_RP_NAME', 'Flask App')
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_DEBUG', 'False').lower() != 'true'
    VERSION = os.environ.get('VERSION', '')
    GTAG_ID = os.environ.get('GTAG_ID', '')
