UPDATE users
SET name = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}, role = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}, disabled = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
WHERE id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
