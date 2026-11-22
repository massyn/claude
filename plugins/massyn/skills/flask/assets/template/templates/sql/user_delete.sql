DELETE FROM users WHERE id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
