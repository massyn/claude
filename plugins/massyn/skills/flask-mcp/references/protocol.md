# Protocol

MCP is JSON-RPC 2.0 over HTTP. This server is stateless: every request carries its bearer token, the
token yields `user_id`, and nothing is kept between requests.

## The endpoint

`POST /` in `app/mcp/__init__.py`:

1. Rate-limit (`MCP_RATE_LIMIT`).
2. Require `Authorization: Bearer <token>` and `validate_token()` it - else 401 with the
   `WWW-Authenticate` discovery header.
3. Parse JSON; empty or invalid → 400.
4. A list is a batch: dispatch each message, drop `None` results, return the list (or 204 if every
   message was a notification). A single message: dispatch, 204 if `None`.
5. If `Accept` contains `text/event-stream`, wrap the payload as one SSE event
   (`data: <json>\n\n`); otherwise return plain JSON. Claude clients send both types in `Accept`.

Only `POST` is routed. A client's optional `GET` (to open a server-push stream) gets 405, which the
spec allows for servers with nothing to push.

The MCP route shares `/` with the app's home page; Flask dispatches by method, so `GET /` still
renders the site.

## Methods

`handle_jsonrpc(data, user_id)` in `app/mcp/protocol.py`:

| Method | Response |
|--------|----------|
| `initialize` | `protocolVersion`, `capabilities: {tools: {}}`, `serverInfo` (`MCP_SERVER_NAME`, `VERSION`), `instructions` |
| `ping` | `{}` (nothing if sent as a notification) |
| `tools/list` | `{tools: TOOLS_LIST}` |
| `tools/call` | `handle_tool_call(name, arguments, user_id)` - always a result, `isError` marks tool failure |
| any notification (no `id`) | nothing - includes `notifications/initialized` |
| anything else with an `id` | error `-32601 Method not found` |

`protocolVersion` is `2024-11-05`, the version Citadel runs against current Claude clients. Only
raise it after testing a real client against the new version.

To add another capability (resources, prompts), add it to `capabilities` in `initialize` and a
branch for its methods in `handle_jsonrpc`, each delegating to its own module.

## `initialize` instructions

The `instructions` string is injected into the client's system prompt for the whole conversation -
it is the most effective place to steer how the model uses the tools. `build_instructions(user_id)`
in `app/mcp/instructions.py` returns:

1. `SYSTEM_PROMPT` - product-level rules, the same for every user: what the domain objects are,
   which tool to call first, naming and tagging conventions, things never to do.
2. Per-user context appended under headings - Citadel adds the user's own rules entry and a list of
   their rooms, so the model is oriented before its first tool call.

Keep product rules in `SYSTEM_PROMPT` (code, reviewed) and personal preferences in user data
(editable through the tools). If the per-user lookup fails, log it and return the bare prompt -
`initialize` must not fail.

Tool `description`s carry the per-tool rules; `instructions` carry the cross-cutting ones.
