DELETE FROM mcp_tokens WHERE access_token = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %} AND user_id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
