SELECT u.id, u.name, u.email, u.role, u.disabled, u.google_id, u.last_login, u.last_method, u.created_on,
       (SELECT COUNT(*) FROM passkeys p WHERE p.user_id = u.id) AS passkeys
FROM users u
WHERE u.id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
