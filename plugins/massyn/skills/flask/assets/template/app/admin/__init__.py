"""Admin interface: manage who can sign in. Every route needs the admin role."""

from flask import Blueprint

bp = Blueprint('admin', __name__, url_prefix='/admin')

from app.admin import routes  # noqa: E402,F401 - registers the routes on bp
