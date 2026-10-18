"""MCP server checks: discovery, the OAuth 2.1 + PKCE flow, personal access tokens and JSON-RPC.

Signs in through the TEST_USER bypass, so no Google credentials are needed. Uses a throwaway
SQLite database.
"""

import base64
import hashlib
import json
import os
import secrets
from urllib.parse import parse_qs, urlparse

import pytest

REDIRECT_URI = 'https://claude.ai/api/mcp/auth_callback'


@pytest.fixture
def app(tmp_path):
    os.environ.setdefault('DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    from app import create_app

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, TEST_USER='alice', RATELIMIT_ENABLED=False)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    return verifier, challenge


def authorise(client, challenge: str, action: str = 'allow') -> dict:
    """Run authorise -> sign-in -> consent and return the redirect's query parameters."""
    res = client.get('/oauth/authorize', query_string={
        'response_type': 'code',
        'client_id': 'test-client',
        'redirect_uri': REDIRECT_URI,
        'state': 'xyz',
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'claude.ai' in res.data, 'consent page must show where the code is being sent'

    res = client.post('/oauth/authorize', data={'action': action})
    assert res.status_code == 302
    location = urlparse(res.headers['Location'])
    assert f'{location.scheme}://{location.netloc}{location.path}' == REDIRECT_URI
    return {k: v[0] for k, v in parse_qs(location.query).items()}


def exchange(client, code: str, verifier: str):
    return client.post('/oauth/token', data={
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': 'test-client',
        'redirect_uri': REDIRECT_URI,
        'code_verifier': verifier,
    })


def oauth_tokens(client) -> dict:
    verifier, challenge = pkce_pair()
    params = authorise(client, challenge)
    res = exchange(client, params['code'], verifier)
    assert res.status_code == 200
    return res.get_json()


def rpc(client, token: str, method: str, params: dict | None = None, req_id: int | None = 1, **headers):
    message = {'jsonrpc': '2.0', 'method': method, 'params': params or {}}
    if req_id is not None:
        message['id'] = req_id
    return client.post('/', json=message, headers={'Authorization': f'Bearer {token}', **headers})


# --- Discovery ---

def test_unauthenticated_request_points_at_discovery(client):
    res = client.post('/', json={'jsonrpc': '2.0', 'id': 1, 'method': 'initialize'})
    assert res.status_code == 401
    assert '/.well-known/oauth-protected-resource' in res.headers['WWW-Authenticate']


def test_bad_token_is_rejected(client):
    assert rpc(client, 'not-a-token', 'tools/list').status_code == 401


def test_discovery_documents(client):
    resource = client.get('/.well-known/oauth-protected-resource').get_json()
    server = client.get('/.well-known/oauth-authorization-server').get_json()
    assert resource['authorization_servers'] == [server['issuer']]
    assert server['code_challenge_methods_supported'] == ['S256']
    assert server['token_endpoint'].endswith('/oauth/token')
    assert server['registration_endpoint'].endswith('/oauth/register')


def test_dynamic_client_registration(client):
    res = client.post('/oauth/register', json={'redirect_uris': [REDIRECT_URI], 'client_name': 'Claude'})
    assert res.status_code == 201
    body = res.get_json()
    assert body['client_id']
    assert body['token_endpoint_auth_method'] == 'none'


# --- OAuth flow ---

def test_full_oauth_flow_issues_working_token(client):
    tokens = oauth_tokens(client)
    assert tokens['token_type'] == 'Bearer'
    res = rpc(client, tokens['access_token'], 'tools/call', {'name': 'whoami', 'arguments': {}})
    assert res.status_code == 200
    whoami = json.loads(res.get_json()['result']['content'][0]['text'])
    assert whoami['name'] == 'alice'


def test_state_is_returned(client):
    _, challenge = pkce_pair()
    assert authorise(client, challenge)['state'] == 'xyz'


def test_deny_returns_access_denied(client):
    _, challenge = pkce_pair()
    params = authorise(client, challenge, action='deny')
    assert params == {'error': 'access_denied', 'state': 'xyz'}


def test_wrong_pkce_verifier_is_rejected(client):
    _, challenge = pkce_pair()
    params = authorise(client, challenge)
    res = exchange(client, params['code'], 'wrong-verifier')
    assert res.status_code == 400
    assert res.get_json()['error'] == 'invalid_grant'


def test_auth_code_is_single_use(client):
    verifier, challenge = pkce_pair()
    params = authorise(client, challenge)
    assert exchange(client, params['code'], verifier).status_code == 200
    assert exchange(client, params['code'], verifier).status_code == 400


def test_refresh_rotates_tokens(client):
    tokens = oauth_tokens(client)
    res = client.post('/oauth/token', data={'grant_type': 'refresh_token', 'refresh_token': tokens['refresh_token']})
    assert res.status_code == 200
    fresh = res.get_json()
    assert fresh['access_token'] != tokens['access_token']
    assert rpc(client, tokens['access_token'], 'tools/list').status_code == 401
    assert rpc(client, fresh['access_token'], 'tools/list').status_code == 200
    reuse = client.post('/oauth/token', data={'grant_type': 'refresh_token', 'refresh_token': tokens['refresh_token']})
    assert reuse.status_code == 400


def test_token_endpoint_accepts_json(client):
    tokens = oauth_tokens(client)
    res = client.post('/oauth/token', json={'grant_type': 'refresh_token', 'refresh_token': tokens['refresh_token']})
    assert res.status_code == 200


# --- Personal access tokens ---

def test_personal_access_token(client):
    client.get('/auth/google', follow_redirects=True)
    client.post('/tokens/generate')
    with client.session_transaction() as sess:
        token = sess['new_pat']
    page = client.get('/tokens/')
    assert token.encode() in page.data, 'new token is shown once with the claude mcp add command'
    assert rpc(client, token, 'tools/list').status_code == 200

    client.post('/tokens/revoke')
    assert rpc(client, token, 'tools/list').status_code == 401


# --- JSON-RPC ---

def test_initialize(client):
    token = oauth_tokens(client)['access_token']
    result = rpc(client, token, 'initialize').get_json()['result']
    assert result['capabilities'] == {'tools': {}}
    assert result['serverInfo']['name']
    assert 'alice' in result['instructions']


def test_every_tool_declares_input_schema_and_no_output_schema(client):
    token = oauth_tokens(client)['access_token']
    tools = rpc(client, token, 'tools/list').get_json()['result']['tools']
    assert tools
    for tool in tools:
        assert tool['inputSchema']['type'] == 'object', tool['name']
        assert 'outputSchema' not in tool, tool['name']


def test_every_listed_tool_has_a_handler(client):
    token = oauth_tokens(client)['access_token']
    tools = rpc(client, token, 'tools/list').get_json()['result']['tools']
    for tool in tools:
        result = rpc(client, token, 'tools/call', {'name': tool['name'], 'arguments': {}}).get_json()['result']
        assert 'Unknown tool' not in result['content'][0]['text'], tool['name']


def test_unknown_tool_is_a_tool_error(client):
    token = oauth_tokens(client)['access_token']
    result = rpc(client, token, 'tools/call', {'name': 'nope', 'arguments': {}}).get_json()['result']
    assert result['isError'] is True


def test_notification_gets_no_body(client):
    token = oauth_tokens(client)['access_token']
    res = rpc(client, token, 'notifications/initialized', req_id=None)
    assert res.status_code == 204


def test_unknown_method(client):
    token = oauth_tokens(client)['access_token']
    assert rpc(client, token, 'resources/list').get_json()['error']['code'] == -32601


def test_batch(client):
    token = oauth_tokens(client)['access_token']
    res = client.post('/', json=[
        {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'},
        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
        {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
    ], headers={'Authorization': f'Bearer {token}'})
    assert [r['id'] for r in res.get_json()] == [1, 2]


def test_sse_response_when_accepted(client):
    token = oauth_tokens(client)['access_token']
    res = rpc(client, token, 'ping', Accept='application/json, text/event-stream')
    assert res.mimetype == 'text/event-stream'
    body = res.get_data(as_text=True)
    assert body.startswith('data: ') and json.loads(body[len('data: '):])['id'] == 1
