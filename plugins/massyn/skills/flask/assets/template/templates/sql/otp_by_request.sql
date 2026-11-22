SELECT id, email, code_hash, attempts, expires_at
FROM otp_codes
WHERE request_id = {% if dialect == 'sqlite' %}?{% else %}%s{% endif %}
