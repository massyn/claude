DELETE FROM mcp_tokens WHERE user_id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %} AND client_id = 'pat'
