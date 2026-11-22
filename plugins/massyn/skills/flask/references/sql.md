# SQL templates and `db.py`

## Where SQL lives

All SQL is in `templates/sql/` as Jinja templates, one file per logical query, named by operation
(`user_insert.sql`, `order_list.sql`). `schema.sql` creates tables with `CREATE TABLE IF NOT EXISTS` and is
run by `init_db()` at start-up. `init_db()` runs every file in `db.SCHEMA_FILES`, in order, statement
by statement - add a feature's schema file to that tuple. Postgres statements are split on `;`, so
never put a semicolon inside a SQL comment.

Every template receives `dialect` (`"sqlite"` or `"postgres"`) and emits the right placeholders:

```sql
SELECT id, name, email, role, created_on
FROM users
WHERE email = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
```

Use dialect blocks for anything that differs between engines:

```sql
CREATE TABLE IF NOT EXISTS users (
    {% if dialect == 'sqlite' %}
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {% else %}
    id SERIAL PRIMARY KEY,
    {% endif %}
    email TEXT UNIQUE,
    created_on {% if dialect == 'sqlite' %}DATETIME{% else %}TIMESTAMP{% endif %} DEFAULT CURRENT_TIMESTAMP
)
```

Typical differences: `RETURNING`, `ILIKE` vs `LIKE`, type casts, `ON CONFLICT`, auto-increment keys,
timestamp types.

## Calling SQL from Python

`db.py` picks the driver from `DATABASE_URL` (`sqlite...` → `sqlite3`, anything else → `psycopg` with
`dict_row`), caches the connection on `g` and closes it on app-context teardown.

| Function | Use |
|----------|-----|
| `query(template, params, **context)` | Run a SELECT; returns `list[dict]`. `context` feeds the template (whitelisted identifiers), never values |
| `execute(template, params)` | Run a write and commit |
| `execute_batch([(template, params), ...])` | Run several writes in one transaction - all apply or none do |
| `render_sql(template, dialect, **kwargs)` | Render a template directly (rarely needed) |

```python
rows = query('user_by_email.sql', (email,))
execute('user_add.sql', (name, email, role, new_passkey_handle()))
```

Values are always passed as `params` - never interpolated into the template. Template variables are for
structure only (dialect, and whitelisted identifiers such as a validated sort column).

## Dynamic sorting and pagination

Identifiers cannot be parameterised, so a sortable list passes a **whitelisted** column and direction
into the template as kwargs, while `LIMIT`/`OFFSET` values travel as parameters:

```sql
SELECT id, name, created_on
FROM items
ORDER BY {{ sort }} {{ direction }}
LIMIT {% if dialect == 'sqlite' %}? OFFSET ?{% else %}%s OFFSET %s{% endif %}
```

The route (or service) validates `sort` against an explicit allow-list and `direction` against
`{'asc', 'desc'}` before rendering, then calls `query('items_list.sql', (per_page, offset), sort=..., direction=...)`.
`app/admin/users.py` and `user_list.sql` are a working example.
