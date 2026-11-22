CREATE TABLE IF NOT EXISTS users (
    {% if dialect == 'sqlite' %}
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {% else %}
    id SERIAL PRIMARY KEY,
    {% endif %}
    -- NULL unless the user signed in with Google, and optional even then (Google is an extra).
    google_id TEXT UNIQUE,
    name TEXT NOT NULL,
    -- Always lower case. The identity every sign-in method resolves to; NULL for passkey-only users.
    email TEXT UNIQUE,
    -- 'user' or 'admin'. The ADMIN_USER breakglass email is treated as admin without a row here.
    role TEXT NOT NULL DEFAULT 'user',
    -- 1 blocks every sign-in method and ends any live session. ADMIN_USER is never blocked.
    disabled INTEGER NOT NULL DEFAULT 0,
    last_login {% if dialect == 'sqlite' %}DATETIME{% else %}TIMESTAMP{% endif %},
    last_method TEXT,  -- how they last signed in: code, google, passkey or test
    -- WebAuthn user handle (base64url): names the user on their passkeys without revealing the id.
    passkey_handle TEXT UNIQUE NOT NULL,
    created_on {% if dialect == 'sqlite' %}DATETIME{% else %}TIMESTAMP{% endif %} DEFAULT CURRENT_TIMESTAMP
);

-- A user's passkeys (WebAuthn credentials). Only the public key is stored: the private key stays on
-- the user's device or in their password manager.
CREATE TABLE IF NOT EXISTS passkeys (
    {% if dialect == 'sqlite' %}
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {% else %}
    id SERIAL PRIMARY KEY,
    {% endif %}
    user_id INTEGER NOT NULL REFERENCES users(id),
    credential_id TEXT UNIQUE NOT NULL,  -- base64url
    public_key TEXT NOT NULL,            -- base64url COSE key
    sign_count BIGINT NOT NULL DEFAULT 0,
    created_on {% if dialect == 'sqlite' %}DATETIME{% else %}TIMESTAMP{% endif %} DEFAULT CURRENT_TIMESTAMP,
    last_used {% if dialect == 'sqlite' %}DATETIME{% else %}TIMESTAMP{% endif %}
);

CREATE INDEX IF NOT EXISTS idx_passkeys_user_id ON passkeys (user_id);

-- Emailed one-time sign-in codes. One live code per email; only an HMAC of the code is stored.
CREATE TABLE IF NOT EXISTS otp_codes (
    {% if dialect == 'sqlite' %}
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {% else %}
    id SERIAL PRIMARY KEY,
    {% endif %}
    request_id TEXT UNIQUE NOT NULL,  -- also held in the requesting browser's session
    email TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    expires_at BIGINT NOT NULL,       -- Unix time, so both dialects compare it the same way
    created_on {% if dialect == 'sqlite' %}DATETIME{% else %}TIMESTAMP{% endif %} DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_otp_codes_email ON otp_codes (email);
