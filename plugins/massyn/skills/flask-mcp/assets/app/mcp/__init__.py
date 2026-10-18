import json
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import limiter
from app.mcp.protocol import handle_jsonrpc
from app.mcp.tokens import (
    consume_auth_code,
    generate_auth_code,
    issue_tokens,
    refresh_tokens,
    validate_token,
)

bp = Blueprint('mcp', __name__)


def base_url() -> str:
    cf_visitor = request.headers.get('CF-Visitor', '')
    is_https = '"scheme":"https"' in cf_visitor or current_app.config.get('FORCE_HTTPS')
    scheme = 'https' if is_https else request.scheme

    trusted_hostnames = current_app.config.get('APP_HOSTNAMES', [])
    if trusted_hostnames:
        host = request.host if request.host in trusted_hostnames else trusted_hostnames[0]
    else:
        # Trusting the Host header is open to injection; set APP_HOSTNAME in production.
        host = request.host
    return f'{scheme}://{host}'


def _param(key: str) -> str:
    """Token endpoint parameters arrive as form data or JSON depending on the client."""
    if request.is_json:
        return (request.get_json(silent=True) or {}).get(key, '')
    return request.form.get(key, '')


def _redirect_back(oauth: dict, params: dict) -> Response:
    if oauth['state']:
        params['state'] = oauth['state']
    sep = '&' if '?' in oauth['redirect_uri'] else '?'
    return redirect(f"{oauth['redirect_uri']}{sep}{urlencode(params)}")


# --- Discovery (RFC 9728 protected resource, RFC 8414 authorisation server) ---

@bp.route('/.well-known/oauth-protected-resource')
def oauth_protected_resource() -> Response:
    base = base_url()
    return jsonify({
        'resource': base,
        'authorization_servers': [base],
        'bearer_methods_supported': ['header'],
    })


@bp.route('/.well-known/oauth-authorization-server')
def oauth_metadata() -> Response:
    base = base_url()
    return jsonify({
        'issuer': base,
        'authorization_endpoint': f'{base}/oauth/authorize',
        'token_endpoint': f'{base}/oauth/token',
        'registration_endpoint': f'{base}/oauth/register',
        'response_types_supported': ['code'],
        'grant_types_supported': ['authorization_code', 'refresh_token'],
        'code_challenge_methods_supported': ['S256'],
        'token_endpoint_auth_methods_supported': ['none'],
    })


# --- OAuth 2.1 authorisation server ---

@bp.route('/oauth/register', methods=['POST'])
def oauth_register() -> Response:
    # Dynamic client registration (RFC 7591). Clients are public (PKCE, no secret), so nothing
    # is stored: the client_id is echoed back and bound to the auth code at authorise time.
    data = request.get_json(silent=True) or {}
    return jsonify({
        'client_id': data.get('client_id') or secrets.token_urlsafe(16),
        'client_id_issued_at': int(datetime.now(timezone.utc).timestamp()),
        'redirect_uris': data.get('redirect_uris', []),
        'grant_types': data.get('grant_types', ['authorization_code']),
        'response_types': data.get('response_types', ['code']),
        'token_endpoint_auth_method': 'none',
        'client_name': data.get('client_name', ''),
    }), 201


def _render_consent(oauth: dict) -> str:
    return render_template(
        'mcp/authorize.html',
        client_id=oauth['client_id'],
        redirect_host=urlparse(oauth['redirect_uri']).netloc,
    )


@bp.route('/oauth/authorize', methods=['GET'])
def oauth_authorize() -> Response:
    # Returning from Google sign-in: the request parameters were parked in the session.
    if 'user' in session and session.get('mcp_oauth'):
        return _render_consent(session['mcp_oauth'])

    if request.args.get('response_type') != 'code':
        return jsonify({'error': 'unsupported_response_type'}), 400
    client_id = request.args.get('client_id', '')
    redirect_uri = request.args.get('redirect_uri', '')
    if not client_id or not redirect_uri:
        return jsonify({'error': 'invalid_request'}), 400

    session['mcp_oauth'] = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': request.args.get('state', ''),
        'code_challenge': request.args.get('code_challenge', ''),
        'code_challenge_method': request.args.get('code_challenge_method', 'S256'),
    }

    if 'user' not in session:
        return redirect(url_for('auth.google'))
    return _render_consent(session['mcp_oauth'])


@bp.route('/oauth/authorize', methods=['POST'])
def oauth_authorize_post() -> Response:
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    oauth = session.pop('mcp_oauth', None)
    if not oauth:
        return jsonify({'error': 'invalid_request', 'error_description': 'No pending authorisation'}), 400

    if request.form.get('action') != 'allow':
        return _redirect_back(oauth, {'error': 'access_denied'})

    code = generate_auth_code(
        user_id=session['user']['id'],
        client_id=oauth['client_id'],
        redirect_uri=oauth['redirect_uri'],
        code_challenge=oauth['code_challenge'],
        code_challenge_method=oauth['code_challenge_method'],
    )
    return _redirect_back(oauth, {'code': code})


@bp.route('/oauth/token', methods=['POST'])
def oauth_token() -> Response:
    grant_type = _param('grant_type')

    if grant_type == 'authorization_code':
        client_id = _param('client_id')
        row = consume_auth_code(_param('code'), client_id, _param('redirect_uri'), _param('code_verifier'))
        if not row:
            return jsonify({'error': 'invalid_grant'}), 400
        tokens = issue_tokens(row['user_id'], client_id)
    elif grant_type == 'refresh_token':
        tokens = refresh_tokens(_param('refresh_token'))
        if not tokens:
            return jsonify({'error': 'invalid_grant'}), 400
    else:
        return jsonify({'error': 'unsupported_grant_type'}), 400

    access_token, refresh_token = tokens
    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'refresh_token': refresh_token,
    })


# --- MCP endpoint (Streamable HTTP, stateless) ---

def _unauthorised() -> Response:
    resp = jsonify({'error': 'unauthorized'})
    resp.status_code = 401
    # Points the client at discovery, which starts the OAuth flow.
    resp.headers['WWW-Authenticate'] = (
        f'Bearer resource_metadata="{base_url()}/.well-known/oauth-protected-resource"'
    )
    return resp


def _respond(payload: dict | list) -> Response:
    if 'text/event-stream' in request.headers.get('Accept', ''):
        body = f'data: {json.dumps(payload)}\n\n'
        return Response(body, mimetype='text/event-stream', headers={'Cache-Control': 'no-cache'})
    return jsonify(payload)


# POST only: a stateless server has nothing to push, and the spec allows 405 for GET.
@bp.route('/', methods=['POST'])
@limiter.limit(lambda: current_app.config['MCP_RATE_LIMIT'])
def mcp_endpoint() -> Response:
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return _unauthorised()
    token_row = validate_token(auth_header[len('Bearer '):])
    if not token_row:
        return _unauthorised()

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'invalid_request'}), 400

    user_id: int = token_row['user_id']

    if isinstance(data, list):
        responses = [r for item in data if (r := handle_jsonrpc(item, user_id)) is not None]
        return _respond(responses) if responses else ('', 204)

    response = handle_jsonrpc(data, user_id)
    return _respond(response) if response is not None else ('', 204)
