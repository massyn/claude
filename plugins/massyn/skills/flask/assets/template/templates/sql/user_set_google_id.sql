UPDATE users
SET google_id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
WHERE id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
