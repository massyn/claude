UPDATE users
SET last_login = CURRENT_TIMESTAMP, last_method = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
WHERE id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
