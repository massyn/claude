SELECT id, google_id, name, email, role, disabled, last_login, last_method, created_on
FROM users
WHERE email = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
