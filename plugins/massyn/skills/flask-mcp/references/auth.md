# Authentication

Two ways in, one token table. OAuth is what Claude.ai, Claude Desktop and Claude Code's `/mcp`
sign-in use; a personal access token (PAT) is the copy-paste shortcut for Claude Code. The MCP
endpoint only ever sees `Authorization: Bearer <token>`, looks it up in `mcp_tokens`, and takes
`user_id` from the row.

## Discovery

A client that calls `POST /` without a valid token gets:

```
HTTP/1.1 401
WWW-Authenticate: Bearer resource_metadata="https://myapp.example.com/.well-known/oauth-protected-resource"
```

It then fetches, in order:

| URL | Standard | Says |
|-----|----------|------|
| `/.well-known/oauth-protected-resource` | RFC 9728 | The resource is this site; its authorisation server is this site |
| `/.well-known/oauth-authorization-server` | RFC 8414 | Authorise/token/register endpoints, `code` + S256 PKCE, public clients (`none` auth) |

Both are built from `base_url()` so they always name a trusted hostname over the right scheme.
If discovery returns `http://` behind Cloudflare/Nginx, set `FORCE_HTTPS=true`.

## OAuth 2.1 flow

1. **Register** - `POST /oauth/register` (RFC 7591 dynamic client registration). Clients are
   public, so nothing is stored: the server returns the client's own `client_id` or a random one.
   The `client_id` is later bound to the auth code and checked again at the token endpoint.
2. **Authorise** - `GET /oauth/authorize?response_type=code&client_id&redirect_uri&state&code_challenge&code_challenge_method=S256`.
   The parameters are parked in `session['mcp_oauth']`.
   - Not signed in → redirect to `auth.google`. The Google callback sees `mcp_oauth` in the session
     and redirects back to `/oauth/authorize`, which now renders the consent page from the session.
   - Signed in → consent page straight away.
3. **Consent** - `templates/mcp/authorize.html` shows the `client_id` and the host the code will be
   sent to. `POST /oauth/authorize` with `action=allow` creates a 10-minute, single-use auth code
   (`mcp_auth_codes`) and redirects to `redirect_uri?code=…&state=…`. Anything else redirects with
   `error=access_denied`. Either way the parked parameters are removed from the session.
4. **Exchange** - `POST /oauth/token` with `grant_type=authorization_code`, `code`, `client_id`,
   `redirect_uri`, `code_verifier`. `consume_auth_code()` checks expiry, that `client_id` and
   `redirect_uri` match, and that `base64url(sha256(verifier))` equals the stored challenge
   (constant-time compare), then deletes the code. Returns `access_token`, `refresh_token`,
   `token_type: Bearer`.
5. **Refresh** - `grant_type=refresh_token`. The old pair is deleted and a new pair issued
   (rotation); a reused refresh token fails with `invalid_grant`.

The token endpoint reads parameters from form data or JSON - clients differ.

## Token storage

```
mcp_auth_codes(code PK, user_id, client_id, redirect_uri, code_challenge, code_challenge_method, expires_at, created_at)
mcp_tokens(access_token PK, refresh_token UNIQUE NULL, user_id, client_id, expires_at, last_used, created_at)
```

- Tokens are `secrets.token_urlsafe(32)`.
- `last_used` is touched on every validated request; the token page shows it.
- PATs are rows with `client_id = 'pat'` and no refresh token. `issue_pat()` deletes the user's
  existing PAT first, so each user has at most one.

## Personal access tokens

`/tokens/` (`app/pat.py`) lets a signed-in user generate, regenerate and revoke their PAT and
revoke individual OAuth sessions. A new PAT is shown once, alongside the ready-made
`claude mcp add --transport http … --header "Authorization: Bearer …"` command. Destructive actions
go through Bootstrap confirm modals.

## Session instructions at sign-in

If the app needs per-user state to exist before the first MCP session (Citadel creates a per-user
"autoexec" entry), create it in `establish_session()`, which every sign-in method calls, and again, idempotently,
in `build_instructions()`. Log failures with `logger.exception`; never swallow them with `pass`.

## Security trade-offs (inherited from Citadel - decide per app)

These are deliberate simplifications. Change them when an app's data warrants it.

- **Access tokens do not expire.** Rows carry `expires_at = 2099-01-01` and `expires_in: 3600` is
  advisory only. Revocation is manual from `/tokens/`. To enforce expiry, write a real
  `expires_at` in `issue_tokens()` - `validate_token()` already checks it, and clients refresh on 401.
- **Tokens are stored in plain text.** A database leak exposes live tokens. To harden, store
  `sha256(token)` and look up by hash (the token page then cannot show a prefix).
- **Open registration, unvalidated `redirect_uri`.** Any `redirect_uri` is accepted, because
  registration stores nothing. PKCE stops interception but not consent phishing: someone can send a
  user an authorise link that delivers the code to their own host. The consent page shows the
  destination host to make this visible. To close it, store registered clients and their
  `redirect_uris`, or allow-list known callback hosts (`claude.ai`, `localhost`).
- **PKCE is optional.** A request without `code_challenge` is accepted. Every Claude client sends
  S256; to require it, reject an empty challenge in `oauth_authorize()`.
