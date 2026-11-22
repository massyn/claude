SELECT id, name, email, role, disabled, created_on
FROM users
WHERE id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
