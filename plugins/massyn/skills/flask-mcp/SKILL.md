---
name: flask-mcp
description: Add a remote MCP (Model Context Protocol) server to a Flask app so Claude.ai, Claude Desktop and Claude Code can call the app's tools on behalf of a signed-in user - a stateless Streamable HTTP endpoint, a built-in OAuth 2.1 authorisation server (discovery, dynamic client registration, PKCE, refresh rotation) layered over the app's Google sign-in, personal access tokens for Claude Code, a JSON-RPC dispatcher, per-user server instructions and a tool registry. Builds on the flask skill and deploys unchanged with flask-deploy. Use whenever exposing a Flask app over MCP, adding or changing MCP tools, connecting Claude to an app as a custom connector, or debugging MCP auth/connection problems - even if the user doesn't say "MCP" explicitly (e.g. "let Claude read my app's data", "make this a Claude connector").
---

# Flask MCP server

A remote MCP server that lives inside a golden-template Flask app: same process, same database,
same Google sign-in, no SDK. Apply the `flask` and `python` skills as well. Patterns come from
Citadel (`~/github/citadel`), which runs this setup in production with Claude.ai, Claude Desktop and
Claude Code as clients.

## How it fits together

```
Client (Claude.ai / Claude Code)
  │ POST /  (no token)                      → 401 + WWW-Authenticate: resource_metadata=…
  │ GET /.well-known/oauth-protected-resource → names this app as its own authorisation server
  │ GET /.well-known/oauth-authorization-server → endpoints, S256 PKCE, public clients
  │ POST /oauth/register                     → client_id (nothing stored)
  │ GET /oauth/authorize ──► Google sign-in ──► consent page ──► redirect_uri?code=…&state=…
  │ POST /oauth/token (code + verifier)      → access + refresh token (mcp_tokens row)
  │ POST /  Bearer <token>  JSON-RPC         → initialize / tools/list / tools/call
  ▼
mcp/__init__.py  validate token → user_id → protocol.handle_jsonrpc → tools.handle_tool_call
```

Claude Code can skip OAuth with a personal access token from `/tokens/`, sent as
`Authorization: Bearer …`. Both kinds of token live in the same `mcp_tokens` table and are
indistinguishable to the MCP endpoint.

## Adding MCP to an app

1. Copy `assets/` into the project (it mirrors the project layout): `app/mcp/`, `app/pat.py`,
   `templates/mcp/`, `templates/tokens/`, `templates/sql/mcp_*.sql`, `templates/sql/user_by_id.sql`,
   `static/js/tokens.js`, `tests/test_mcp.py`. Rename `app.` imports to the project package.
2. Wire config, the app factory, `db.init_db`, the Google callbacks and `base.html` as in
   `references/wiring.md`.
3. Rewrite `SYSTEM_PROMPT` in `app/mcp/instructions.py` for the app's domain.
4. Replace or extend the example `whoami` tool with the app's tools - `references/tools.md`.
5. Run `pytest tests/test_mcp.py`.
6. Deploy, then connect a client - `references/clients.md`.

## Hard rules

- **Every tool declares `inputSchema`**, an object schema even when there are no arguments
  (`{'type': 'object', 'properties': {}, 'additionalProperties': False}`).
- **Never add `outputSchema`.** It breaks Claude-side tool use. `tests/test_mcp.py` enforces both.
- **Every tool is scoped to `user_id`.** The handler signature is `(args, user_id)`; every SQL
  query a tool runs filters on the user. `user_id` comes only from the validated token, never from
  arguments.
- **Tool failures are results, not protocol errors.** Return `_err(msg)` (`isError: True`) for bad
  input or missing records; raise `ValueError` for validation and let `handle_tool_call` convert it.
  Unexpected exceptions are logged with `logger.exception` and returned as a generic message -
  never the exception text.
- **Stateless Streamable HTTP.** One `POST /` endpoint; no sessions, no `Mcp-Session-Id`, no GET
  stream (Flask answers GET with 405, which the spec allows). Notifications get `204` and no body.
  Reply as SSE (`data: …\n\n`) when the client's `Accept` includes `text/event-stream`, else JSON.
- **Bearer tokens only, CSRF-exempt.** The MCP blueprint is exempt from CSRF; every MCP request is
  authenticated by `Authorization: Bearer`. A missing or bad token returns 401 with
  `WWW-Authenticate: Bearer resource_metadata="<base>/.well-known/oauth-protected-resource"` -
  that header is what starts the OAuth flow in Claude clients.
- **Base URL from the hostname allow-list.** Discovery documents and the 401 header are built from
  `base_url()`, which uses `APP_HOSTNAMES` and `CF-Visitor`/`FORCE_HTTPS` - never the raw `Host`
  header, never `url_for(..., _external=True)`.
- **The app is its own authorisation server.** Google is only the sign-in step inside
  `/oauth/authorize`; MCP clients never see Google tokens.
- **Own rate limit on the MCP endpoint.** The app-wide default (`50 per hour`) would throttle a
  single conversation; the endpoint carries `@limiter.limit(MCP_RATE_LIMIT)` instead.

## Reference files

| File | Read when |
|------|-----------|
| `references/wiring.md` | Adding MCP to an app - config, app factory, `init_db`, Google callback and nav changes |
| `references/auth.md` | Discovery, OAuth flow, PKCE, token storage, PATs, consent page, security trade-offs |
| `references/protocol.md` | The endpoint, JSON-RPC methods, SSE vs JSON, batches, `initialize` instructions |
| `references/tools.md` | Adding a tool - schema, handler, description writing, argument handling, SQL |
| `references/clients.md` | Connecting Claude.ai, Claude Desktop, Claude Code; testing with curl; troubleshooting |

## Assets

| Path | Purpose |
|------|---------|
| `app/mcp/__init__.py` | Blueprint: discovery, OAuth endpoints, consent, the MCP endpoint, `base_url()` |
| `app/mcp/tokens.py` | Auth codes, PKCE check, token issue/validate/refresh, PAT issue |
| `app/mcp/protocol.py` | JSON-RPC dispatcher (`initialize`, `ping`, `tools/list`, `tools/call`) |
| `app/mcp/instructions.py` | `SYSTEM_PROMPT` and per-user `initialize` instructions |
| `app/mcp/tools.py` | `TOOLS_LIST`, handler registry, `_ok`/`_err`, the example `whoami` tool |
| `app/pat.py` | `/tokens/` page: generate/revoke the PAT, list/revoke OAuth sessions |
| `templates/mcp/authorize.html` | Consent page (shows the client and where the code will be sent) |
| `templates/tokens/index.html` | Token page with the `claude mcp add` command |
| `static/js/tokens.js` | Copy buttons and the revoke modal (no inline JS, CSP-safe) |
| `templates/sql/mcp_*.sql` | Schema and queries for `mcp_auth_codes` and `mcp_tokens` |
| `tests/test_mcp.py` | Discovery, full OAuth + PKCE flow, refresh rotation, PATs, JSON-RPC, schema rules |
