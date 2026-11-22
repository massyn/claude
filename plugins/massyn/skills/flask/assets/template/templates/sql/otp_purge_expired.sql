DELETE FROM otp_codes WHERE expires_at < {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
