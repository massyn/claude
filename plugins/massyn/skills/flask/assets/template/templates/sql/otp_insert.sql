INSERT INTO otp_codes (request_id, email, code_hash, expires_at)
VALUES ({% if dialect == 'sqlite' %}?, ?, ?, ?{% else %}%s, %s, %s, %s{% endif %})
