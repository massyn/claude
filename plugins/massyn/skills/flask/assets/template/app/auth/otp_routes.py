"""Email sign-in: ask for a code, enter it. Also the TEST_USER bypass, which skips the code."""

from flask import current_app, flash, redirect, render_template, request, url_for

from app import limiter
from app.auth import after_login_url, bp, establish_session, mailgun, otp
from app.auth.service import get_remote_ip, is_valid_email, normalise_email, sign_in_user


def _email_key() -> str:
    """Rate-limit key: the email being asked about, so one inbox cannot be flooded from many IPs."""
    return normalise_email(request.form.get('email')) or get_remote_ip()


def _pending_key() -> str:
    return otp.pending_email() or get_remote_ip()


@bp.route('/login', methods=['POST'])
@limiter.limit('20 per hour')
@limiter.limit('5 per hour', key_func=_email_key)
def login_submit():
    email = normalise_email(request.form.get('email'))
    if not is_valid_email(email):
        flash('Enter a valid email address.', 'danger')
        return redirect(url_for('auth.login'))

    # Dev only: the TEST_USER email signs straight in, with no code and no email.
    if email == current_app.config.get('TEST_USER'):
        user = sign_in_user(email, create=True)
        if user is None:  # the account is disabled
            flash("That account can't sign in.", 'danger')
            return redirect(url_for('auth.login'))
        establish_session(user, 'test')
        return redirect(after_login_url())

    try:
        otp.request_code(email)
    except mailgun.MailError as e:
        flash(str(e), 'danger')
        return redirect(url_for('auth.login'))
    return redirect(url_for('auth.login_code'))


@bp.route('/code', methods=['GET', 'POST'])
@limiter.limit('20 per hour', methods=['POST'])
def login_code():
    email = otp.pending_email()
    if not email:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        try:
            verified = otp.verify_code(request.form.get('code', ''))
        except otp.OtpError as e:
            flash(str(e), 'danger')
        else:
            user = sign_in_user(verified, create=current_app.config.get('ALLOW_SIGNUP', False))
            if user is not None:
                establish_session(user, 'code')
                return redirect(after_login_url())
            flash(otp.INVALID_CODE, 'danger')
    return render_template('login_code.html', email=email, code_length=otp.CODE_LENGTH)


@bp.route('/code/resend', methods=['POST'])
@limiter.limit('5 per hour', key_func=_pending_key)
def login_code_resend():
    email = otp.pending_email()
    if not email:
        return redirect(url_for('auth.login'))
    try:
        otp.request_code(email)
    except mailgun.MailError as e:
        flash(str(e), 'danger')
    else:
        flash('A new code is on its way if that address can sign in.', 'info')
    return redirect(url_for('auth.login_code'))
