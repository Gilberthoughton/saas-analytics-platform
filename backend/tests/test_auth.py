"""Auth + registration API tests."""

from tests.conftest import auth_headers, login, register


def test_health(client):
    assert client.get("/health").status_code == 200


def test_register_creates_user_org_and_owner(client):
    resp = register(client, email="new@example.com", org="NewCo")
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body

    token = login(client, email="new@example.com")
    me = client.get("/api/v1/auth/me", headers=auth_headers(token)).json()
    assert me["organization_name"] == "NewCo"
    assert me["role"] == "owner"  # registrant owns their org


def test_register_duplicate_email(client):
    register(client, email="dupe@example.com")
    assert register(client, email="dupe@example.com").status_code == 409


def test_register_validation(client):
    # short password
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "x@example.com",
            "password": "123",
            "full_name": "X",
            "organization_name": "Org",
        },
    )
    assert resp.status_code == 422


def test_login_wrong_password(client):
    register(client, email="user@example.com")
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_protected_route_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401
