DELETE FROM mcp_auth_codes WHERE code = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
