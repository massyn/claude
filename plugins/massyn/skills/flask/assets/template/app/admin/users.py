"""Managing users: list, add, edit and delete."""

import logging

from app.auth.service import is_admin_email, is_valid_email, new_passkey_handle, normalise_email
from app.db import execute, execute_batch, query

log = logging.getLogger(__name__)

ROLES = ('user', 'admin')
NAME_MAX_LENGTH = 60

# Query-string sort keys mapped to SQL columns. Only these ever reach ORDER BY.
SORT_COLUMNS = {
    'name': 'u.name',
    'email': 'u.email',
    'role': 'u.role',
    'status': 'u.disabled',
    'last_login': 'u.last_login',
    'created': 'u.created_on',
}


class UserError(Exception):
    """A change was refused; the message is safe to show the admin."""


def list_users(page: int, per_page: int, sort: str, direction: str) -> tuple[list[dict], int]:
    """One page of users, and how many there are in all."""
    rows = query(
        'user_list.sql',
        (per_page, (page - 1) * per_page),
        sort_column=SORT_COLUMNS[sort],
        direction='DESC' if direction == 'desc' else 'ASC',
    )
    return rows, query('user_count.sql')[0]['total']


def get_user(user_id: int) -> dict | None:
    rows = query('user_detail.sql', (user_id,))
    return rows[0] if rows else None


def lock_reason(user: dict, actor_id: int | None) -> str | None:
    """Why this user's role, status and existence can't be changed here, or None if they can."""
    if is_admin_email(user['email']):
        return 'This is the ADMIN_USER breakglass email: it is always an enabled admin.'
    if user['id'] == actor_id:
        return "You can't change your own role or status, or delete yourself."
    return None


def add_user(email: str, name: str, role: str) -> None:
    email = normalise_email(email)
    name = name.strip() or email.split('@')[0]
    if not is_valid_email(email):
        raise UserError('Enter a valid email address.')
    if len(name) > NAME_MAX_LENGTH:
        raise UserError(f'Names can be at most {NAME_MAX_LENGTH} characters.')
    if role not in ROLES:
        raise UserError('Choose a role.')
    if query('user_by_email.sql', (email,)):
        raise UserError('A user with that email already exists.')
    execute('user_add.sql', (name, email, role, new_passkey_handle()))
    log.info('User added: %s (%s)', email, role)


def update_user(actor_id: int | None, user: dict, name: str, role: str, disabled: bool) -> None:
    name = name.strip()
    if not name or len(name) > NAME_MAX_LENGTH:
        raise UserError(f'Enter a name of up to {NAME_MAX_LENGTH} characters.')
    if role not in ROLES:
        raise UserError('Choose a role.')
    if lock_reason(user, actor_id) and (role != user['role'] or disabled != bool(user['disabled'])):
        raise UserError(lock_reason(user, actor_id))
    execute('user_update.sql', (name, role, int(disabled), user['id']))
    log.info('User %s updated by %s: role=%s disabled=%s', user['id'], actor_id, role, disabled)


def delete_user(actor_id: int | None, user: dict) -> None:
    """Delete a user and their passkeys. App tables that reference users must be cleared by the app."""
    if lock_reason(user, actor_id):
        raise UserError(lock_reason(user, actor_id))
    execute_batch([('passkey_delete_by_user.sql', (user['id'],)), ('user_delete.sql', (user['id'],))])
    log.info('User %s deleted by %s', user['id'], actor_id)
