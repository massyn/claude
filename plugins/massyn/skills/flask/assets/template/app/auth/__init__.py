from flask import Blueprint, abort, current_app, flash, redirect, render_template, session, url_for
from authlib.integrations.flask_client import OAuth

from app.auth import mailgun
from app.auth.service import is_admin_email
from app.db import execute

bp = Blueprint('auth', __name__, url_prefix='/auth')
oauth = OAuth()

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)


@bp.route('/login')
def login():
    if session.get('user'):
        return redirect(url_for('main.index'))
    config = current_app.config
    return render_template(
        'login.html',
        mail_configured=mailgun.is_configured(),
        test_user_active=bool(config.get('TEST_USER')),
        google_enabled=bool(config.get('GOOGLE_CLIENT_ID')),
        passkey_signup_enabled=bool(config.get('PASSKEY_SIGNUP')),
    )


@bp.route('/google')
def google():
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        abort(404)
    from app.auth.service import get_oauth_redirect_uri
    return oauth.google.authorize_redirect(get_oauth_redirect_uri())


@bp.route('/callback')
def callback():
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        abort(404)
    token = oauth.google.authorize_access_token()
    info = token.get('userinfo', {})
    from app.auth.service import sign_in_user
    user = None
    # Only a verified Google email is proof of who this is.
    if info.get('email_verified'):
        user = sign_in_user(
            info.get('email', ''),
            info.get('name', ''),
            google_id=info['sub'],
            create=current_app.config.get('ALLOW_SIGNUP', False),
        )
    if user is None:
        flash("That Google account can't sign in here.", 'danger')
        return redirect(url_for('auth.login'))
    establish_session(user, 'google')
    return redirect(after_login_url())


@bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main.index'))


def establish_session(user: dict, method: str) -> None:
    """Start the user's session once a sign-in method has proven who they are.

    `method` (code, google, passkey, test) is recorded as how they last signed in. The ADMIN_USER
    email is always an admin, whatever its row says; that account may have no row (id is None).
    """
    email = user.get('email') or ''
    session.permanent = True
    session['user'] = {
        'id': user['id'],
        'name': user['name'],
        'email': email,
        'role': 'admin' if is_admin_email(email) else user.get('role', 'user'),
    }
    if user['id'] is not None:
        execute('user_record_login.sql', (method, user['id']))


def after_login_url() -> str:
    return url_for('main.index')


from app.auth import passkey_routes  # noqa: E402,F401 - registers the passkey routes on bp
from app.auth import otp_routes  # noqa: E402,F401 - registers the email-code routes on bp
