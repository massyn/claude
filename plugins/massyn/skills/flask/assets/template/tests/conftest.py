"""Shared fixtures: the app on a throwaway SQLite database, with a fake Mailgun."""

import os
import tempfile

import pytest

# config.py insists on DATABASE_URL at import time; each test then points the app at its own file.
os.environ.setdefault('DATABASE_URL', f'sqlite:///{tempfile.mkdtemp()}/default.db')


@pytest.fixture
def app(tmp_path, monkeypatch):
    from app import create_app, limiter
    from app.db import init_db

    app = create_app()
    app.config.update(
        DATABASE_URL=f'sqlite:///{tmp_path / "test.db"}',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret',
        MAILGUN_API_KEY='key',
        MAILGUN_DOMAIN='mg.example.com',
        MAILGUN_FROM='App <login@mg.example.com>',
        ADMIN_USER='',
        TEST_USER='',
        ALLOW_SIGNUP=False,
        PASSKEY_SIGNUP=False,
        APP_HOSTNAMES=[],
        PASSKEY_RP_ID='',
        OTP_TTL_SECONDS=600,
        OTP_MAX_ATTEMPTS=5,
    )
    limiter.enabled = False
    init_db(app)
    app.sent = []
    monkeypatch.setattr(
        'app.auth.mailgun.send', lambda to, subject, text: app.sent.append((to, subject, text))
    )
    return app


@pytest.fixture
def client(app):
    return app.test_client()
