from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.auth.decorators import login_required
from app.db import execute, query
from app.mcp import base_url
from app.mcp.tokens import issue_pat

bp = Blueprint('pat', __name__, url_prefix='/tokens')


def _user_id() -> int:
    return session['user']['id']


@bp.route('/')
@login_required
def index():
    user_id = _user_id()
    rows = query('mcp_pat_get.sql', (user_id,))
    return render_template(
        'tokens/index.html',
        pat=rows[0] if rows else None,
        oauth_tokens=query('mcp_oauth_tokens_get.sql', (user_id,)),
        new_token=session.pop('new_pat', None),
        server_name=current_app.config['MCP_SERVER_NAME'],
        server_url=base_url(),
    )


@bp.route('/generate', methods=['POST'])
@login_required
def generate():
    session['new_pat'] = issue_pat(_user_id())
    return redirect(url_for('pat.index'))


@bp.route('/revoke', methods=['POST'])
@login_required
def revoke():
    execute('mcp_pat_delete.sql', (_user_id(),))
    flash('Token revoked.', 'success')
    return redirect(url_for('pat.index'))


@bp.route('/revoke-oauth', methods=['POST'])
@login_required
def revoke_oauth():
    access_token = request.form.get('access_token', '').strip()
    if access_token:
        execute('mcp_token_delete_by_access.sql', (access_token, _user_id()))
    flash('OAuth session revoked.', 'success')
    return redirect(url_for('pat.index'))
