import logging

from app.db import query

_log = logging.getLogger(__name__)

# Product-level operating rules, sent to every client in the initialize response.
# Rewrite this for the app: what the domain objects are, which tool to call first,
# and the conventions the model must follow when writing data.
SYSTEM_PROMPT = """\
You are connected to this app over MCP. Every tool acts on behalf of the signed-in
user and only sees that user's data.

Call whoami at the start of a conversation to confirm which account you are using."""


def build_instructions(user_id: int) -> str:
    """System prompt plus per-user context. Falls back to the bare prompt if the lookup fails."""
    try:
        rows = query('user_by_id.sql', (user_id,))
    except Exception:
        _log.exception('MCP instructions lookup failed for user %s', user_id)
        return SYSTEM_PROMPT
    if not rows:
        return SYSTEM_PROMPT
    return f"{SYSTEM_PROMPT}\n\n## Session\nSigned in as {rows[0]['name']}."
