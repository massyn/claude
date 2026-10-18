DELETE FROM mcp_tokens WHERE refresh_token = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
