# Wiring the MCP layer into a golden-template app

Copy `assets/` into the project first (it mirrors the project layout), then make these edits.
Paths assume the package is still called `app`; rename imports to match.

## `config.py`

Add to `Config`:

```python
MCP_SERVER_NAME = os.environ.get('MCP_SERVER_NAME', 'myapp')
MCP_RATE_LIMIT = os.environ.get('MCP_RATE_LIMIT', '1000 per hour')
```

`MCP_SERVER_NAME` is the `serverInfo.name` clients see and the name used in the `claude mcp add`
command on the token page. `MCP_RATE_LIMIT` replaces the app-wide default limit on the MCP endpoint
(see the rate-limit rule in `SKILL.md`). Add both, commented, to `.env.example`.

## `app/__init__.py`

Register both blueprints in `create_app()` and exempt the MCP blueprint from CSRF: MCP clients and
the OAuth token endpoint send bearer tokens or PKCE, never a CSRF token.

```python
from app.pat import bp as pat_bp
app.register_blueprint(pat_bp)

from app.mcp import bp as mcp_bp
app.register_blueprint(mcp_bp)
csrf.exempt(mcp_bp)
```

The consent form (`POST /oauth/authorize`) lives on the exempt blueprint too; it still renders a
`csrf_token` field, and the session-bound `mcp_oauth` parameters it consumes cannot be planted
cross-site. Do not move it to a separate CSRF-protected blueprint unless you also move the GET.

## `app/db.py`

The golden `init_db()` runs `schema.sql` with a single `cursor.execute()`, which SQLite rejects for
more than one statement. Replace it so it runs every schema file, statement by statement:

```python
def init_db(app) -> None:
    with app.app_context():
        conn, dialect = get_db()
        for template in ('schema.sql', 'mcp_schema.sql'):
            sql = render_sql(template, dialect)
            if dialect == 'sqlite':
                conn.executescript(sql)
            else:
                cur = conn.cursor()
                for stmt in sql.split(';'):
                    if stmt.strip():
                        cur.execute(stmt)
        conn.commit()
```

`mcp_schema.sql` references `users(id)`, so it runs after `schema.sql`.

## `app/auth/__init__.py`

When a client sends an unauthenticated user to `/oauth/authorize`, the request is parked in
`session['mcp_oauth']` and the user is sent to Google. After sign-in they must land back on the
consent page, not the home page. In **both** `callback()` and `test_callback()`, replace the final
`return redirect(url_for('main.index'))` with:

```python
if session.get('mcp_oauth'):
    return redirect(url_for('mcp.oauth_authorize'))
return redirect(url_for('main.index'))
```

## `templates/base.html`

Add a link to the token page in the signed-in user dropdown:

```html
<li><a class="dropdown-item" href="{{ url_for('pat.index') }}">🔑 API token</a></li>
```

## Content Security Policy

`templates/tokens/index.html` loads `static/js/tokens.js` (copy buttons, revoke modal) instead of
inline handlers, so no CSP change is needed. Bootstrap's JS bundle must be on the page for the
confirm modals.

## Check

```bash
pytest tests/test_mcp.py
```
