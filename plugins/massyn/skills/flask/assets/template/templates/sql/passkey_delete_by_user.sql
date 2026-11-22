DELETE FROM passkeys WHERE user_id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
