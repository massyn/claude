INSERT INTO mcp_auth_codes (code, user_id, client_id, redirect_uri, code_challenge, code_challenge_method, expires_at)
VALUES ({% if dialect == 'sqlite' %}?, ?, ?, ?, ?, ?, ?{% else %}%s, %s, %s, %s, %s, %s, %s{% endif %})
