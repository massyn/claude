# Building tools

All tools live in `app/mcp/tools.py`: a `TOOLS_LIST` of definitions, one handler function per tool,
and a `_HANDLERS` dict mapping name to handler. When the file passes ~400 lines, split handlers into
modules by domain (`app/mcp/tools_entries.py`, `app/mcp/tools_todos.py`), each exporting its
definitions and handlers, and have `tools.py` concatenate them.

## Adding a tool

1. Add the definition to `TOOLS_LIST`.
2. Write `_<name>(args: dict, user_id: int) -> dict`.
3. Register it in `_HANDLERS`.
4. Add any SQL as `templates/sql/mcp_<thing>_<operation>.sql`, filtering on the user.
5. `pytest tests/test_mcp.py` - it checks every listed tool has a handler and an `inputSchema`.

```python
{
    'name': 'add_note',
    'description': (
        'Creates a note in a project. The project is created implicitly if it does not exist. '
        'Returns the new note id. Check get_projects first and reuse an existing project.'
    ),
    'inputSchema': {
        'type': 'object',
        'properties': {
            'project': {'type': 'string', 'description': 'Lowercase hyphenated slug e.g. my-project'},
            'title': {'type': 'string'},
            'body': {'type': 'string', 'description': 'Markdown'},
            'priority': {'type': 'integer', 'description': '1 (critical) to 5 (backlog). Default: 3.'},
        },
        'required': ['project', 'title'],
    },
},
```

```python
def _add_note(args: dict, user_id: int) -> dict:
    project = args.get('project', '').strip().lower()
    title = html.unescape(args.get('title', '').strip())
    body = html.unescape(args.get('body', '').strip())
    priority = int(args.get('priority') or 3)
    if not project or not title:
        return _err('project and title are required')
    if not 1 <= priority <= 5:
        raise ValueError('priority must be between 1 and 5')

    # insert_returning_id: a db.py helper the app adds for INSERT ... RETURNING id (Citadel: insert_entry)
    note_id = insert_returning_id('mcp_note_insert.sql', (user_id, project, title, body, priority))
    return _ok({'id': note_id, 'project': project})
```

## Definitions

- **`inputSchema` always; `outputSchema` never.** An argument-less tool still declares
  `{'type': 'object', 'properties': {}, 'additionalProperties': False}`.
- **`required` lists only what the handler cannot default.** Say the default in the property's
  `description` ("Default: 50.").
- **Describe formats in the property description** - slugs, ISO dates (`YYYY-MM-DD`), allowed values
  (`active or archived`), ranges. Clients do not enforce `enum`/`format` reliably; the description is
  what the model reads.
- **Prefer simple types.** Citadel passes lists as strings (`'JSON array of tags e.g. ["a","b"]'`)
  and accepts JSON, comma- or semicolon-separated input in the handler. Models get strings right
  more often than nested arrays.
- **Ids are strings** in schemas even when integers in the database; convert in the handler.

## Descriptions steer behaviour

The tool `description` is the model's only manual for that tool. Write it for the model:

- First sentence: what it does and what it returns.
- Side effects: "created implicitly if it does not exist", "irreversible - use update with
  status=archived for soft-delete".
- When to call it relative to other tools: "Call this at the start of every conversation",
  "Check get_room first".
- Rules in capitals sparingly: `IMPORTANT: associate with the correct project, not a catch-all.`
- Redirect misuse: "Do not write a checklist into detail - call add_sub_task once per step."

Cross-cutting rules (vocabularies, workflow) go in `SYSTEM_PROMPT` instead - see `protocol.md`.

## Handlers

- **Signature `(args, user_id)`; `user_id` is trusted, `args` is not.** Never accept a user id,
  owner or tenant from `args`.
- **Read arguments defensively:** `args.get('x', '')`, `.strip()`, `int(args.get('n') or default)`.
  Missing optional arguments may be absent, `None` or `''`.
- **Decode HTML entities** on free-text fields with `html.unescape()` - some clients send `&amp;`.
- **Normalise identifiers** the model types (`.strip().lower()` on slugs and names).
- **Partial updates:** an `update_*` tool changes only the fields present in `args`; build the SQL
  with template kwargs saying which columns to set, values still passed as parameters.
- **Return `_ok(data)`** - dicts/lists are JSON-encoded (`default=str` handles dates); a string is
  sent as-is, good for confirmations ("Merged 'a' into 'b'").
- **Return `_err(msg)`** for anything the model can fix: missing arguments, not found
  ("Entry '42' not found"), invalid state. Make the message say what to do.
- **Raise `ValueError`** from deep validation; `handle_tool_call` turns it into `_err`. Any other
  exception is logged and returned as a generic error.
- **Summary vs detail.** List tools return summary fields with pagination (`limit`, `offset`,
  filters); a separate `get_*` returns the full record. Keeps context small.

## SQL

Every query lives in `templates/sql/` (the `flask` skill's SQL rules apply) and every query a tool
runs includes `user_id = ?` - including updates and deletes (`WHERE id = ? AND user_id = ?`), so a
guessed id cannot touch another user's row. Search can use SQLite FTS5 and `ILIKE` on Postgres
behind a `dialect` block, as Citadel's `mcp_search.sql` does.

Mutations that span tables go through one transaction (a `db.py` helper that executes several
templates and commits once).
