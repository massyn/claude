DELETE FROM otp_codes WHERE email = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
