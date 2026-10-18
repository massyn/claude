import logging

from flask import current_app

from app.mcp.instructions import build_instructions
from app.mcp.tools import TOOLS_LIST, handle_tool_call

_log = logging.getLogger(__name__)

PROTOCOL_VERSION = '2024-11-05'


def _result(req_id, result: dict) -> dict:
    return {'jsonrpc': '2.0', 'id': req_id, 'result': result}


def _error(req_id, code: int, message: str) -> dict:
    return {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': code, 'message': message}}


def handle_jsonrpc(data: dict, user_id: int) -> dict | None:
    """Dispatch one JSON-RPC message. Returns None for notifications (no response is sent)."""
    method = data.get('method', '')
    req_id = data.get('id')
    params = data.get('params') or {}

    if method == 'initialize':
        return _result(req_id, {
            'protocolVersion': PROTOCOL_VERSION,
            'capabilities': {'tools': {}},
            'serverInfo': {
                'name': current_app.config['MCP_SERVER_NAME'],
                'version': current_app.config.get('VERSION') or '0.0.0',
            },
            'instructions': build_instructions(user_id),
        })

    if method == 'ping':
        return _result(req_id, {}) if req_id is not None else None

    if method == 'tools/list':
        return _result(req_id, {'tools': TOOLS_LIST})

    if method == 'tools/call':
        return _result(req_id, handle_tool_call(
            params.get('name', ''), params.get('arguments') or {}, user_id,
        ))

    # Notifications (no id), including notifications/initialized, get no response.
    if req_id is None:
        return None

    _log.info('MCP method not found: %s', method)
    return _error(req_id, -32601, f'Method not found: {method}')
