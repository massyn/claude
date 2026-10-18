SELECT code, user_id, client_id, redirect_uri, code_challenge, code_challenge_method, expires_at
FROM mcp_auth_codes
WHERE code = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
