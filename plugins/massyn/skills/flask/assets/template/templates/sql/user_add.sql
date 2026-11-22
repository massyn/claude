INSERT INTO users (name, email, role, passkey_handle)
VALUES ({% if dialect == 'sqlite' %}?, ?, ?, ?{% else %}%s, %s, %s, %s{% endif %})
