import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.db import execute, query

# Access tokens do not expire; clients still receive refresh tokens so they can rotate.
_NEVER = '2099-01-01T00:00:00+00:00'


def _now() -> datetime:
    return datetime.now(timezone.utc)


def generate_auth_code(
    user_id: int,
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str,
) -> str:
    code = secrets.token_urlsafe(32)
    expires_at = (_now() + timedelta(minutes=10)).isoformat()
    execute(
        'mcp_auth_code_insert.sql',
        (code, user_id, client_id, redirect_uri, code_challenge, code_challenge_method, expires_at),
    )
    return code


def consume_auth_code(
    code: str,
    client_id: str,
    redirect_uri: str,
    code_verifier: str,
) -> dict | None:
    """Return the auth code row if the exchange is valid, deleting the code so it is single-use."""
    rows = query('mcp_auth_code_get.sql', (code,))
    if not rows:
        return None
    row = rows[0]

    if _now() > datetime.fromisoformat(row['expires_at']):
        execute('mcp_auth_code_delete.sql', (code,))
        return None

    if row['client_id'] != client_id or row['redirect_uri'] != redirect_uri:
        return None

    if row['code_challenge']:
        if row['code_challenge_method'] == 'S256':
            digest = hashlib.sha256(code_verifier.encode()).digest()
            challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
            if not secrets.compare_digest(challenge, row['code_challenge']):
                return None
        elif not secrets.compare_digest(code_verifier, row['code_challenge']):
            return None

    execute('mcp_auth_code_delete.sql', (code,))
    return row


def issue_tokens(user_id: int, client_id: str) -> tuple[str, str]:
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    execute('mcp_token_insert.sql', (access_token, refresh_token, user_id, client_id, _NEVER))
    return access_token, refresh_token


def issue_pat(user_id: int) -> str:
    """Replace the user's personal access token. PATs have no refresh token."""
    execute('mcp_pat_delete.sql', (user_id,))
    token = secrets.token_urlsafe(32)
    execute('mcp_token_insert.sql', (token, None, user_id, 'pat', _NEVER))
    return token


def validate_token(access_token: str) -> dict | None:
    rows = query('mcp_token_get.sql', (access_token,))
    if not rows:
        return None
    row = rows[0]
    if _now() > datetime.fromisoformat(row['expires_at']):
        return None
    execute('mcp_token_touch.sql', (_now().isoformat(), access_token))
    return row


def refresh_tokens(refresh_token: str) -> tuple[str, str] | None:
    """Rotate: the old access/refresh pair is deleted and a new pair issued."""
    rows = query('mcp_token_by_refresh.sql', (refresh_token,))
    if not rows:
        return None
    row = rows[0]
    execute('mcp_token_delete_by_refresh.sql', (refresh_token,))
    return issue_tokens(row['user_id'], row['client_id'])
