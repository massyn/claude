{# sort_column and direction come from a whitelist in the route, never from the query string. #}
SELECT u.id, u.name, u.email, u.role, u.disabled, u.google_id, u.last_login, u.last_method, u.created_on,
       (SELECT COUNT(*) FROM passkeys p WHERE p.user_id = u.id) AS passkeys
FROM users u
ORDER BY {{ sort_column }} {{ direction }}, u.id
LIMIT {% if dialect == 'sqlite' %}?{% else %}%s{% endif %} OFFSET {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
