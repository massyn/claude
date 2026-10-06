"""PWA wiring: the service worker route and the tab-bar section lookup.

Register with `app.register_blueprint(pwa.bp)` and expose `nav_section` to templates through the
app factory's context processor.
"""

from flask import Blueprint, current_app, request

bp = Blueprint('pwa', __name__)

# Which bottom-bar tab each page belongs to. Endpoints are checked first, then blueprints, so a
# single page can sit under a different tab from the rest of its blueprint. Pages listed in
# neither light up no tab.
TAB_BY_ENDPOINT = {
    'main.index': 'home',
    'main.about': 'about',
    'auth.login': 'me',
}
TAB_BY_BLUEPRINT = {
    'auth': 'me',
}


@bp.route('/sw.js')
def service_worker():
    """Serve the service worker from the site root: its scope is the path it is served from,
    so from /static/ it would control no app pages."""
    return current_app.send_static_file('sw.js')


def nav_section() -> str:
    """The tab the current page belongs to, or '' when it belongs to none."""
    endpoint = request.endpoint or ''
    if endpoint in TAB_BY_ENDPOINT:
        return TAB_BY_ENDPOINT[endpoint]
    return TAB_BY_BLUEPRINT.get(request.blueprint or '', '')
