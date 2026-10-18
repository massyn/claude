import json
import logging
from collections.abc import Callable

from app.db import query

_log = logging.getLogger(__name__)

# Every tool declares inputSchema. Do not add outputSchema: it breaks Claude-side tool use.
TOOLS_LIST = [
    {
        'name': 'whoami',
        'description': (
            'Returns the signed-in user\'s id, name and email. '
            'Call this at the start of a conversation to confirm which account is in use.'
        ),
        'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
    },
]


def _ok(data) -> dict:
    text = data if isinstance(data, str) else json.dumps(data, default=str)
    return {'content': [{'type': 'text', 'text': text}], 'isError': False}


def _err(msg: str) -> dict:
    return {'content': [{'type': 'text', 'text': msg}], 'isError': True}


def handle_tool_call(name: str, arguments: dict, user_id: int) -> dict:
    handler = _HANDLERS.get(name)
    if handler is None:
        return _err(f'Unknown tool: {name}')
    try:
        return handler(arguments, user_id)
    except ValueError as exc:
        return _err(str(exc))
    except Exception:
        _log.exception('MCP tool %s failed for user %s', name, user_id)
        return _err(f'Internal error running {name}')


# --- Tools ---

def _whoami(args: dict, user_id: int) -> dict:
    rows = query('user_by_id.sql', (user_id,))
    if not rows:
        return _err('User not found')
    return _ok(rows[0])


_HANDLERS: dict[str, Callable[[dict, int], dict]] = {
    'whoami': _whoami,
}
