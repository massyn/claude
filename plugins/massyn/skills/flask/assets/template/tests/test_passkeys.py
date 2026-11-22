"""Passkey checks, against a software authenticator: a P-256 key that answers WebAuthn creation options
with "none" attestation and signs sign-in assertions, so the real ceremonies run with nothing mocked.
"""

import base64
import hashlib
import json
import os
import struct

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

ORIGIN = 'http://localhost'
RP_ID = 'localhost'


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


class SoftAuthenticator:
    """One passkey: a key pair and a credential id."""

    def __init__(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = os.urandom(32)
        self.sign_count = 0

    def _client_data(self, kind: str, challenge: str) -> bytes:
        return json.dumps({'type': kind, 'challenge': challenge, 'origin': ORIGIN, 'crossOrigin': False}).encode()

    def create(self, options: dict) -> dict:
        numbers = self.key.public_key().public_numbers()
        cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: numbers.x.to_bytes(32, 'big'), -3: numbers.y.to_bytes(32, 'big')})
        auth_data = (
            hashlib.sha256(RP_ID.encode()).digest()
            + bytes([0x45])  # user present, user verified, attested credential data
            + struct.pack('>I', self.sign_count)
            + bytes(16)  # AAGUID
            + struct.pack('>H', len(self.credential_id))
            + self.credential_id
            + cose
        )
        return {
            'id': b64(self.credential_id),
            'rawId': b64(self.credential_id),
            'type': 'public-key',
            'clientExtensionResults': {},
            'response': {
                'clientDataJSON': b64(self._client_data('webauthn.create', options['challenge'])),
                'attestationObject': b64(cbor2.dumps({'fmt': 'none', 'attStmt': {}, 'authData': auth_data})),
                'transports': [],
            },
        }

    def sign(self, options: dict, user_handle: str | None = None) -> dict:
        self.sign_count += 1
        client_data = self._client_data('webauthn.get', options['challenge'])
        auth_data = hashlib.sha256(RP_ID.encode()).digest() + bytes([0x05]) + struct.pack('>I', self.sign_count)
        signature = self.key.sign(auth_data + hashlib.sha256(client_data).digest(), ec.ECDSA(hashes.SHA256()))
        return {
            'id': b64(self.credential_id),
            'rawId': b64(self.credential_id),
            'type': 'public-key',
            'clientExtensionResults': {},
            'response': {
                'clientDataJSON': b64(client_data),
                'authenticatorData': b64(auth_data),
                'signature': b64(signature),
                'userHandle': user_handle,
            },
        }


def signed_in_client(app, email='alice@example.com'):
    app.config['TEST_USER'] = email
    client = app.test_client()
    client.post('/auth/login', data={'email': email})  # TEST_USER: no code needed
    return client


def add_passkey(client) -> SoftAuthenticator:
    passkey = SoftAuthenticator()
    options = client.post('/auth/passkey/register/options', json={}).get_json()
    res = client.post('/auth/passkey/register', json=passkey.create(options))
    assert res.status_code == 200, res.get_json()
    return passkey


def sign_in_with(app, passkey, **kwargs):
    client = app.test_client()
    options = client.post('/auth/passkey/login/options').get_json()
    return client, client.post('/auth/passkey/login', json=passkey.sign(options, **kwargs))


def user_row(app, email):
    from app.db import query

    with app.app_context():
        rows = query('user_by_email.sql', (email,))
        return rows[0] if rows else None


def test_a_signed_in_user_adds_a_passkey_and_signs_in_with_it(app):
    client = signed_in_client(app)
    passkey = add_passkey(client)
    assert b'Passkey 1' in client.get('/auth/passkeys').data

    other, res = sign_in_with(app, passkey)
    assert res.status_code == 200
    with other.session_transaction() as s:
        assert s['user']['email'] == 'alice@example.com'
    assert user_row(app, 'alice@example.com')['last_method'] == 'passkey'


def test_a_replayed_or_unknown_passkey_is_refused(app):
    passkey = add_passkey(signed_in_client(app))

    client = app.test_client()
    options = client.post('/auth/passkey/login/options').get_json()
    assertion = passkey.sign(options)
    assert client.post('/auth/passkey/login', json=assertion).status_code == 200
    replay = app.test_client()
    replay.post('/auth/passkey/login/options')
    assert replay.post('/auth/passkey/login', json=assertion).status_code == 400  # new challenge, old signature

    _, res = sign_in_with(app, SoftAuthenticator())
    assert res.status_code == 400


def test_a_disabled_user_cannot_sign_in_with_a_passkey(app):
    from app.db import execute

    passkey = add_passkey(signed_in_client(app))
    row = user_row(app, 'alice@example.com')
    with app.app_context():
        execute('user_update.sql', ('Alice', 'user', 1, row['id']))
    _, res = sign_in_with(app, passkey)
    assert res.status_code == 400


def test_passkey_signup_is_opt_in_and_the_last_passkey_of_a_passkey_only_user_stays(app, client):
    assert client.get('/auth/passkey/signup').status_code == 404
    assert client.post('/auth/passkey/register/options', json={'name': 'Mallory'}).status_code == 400

    app.config['PASSKEY_SIGNUP'] = True
    passkey = SoftAuthenticator()
    options = client.post('/auth/passkey/register/options', json={'name': 'Pat'}).get_json()
    res = client.post('/auth/passkey/register', json=passkey.create(options))
    assert res.status_code == 200
    with client.session_transaction() as s:
        assert s['user']['name'] == 'Pat' and s['user']['email'] == ''

    from app.db import query

    with app.app_context():
        passkey_id = query('passkey_list_by_user.sql', (s['user']['id'],))[0]['id']
    client.post(f'/auth/passkey/{passkey_id}/delete')
    with app.app_context():
        assert query('passkey_list_by_user.sql', (s['user']['id'],))  # removing it would lock them out
