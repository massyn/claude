"""Sign-in and admin checks: emailed codes, the ADMIN_USER and TEST_USER special cases, disabled users
and the user admin screens. Uses a throwaway SQLite database and a fake Mailgun.
"""

import re

ADMIN = 'breakglass@example.com'
TEST = 'dev@example.com'


def add_user(app, email, role='user', name=''):
    from app.admin.users import add_user as add

    with app.app_context():
        add(email, name, role)


def user_row(app, email):
    from app.db import query

    with app.app_context():
        rows = query('user_by_email.sql', (email,))
        return rows[0] if rows else None


def last_code(app) -> str:
    return re.search(r'\d{6}', app.sent[-1][1]).group()


def request_code(client, email):
    return client.post('/auth/login', data={'email': email})


def sign_in(app, client, email):
    request_code(client, email)
    return client.post('/auth/code', data={'code': last_code(app)})


def signed_in(client):
    with client.session_transaction() as s:
        return s.get('user')


def test_code_signs_in_a_known_user_and_lowercases_the_email(app, client):
    add_user(app, 'alice@example.com', name='Alice')
    res = request_code(client, ' Alice@Example.COM ')
    assert res.headers['Location'].endswith('/auth/code')
    assert [to for to, _, _ in app.sent] == ['alice@example.com']

    res = client.post('/auth/code', data={'code': last_code(app)})
    assert res.status_code == 302
    user = signed_in(client)
    assert user['email'] == 'alice@example.com' and user['role'] == 'user'
    row = user_row(app, 'alice@example.com')
    assert row['last_login'] and row['last_method'] == 'code'


def test_stored_code_is_not_the_code(app, client):
    from app.db import query

    add_user(app, 'alice@example.com')
    request_code(client, 'alice@example.com')
    with client.session_transaction() as s:
        request_id = s['otp']['request_id']
    with app.app_context():
        stored = query('otp_by_request.sql', (request_id,))
    assert stored and stored[0]['code_hash'] != last_code(app)


def test_unknown_email_gets_the_same_page_but_no_code(app, client):
    res = request_code(client, 'stranger@example.com')
    assert res.headers['Location'].endswith('/auth/code')
    assert app.sent == []
    res = client.post('/auth/code', data={'code': '123456'}, follow_redirects=True)
    assert b"isn&#39;t right or has expired" in res.data
    assert signed_in(client) is None


def test_code_dies_after_too_many_wrong_guesses(app, client):
    add_user(app, 'alice@example.com')
    request_code(client, 'alice@example.com')
    right = last_code(app)
    wrong = '000000' if right != '000000' else '000001'
    for _ in range(5):
        client.post('/auth/code', data={'code': wrong})
    client.post('/auth/code', data={'code': right})
    assert signed_in(client) is None


def test_code_works_only_in_the_browser_that_asked(app, client):
    add_user(app, 'alice@example.com')
    request_code(client, 'alice@example.com')
    other = app.test_client()
    res = other.post('/auth/code', data={'code': last_code(app)})
    assert res.status_code == 302 and res.headers['Location'].endswith('/auth/login')
    assert signed_in(other) is None


def test_expired_and_used_codes_are_refused(app, client):
    add_user(app, 'alice@example.com')
    app.config['OTP_TTL_SECONDS'] = -1
    request_code(client, 'alice@example.com')
    client.post('/auth/code', data={'code': last_code(app)})
    assert signed_in(client) is None

    app.config['OTP_TTL_SECONDS'] = 600
    sign_in(app, client, 'alice@example.com')
    assert signed_in(client)
    client.get('/auth/logout')
    client.post('/auth/code', data={'code': last_code(app)})
    assert signed_in(client) is None


def test_a_new_code_replaces_the_old_one(app, client):
    add_user(app, 'alice@example.com')
    request_code(client, 'alice@example.com')
    first = last_code(app)
    client.post('/auth/code/resend')
    second = last_code(app)
    if first != second:
        client.post('/auth/code', data={'code': first})
        assert signed_in(client) is None
    client.post('/auth/code', data={'code': second})
    assert signed_in(client)


def test_login_page_says_when_mail_is_not_configured(app, client):
    app.config['MAILGUN_API_KEY'] = ''
    res = client.get('/auth/login')
    assert b'Mailgun settings are missing' in res.data
    request_code(client, 'alice@example.com')
    assert app.sent == []


def test_signup_only_when_allowed(app, client):
    request_code(client, 'new@example.com')
    assert app.sent == []
    assert user_row(app, 'new@example.com') is None

    app.config['ALLOW_SIGNUP'] = True
    sign_in(app, client, 'new@example.com')
    assert signed_in(client)['email'] == 'new@example.com'
    assert user_row(app, 'new@example.com')


def test_passkey_signup_is_opt_in(app, client):
    assert client.get('/auth/passkey/signup').status_code == 404
    assert b'Create an account with a passkey' not in client.get('/auth/login').data
    res = client.post('/auth/passkey/register/options', json={'name': 'Mallory'})
    assert res.status_code == 400

    app.config['PASSKEY_SIGNUP'] = True
    assert client.get('/auth/passkey/signup').status_code == 200
    assert b'Create an account with a passkey' in client.get('/auth/login').data


def test_admin_user_is_a_breakglass_admin_with_no_row(app, client):
    app.config['ADMIN_USER'] = ADMIN
    sign_in(app, client, ADMIN.upper())
    user = signed_in(client)
    assert user['role'] == 'admin' and user['id'] is None
    assert user_row(app, ADMIN) is None
    assert client.get('/admin/users').status_code == 200
    assert client.get('/auth/passkeys').status_code == 302  # no passkeys for a rowless account


def test_admin_user_overrides_the_stored_role_and_cannot_be_disabled(app, client):
    app.config['ADMIN_USER'] = ADMIN
    add_user(app, ADMIN, role='user')
    from app.db import execute

    with app.app_context():
        execute('user_update.sql', ('x', 'user', 1, user_row(app, ADMIN)['id']))
    sign_in(app, client, ADMIN)
    assert signed_in(client)['role'] == 'admin'


def test_regular_user_cannot_open_admin(app, client):
    add_user(app, 'alice@example.com')
    sign_in(app, client, 'alice@example.com')
    assert client.get('/admin/users').status_code == 403
    assert client.post('/admin/users/1/delete').status_code == 403


def test_test_user_signs_in_without_a_code_and_the_login_page_says_so(app, client):
    app.config['TEST_USER'] = TEST
    assert b'TEST_USER active' in client.get('/auth/login').data
    res = request_code(client, TEST.upper())
    assert res.status_code == 302 and app.sent == []
    assert signed_in(client)['email'] == TEST

    other = app.test_client()
    request_code(other, 'someone@example.com')
    assert signed_in(other) is None


def test_test_user_inactive_by_default(app, client):
    assert b'TEST_USER active' not in client.get('/auth/login').data
    request_code(client, TEST)
    assert signed_in(client) is None


def test_disabled_user_gets_no_code_and_a_live_session_ends(app, client):
    add_user(app, 'alice@example.com')
    add_user(app, 'boss@example.com', role='admin')
    sign_in(app, client, 'alice@example.com')
    assert client.get('/auth/passkeys').status_code == 200

    from app.db import execute

    with app.app_context():
        execute('user_update.sql', ('Alice', 'user', 1, user_row(app, 'alice@example.com')['id']))
    assert client.get('/auth/passkeys').status_code == 302
    assert signed_in(client) is None

    app.sent.clear()
    request_code(app.test_client(), 'alice@example.com')
    assert app.sent == []


def test_admin_screens_add_edit_and_delete(app, client):
    add_user(app, 'boss@example.com', role='admin')
    sign_in(app, client, 'boss@example.com')

    res = client.post('/admin/users/new', data={'email': 'Bob@Example.com', 'name': 'Bob', 'role': 'user'})
    assert res.status_code == 302
    bob = user_row(app, 'bob@example.com')
    assert bob['role'] == 'user'

    res = client.post('/admin/users/new', data={'email': 'bob@example.com', 'role': 'user'})
    assert b'already exists' in res.data

    list_page = client.get('/admin/users?sort=last_login&direction=desc')
    assert b'bob@example.com' in list_page.data and b'Never' in list_page.data
    assert client.get('/admin/users?sort=1;DROP TABLE users').status_code == 200

    client.post(f'/admin/users/{bob["id"]}/edit', data={'name': 'Robert', 'role': 'admin', 'enabled': 'on'})
    bob = user_row(app, 'bob@example.com')
    assert (bob['name'], bob['role'], bob['disabled']) == ('Robert', 'admin', 0)
    client.post(f'/admin/users/{bob["id"]}/edit', data={'name': 'Robert', 'role': 'admin'})  # switch off
    assert user_row(app, 'bob@example.com')['disabled'] == 1
    assert b'Delete this user' in client.get(f'/admin/users/{bob["id"]}/edit').data

    client.post(f'/admin/users/{bob["id"]}/delete')
    assert user_row(app, 'bob@example.com') is None


def test_admins_cannot_lock_themselves_out(app, client):
    add_user(app, 'boss@example.com', role='admin')
    sign_in(app, client, 'boss@example.com')
    me = user_row(app, 'boss@example.com')

    client.post(f'/admin/users/{me["id"]}/edit', data={'name': 'Boss', 'role': 'user'})
    assert user_row(app, 'boss@example.com')['role'] == 'admin'
    client.post(f'/admin/users/{me["id"]}/edit', data={'name': 'Boss2'})  # a locked switch is not sent
    row = user_row(app, 'boss@example.com')
    assert (row['name'], row['disabled']) == ('Boss2', 0)
    client.post(f'/admin/users/{me["id"]}/delete')
    assert user_row(app, 'boss@example.com')
    assert b'Delete this user' not in client.get(f'/admin/users/{me["id"]}/edit').data
