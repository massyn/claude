"""Sending email through the Mailgun HTTP API. Used for sign-in codes."""

import base64
import logging
import urllib.error
import urllib.parse
import urllib.request

from flask import current_app

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10


class MailError(Exception):
    """The email could not be sent; the message is safe to show the user."""


def is_configured() -> bool:
    """True when the Mailgun credentials are all set."""
    config = current_app.config
    return all(config.get(key) for key in ('MAILGUN_API_KEY', 'MAILGUN_DOMAIN', 'MAILGUN_FROM'))


def send(to: str, subject: str, text: str) -> None:
    """Send a plain-text email, or raise MailError."""
    if not is_configured():
        raise MailError('Email sign-in is not configured.')
    config = current_app.config
    url = (
        f'{config["MAILGUN_BASE_URL"].rstrip("/")}'
        f'/v3/{urllib.parse.quote(config["MAILGUN_DOMAIN"], safe="")}/messages'
    )
    credentials = base64.b64encode(f'api:{config["MAILGUN_API_KEY"]}'.encode()).decode()
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(
            {'from': config['MAILGUN_FROM'], 'to': to, 'subject': subject, 'text': text}
        ).encode(),
        headers={'Authorization': f'Basic {credentials}'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS):
            pass
    except urllib.error.HTTPError as e:
        log.exception('Mailgun rejected the message (HTTP %s)', e.code)
        raise MailError("We couldn't send the email. Please try again shortly.") from e
    except (urllib.error.URLError, TimeoutError) as e:
        log.exception('Mailgun could not be reached')
        raise MailError("We couldn't send the email. Please try again shortly.") from e
