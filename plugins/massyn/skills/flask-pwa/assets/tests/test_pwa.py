"""PWA wiring checks: service worker scope, manifest, icons, head tags and the tab bar.

Uses the app's own `client` fixture if conftest.py defines one; otherwise the fixture below builds
the app against a throwaway SQLite database.
"""

import json
import os
import re
from pathlib import Path

import pytest


@pytest.fixture
def client(tmp_path):
    os.environ.setdefault('DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    from app import create_app

    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


def precached_urls(client) -> list[str]:
    source = client.get('/sw.js').get_data(as_text=True)
    match = re.search(r'const PRECACHE = \[(.*?)\];', source, re.DOTALL)
    assert match, 'sw.js must declare const PRECACHE = [...]'
    return re.findall(r"'([^']+)'", match.group(1))


def test_service_worker_is_served_from_site_root(client):
    res = client.get('/sw.js')
    assert res.status_code == 200
    assert res.mimetype in ('text/javascript', 'application/javascript')
    assert "addEventListener('fetch'" in res.get_data(as_text=True)


def test_precached_pages_render_without_redirect(client):
    # A redirect would be cached in place of the page and served offline.
    for url in precached_urls(client):
        assert client.get(url).status_code == 200, url


def test_manifest_is_installable(client):
    res = client.get('/static/manifest.json')
    assert res.status_code == 200
    manifest = json.loads(res.get_data(as_text=True))
    for field in ('name', 'short_name', 'start_url', 'display', 'theme_color', 'background_color'):
        assert manifest.get(field), field
    assert manifest['display'] in ('standalone', 'fullscreen', 'minimal-ui')
    sizes = {icon['sizes'] for icon in manifest['icons']}
    assert {'192x192', '512x512'} <= sizes
    assert any('maskable' in icon.get('purpose', '') for icon in manifest['icons'])


def test_manifest_icons_exist(client):
    manifest = json.loads(client.get('/static/manifest.json').get_data(as_text=True))
    static_folder = Path(client.application.static_folder)
    for icon in manifest['icons']:
        assert (static_folder / icon['src']).is_file(), icon['src']


def test_pages_carry_pwa_head_and_register_the_worker(client):
    page = client.get('/').get_data(as_text=True)
    assert 'rel="manifest"' in page
    assert 'rel="apple-touch-icon"' in page
    assert 'name="theme-color"' in page
    assert 'viewport-fit=cover' in page
    assert 'data-sw="/sw.js"' in page


def test_tab_bar_marks_the_current_tab(client):
    page = client.get('/').get_data(as_text=True)
    assert 'class="pwa-tab-bar' in page
    current = re.findall(r'<a href="([^"]+)" class="pwa-tab active" aria-current="page">', page)
    assert current == ['/']
