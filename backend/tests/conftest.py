"""Pytest fixtures.

Each test runs against a fresh in-memory SQLite database and an in-memory cache,
so the suite is fast and hermetic — no PostgreSQL or Redis required. CI also runs
it against real PostgreSQL + Redis via service containers.
"""

import os

# Configure the app before it (and its cached Settings) is imported.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("CACHE_BACKEND", "memory")
os.environ.setdefault("ENVIRONMENT", "test")
# Webhook delivery tests point at a closed loopback port so they stay hermetic.
# SSRF protection itself is exercised with this relaxation explicitly disabled —
# see test_webhook_ssrf.py.
os.environ.setdefault("WEBHOOK_ALLOW_PRIVATE_DESTINATIONS", "true")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402,F401  (register models)
from app.core.cache import InMemoryCache, reset_cache_for_tests  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    reset_cache_for_tests(InMemoryCache())  # isolate cache per test
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- helpers ---------------------------------------------------------------


def register(
    client, *, email, password="password123", full_name="Test User", org="Acme"
):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "organization_name": org,
        },
    )


def login(client, *, email, password="password123") -> str:
    resp = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def owner(client):
    """Register + log in an owner; return token, headers, and ids."""
    register(client, email="owner@example.com", org="Acme")
    token = login(client, email="owner@example.com")
    headers = auth_headers(token)
    me = client.get("/api/v1/auth/me", headers=headers).json()
    return {
        "token": token,
        "headers": headers,
        "organization_id": me["organization_id"],
        "user_id": me["user"]["id"],
    }


@pytest.fixture()
def api_key(client, owner) -> str:
    """Create an API key for the owner's org; return the plaintext key."""
    resp = client.post(
        "/api/v1/api-keys", json={"name": "default"}, headers=owner["headers"]
    )
    return resp.json()["key"]
