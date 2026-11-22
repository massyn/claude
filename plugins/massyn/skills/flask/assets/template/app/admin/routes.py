"""User administration screens. Delete lives on the edit screen, behind a modal confirm."""

import math

from flask import abort, flash, redirect, render_template, request, session, url_for

from app.admin import bp, users
from app.auth.decorators import admin_required

DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 100


def _int_arg(name: str, default: int, maximum: int | None = None) -> int:
    try:
        value = int(request.args.get(name, default))
    except ValueError:
        return default
    value = max(value, 1)
    return min(value, maximum) if maximum else value


def _actor_id() -> int | None:
    return session['user']['id']


def _user_or_404(user_id: int) -> dict:
    user = users.get_user(user_id)
    if user is None:
        abort(404)
    return user


@bp.route('/users')
@admin_required
def user_list():
    per_page = _int_arg('per_page', DEFAULT_PER_PAGE, MAX_PER_PAGE)
    sort = request.args.get('sort', 'name')
    if sort not in users.SORT_COLUMNS:
        sort = 'name'
    direction = 'desc' if request.args.get('direction') == 'desc' else 'asc'
    page = _int_arg('page', 1)
    rows, total = users.list_users(page, per_page, sort, direction)
    return render_template(
        'admin/users.html',
        users=rows,
        page=page,
        pages=max(math.ceil(total / per_page), 1),
        per_page=per_page,
        total=total,
        sort=sort,
        direction=direction,
    )


@bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
def user_new():
    form = {'email': '', 'name': '', 'role': 'user'}
    if request.method == 'POST':
        form = {key: request.form.get(key, '') for key in form}
        try:
            users.add_user(form['email'], form['name'], form['role'])
        except users.UserError as e:
            flash(str(e), 'danger')
        else:
            flash(f'{form["email"].strip().lower()} can now sign in.', 'success')
            return redirect(url_for('admin.user_list'))
    return render_template(
        'admin/user_new.html', form=form, roles=users.ROLES, name_max_length=users.NAME_MAX_LENGTH
    )


@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id: int):
    user = _user_or_404(user_id)
    if request.method == 'POST':
        # A locked user's switch is greyed out, so the browser doesn't send it: keep their status.
        locked = users.lock_reason(user, _actor_id()) is not None
        disabled = bool(user['disabled']) if locked else request.form.get('enabled') != 'on'
        try:
            users.update_user(
                _actor_id(),
                user,
                request.form.get('name', ''),
                request.form.get('role', user['role']),
                disabled=disabled,
            )
        except users.UserError as e:
            flash(str(e), 'danger')
        else:
            flash('User saved.', 'success')
            return redirect(url_for('admin.user_list'))
    return render_template(
        'admin/user_edit.html',
        user=user,
        roles=users.ROLES,
        lock_reason=users.lock_reason(user, _actor_id()),
        name_max_length=users.NAME_MAX_LENGTH,
    )


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def user_delete(user_id: int):
    user = _user_or_404(user_id)
    try:
        users.delete_user(_actor_id(), user)
    except users.UserError as e:
        flash(str(e), 'danger')
        return redirect(url_for('admin.user_edit', user_id=user_id))
    flash(f'{user["email"] or user["name"]} deleted.', 'info')
    return redirect(url_for('admin.user_list'))
