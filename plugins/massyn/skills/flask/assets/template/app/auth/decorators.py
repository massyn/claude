from functools import wraps

from flask import abort, redirect, session, url_for

from app.auth.service import is_admin_email
from app.db import query


def current_user() -> dict | None:
    """The signed-in user, checked against the database on every request.

    A user an admin has disabled or deleted is signed out at once, and a changed role takes effect
    at once. The breakglass ADMIN_USER has no row (id is None), so there is nothing to check.
    """
    user = session.get('user')
    if not user or user['id'] is None:
        return user
    rows = query('user_by_id.sql', (user['id'],))
    if not rows or (rows[0]['disabled'] and not is_admin_email(rows[0]['email'])):
        session.pop('user', None)
        return None
    role = 'admin' if is_admin_email(rows[0]['email']) else rows[0]['role']
    if role != user['role']:
        session['user'] = {**user, 'role': role}
    return session['user']


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user():
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def account_required(f):
    """Signed in as someone with a users row, which the ADMIN_USER breakglass account lacks.

    Use it for anything that attaches data to a user (tokens, passkeys, preferences).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for('auth.login'))
        if user['id'] is None:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for('auth.login'))
        if user['role'] != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated
