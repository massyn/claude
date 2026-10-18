CREATE TABLE IF NOT EXISTS mcp_auth_codes (
    code TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    client_id TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    code_challenge TEXT NOT NULL DEFAULT '',
    code_challenge_method TEXT NOT NULL DEFAULT 'S256',
    expires_at TEXT NOT NULL,
    created_at {% if dialect == 'sqlite' %}DATETIME{% else %}TIMESTAMP{% endif %} DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mcp_tokens (
    access_token TEXT PRIMARY KEY,
    refresh_token TEXT UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    client_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_used TEXT,
    created_at {% if dialect == 'sqlite' %}DATETIME{% else %}TIMESTAMP{% endif %} DEFAULT CURRENT_TIMESTAMP
);
