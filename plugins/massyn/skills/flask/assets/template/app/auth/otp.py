"""Emailed one-time sign-in codes.

A code is six digits, valid for OTP_TTL_SECONDS, and tied to the browser that asked for it: the
request id lives in that browser's session, so the code is useless anywhere else. Only an HMAC of
the code is stored (a plain hash of six digits could be reversed instantly), wrong guesses are
counted per code, and a code dies after OTP_MAX_ATTEMPTS of them.

Asking for a code never reveals whether the email can sign in: an email that cannot gets the same
"enter your code" page, it just has no code behind it.
"""

import hashlib
import hmac
import logging
import re
import secrets
import time

from flask import current_app, session

from app.auth import mailgun
from app.auth.service import can_sign_in, normalise_email
from app.db import execute, query

log = logging.getLogger(__name__)

CODE_LENGTH = 6
INVALID_CODE = "That code isn't right or has expired. Please request a new one."


class OtpError(Exception):
    """A code was refused; the message is safe to show the user."""


def _digest(request_id: str, code: str) -> str:
    key = current_app.config['SECRET_KEY'].encode()
    return hmac.new(key, f'{request_id}:{code}'.encode(), hashlib.sha256).hexdigest()


def request_code(email: str) -> None:
    """Start a sign-in for `email`: email a fresh code, replacing any earlier one.

    Raises mailgun.MailError if the email could not be sent.
    """
    email = normalise_email(email)
    now = int(time.time())
    request_id = secrets.token_urlsafe(16)
    session['otp'] = {'request_id': request_id, 'email': email}

    execute('otp_purge_expired.sql', (now,))
    execute('otp_delete_by_email.sql', (email,))
    if not can_sign_in(email):
        log.info('Sign-in code requested for an email that may not sign in')
        return

    code = f'{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}'
    ttl = current_app.config['OTP_TTL_SECONDS']
    execute('otp_insert.sql', (request_id, email, _digest(request_id, code), now + ttl))
    mailgun.send(
        email,
        f'{code} is your sign-in code',
        f'Your sign-in code is {code}\n\n'
        f'It expires in {ttl // 60} minutes and works once. '
        "If you didn't ask for it, ignore this email: nobody can sign in without it.\n",
    )


def pending_email() -> str | None:
    """The email this browser is signing in as, once a code has been requested."""
    return (session.get('otp') or {}).get('email')


def verify_code(code: str) -> str:
    """Check the code entered in this browser and return the email it proves, or raise OtpError."""
    pending = session.get('otp')
    if not pending:
        raise OtpError(INVALID_CODE)
    rows = query('otp_by_request.sql', (pending['request_id'],))
    if not rows:
        # Unknown email, expired, or used up: indistinguishable from a wrong code.
        raise OtpError(INVALID_CODE)
    row = rows[0]

    max_attempts = current_app.config['OTP_MAX_ATTEMPTS']
    if row['expires_at'] < time.time() or row['attempts'] >= max_attempts:
        execute('otp_delete.sql', (row['id'],))
        raise OtpError(INVALID_CODE)

    # Count the guess before judging it, so a failure can never skip the count.
    execute('otp_record_attempt.sql', (row['id'],))
    entered = re.sub(r'[\s-]', '', code or '')
    if not hmac.compare_digest(row['code_hash'], _digest(pending['request_id'], entered)):
        if row['attempts'] + 1 >= max_attempts:
            execute('otp_delete.sql', (row['id'],))
        raise OtpError(INVALID_CODE)

    execute('otp_delete.sql', (row['id'],))
    session.pop('otp', None)
    return row['email']
