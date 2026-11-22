DELETE FROM otp_codes WHERE id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
