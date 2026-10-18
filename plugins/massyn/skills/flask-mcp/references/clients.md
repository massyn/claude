# Connecting clients

The server URL is the site root, e.g. `https://myapp.example.com` - the MCP endpoint is `POST /`.

## Claude.ai and Claude Desktop (OAuth)

Settings → Connectors → Add custom connector → enter the server URL. Claude discovers the OAuth
endpoints, registers, and opens the app's sign-in and consent page. Afterwards the session appears
under OAuth sessions on `/tokens/`, where it can be revoked.

## Claude Code

With a personal access token (generate it on `/tokens/`, which shows this command filled in):

```bash
claude mcp add --transport http --scope user myapp https://myapp.example.com \
  --header "Authorization: Bearer <token>"
```

Or with OAuth: add it without the header, then run `/mcp` inside Claude Code and choose
authenticate - a browser opens on the consent page.

`--scope user` makes the server available in every project; leave it out to scope it to the current
directory. Check with `/mcp`.

## Testing with curl

```bash
TOKEN=...   # a PAT from /tokens/
URL=http://localhost:5000

curl -s -X POST $URL/ -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

curl -s -X POST $URL/ -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

curl -s -X POST $URL/ -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"whoami","arguments":{}}}'
```

Locally, `TEST_USER=alice` in `.env_dev` signs in without Google, so `/tokens/` works offline.
Claude.ai cannot reach `localhost`; test OAuth end to end against the deployed site.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| Connector fails straight after entering the URL | `/.well-known/oauth-protected-resource` not reachable, or the 401 lacks `WWW-Authenticate` |
| Discovery documents show `http://` or the wrong host | `FORCE_HTTPS` / `APP_HOSTNAME` not set in production `.env` |
| Sign-in completes but lands on the home page, not consent | Google callback not redirecting to `mcp.oauth_authorize` when `session['mcp_oauth']` is set |
| `invalid_grant` at the token step | Code expired (10 min) or reused, `redirect_uri`/`client_id` mismatch, or PKCE verifier wrong |
| 400 CSRF error on `/oauth/token` or `/` | MCP blueprint not passed to `csrf.exempt()` |
| Tools connect but calls fail with 429 | `MCP_RATE_LIMIT` too low, or the endpoint is missing its own limit and hitting the app default |
| Tools list but the model never calls them right | Weak tool descriptions or `SYSTEM_PROMPT` - see `tools.md` |
| Tool use breaks after a schema change | An `outputSchema` was added - remove it |
| Works in Claude Code, not Claude.ai | PAT vs OAuth: Claude.ai only does OAuth; check the OAuth flow, not the token |
