SELECT access_token, client_id, expires_at, created_at, last_used
FROM mcp_tokens
WHERE user_id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %} AND client_id != 'pat'
ORDER BY created_at DESC
