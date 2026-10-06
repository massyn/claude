# Wiring the PWA layer into a golden-template app

Tested against the `flask` skill's golden template: these changes plus the copied assets pass
`tests/test_pwa.py`.

## App factory (`app/__init__.py`)

Register the blueprint and the icon global after the main blueprint, and add `nav_section` to the
existing context processor:

```python
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app import pwa
    from app.icons import ICONS
    app.register_blueprint(pwa.bp)
    app.jinja_env.globals['icon_paths'] = ICONS

    ...

    @app.context_processor
    def inject_globals():
        return dict(
            version=app.config.get('VERSION', ''),
            gtag_id=app.config.get('GTAG_ID', ''),
            nav_section=pwa.nav_section,
        )
```

## `templates/base.html`

1. **Head** — delete the template's own `<meta name="viewport">` (the partial supplies one with
   `viewport-fit=cover`) and include the partial after `theme.css`:

   ```html
   <link rel="stylesheet" href="{{ url_for('static', filename='theme.css') }}">
   {% include "partials/pwa_head.html" %}
   {% block extra_css %}{% endblock %}
   ```

2. **Navbar** — delete the `navbar-toggler` button. Keep `navbar-expand-lg` and the
   `collapse navbar-collapse` wrapper: below `lg` the links stay hidden and the tab bar takes over.

   ```html
   {# No toggler: below lg these links stay hidden and partials/tab_bar.html takes over. #}
   ```

3. **Footer** — give the footer the `site-footer` class so it hides when installed on a phone, and put
   the shared confirm modal before it:

   ```html
   {% include "partials/confirm_modal.html" %}
   <footer class="site-footer text-center text-muted small py-2">
   ```

4. **End of body** — after Bootstrap's bundle (confirm.js needs `bootstrap.Modal`):

   ```html
   <script src="{{ url_for('static', filename='js/confirm.js') }}"></script>
   <script src="{{ url_for('static', filename='js/share.js') }}"></script>
   <script src="{{ url_for('static', filename='js/pwa.js') }}" data-sw="{{ url_for('pwa.service_worker') }}"></script>
   {% block extra_js %}{% endblock %}
   {% include "partials/tab_bar.html" %}
   ```

## Tabs (`app/pwa.py` and `tab_bar.html`)

`TAB_BY_ENDPOINT` and `TAB_BY_BLUEPRINT` map pages to a tab name; `tab_bar.html` calls the `tab()`
macro once per tab with the endpoint it links to, the tab name, its label and an icon from
`app/icons.py`. Endpoint entries win over blueprint entries. When a tab's link is a redirect (Kickstand's
"Rides" goes to the rider's home crew), give it its own small route that redirects, so the tab has a
stable URL to link to.

When the section depends on data (Kickstand lights "Rides" only for the rider's home crew), extend
`nav_section()` and cache the lookup on `flask.g` so the tab bar and navbar don't query twice per request.

## Talisman / CSP

Nothing extra is needed for the PWA itself: the manifest, worker, scripts, icons and fonts are all
`'self'`. `pwa.js` exists so registration needs no inline script.

## Tests

`tests/test_pwa.py` builds the app with a throwaway SQLite database unless the project's `conftest.py`
provides a `client` fixture. Update `test_tab_bar_marks_the_current_tab` if `/` is not a tab.
