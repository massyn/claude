UPDATE mcp_tokens SET last_used = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %} WHERE access_token = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
