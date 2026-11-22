UPDATE otp_codes SET attempts = attempts + 1 WHERE id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
