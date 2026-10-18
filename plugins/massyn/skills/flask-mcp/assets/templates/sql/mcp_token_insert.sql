INSERT INTO mcp_tokens (access_token, refresh_token, user_id, client_id, expires_at)
VALUES ({% if dialect == 'sqlite' %}?, ?, ?, ?, ?{% else %}%s, %s, %s, %s, %s{% endif %})
