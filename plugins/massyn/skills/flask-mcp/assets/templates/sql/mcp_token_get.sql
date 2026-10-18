SELECT access_token, refresh_token, user_id, client_id, expires_at
FROM mcp_tokens
WHERE access_token = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
