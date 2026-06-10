"""Membership management + RBAC enforcement + tenant context selection."""

from tests.conftest import auth_headers, login, register


def _add_second_user_as_member(client, owner, *, role="member"):
    """Register a second user (with their own org), then add them to owner's org."""
    register(client, email="bob@example.com", org="BobCo")
    bob_token = login(client, email="bob@example.com")
    resp = client.post(
        "/api/v1/members",
        json={"email": "bob@example.com", "role": role},
        headers=owner["headers"],
    )
    assert resp.status_code == 201
    # Bob acts within the owner's org via the X-Org-Id header.
    bob_headers = {**auth_headers(bob_token), "X-Org-Id": owner["organization_id"]}
    return bob_headers


def test_owner_lists_self_as_only_member(client, owner):
    members = client.get("/api/v1/members", headers=owner["headers"]).json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"


def test_add_member_requires_existing_user(client, owner):
    resp = client.post(
        "/api/v1/members",
        json={"email": "ghost@example.com", "role": "member"},
        headers=owner["headers"],
    )
    assert resp.status_code == 404


def test_add_member_and_list(client, owner):
    _add_second_user_as_member(client, owner)
    members = client.get("/api/v1/members", headers=owner["headers"]).json()
    assert {m["email"] for m in members} == {"owner@example.com", "bob@example.com"}


def test_member_cannot_create_api_key(client, owner):
    bob_headers = _add_second_user_as_member(client, owner, role="member")
    resp = client.post("/api/v1/api-keys", json={"name": "k"}, headers=bob_headers)
    assert resp.status_code == 403  # member < admin


def test_admin_can_create_api_key_after_promotion(client, owner):
    bob_headers = _add_second_user_as_member(client, owner, role="member")
    # find bob's user id
    members = client.get("/api/v1/members", headers=owner["headers"]).json()
    bob_id = next(m["user_id"] for m in members if m["email"] == "bob@example.com")

    promote = client.patch(
        f"/api/v1/members/{bob_id}",
        json={"role": "admin"},
        headers=owner["headers"],
    )
    assert promote.status_code == 200

    resp = client.post("/api/v1/api-keys", json={"name": "k"}, headers=bob_headers)
    assert resp.status_code == 201


def test_member_cannot_read_audit_logs(client, owner):
    bob_headers = _add_second_user_as_member(client, owner, role="member")
    assert client.get("/api/v1/audit-logs", headers=bob_headers).status_code == 403
    assert client.get("/api/v1/audit-logs", headers=owner["headers"]).status_code == 200


def test_wrong_org_header_is_forbidden(client, owner):
    register(client, email="carol@example.com", org="CarolCo")
    carol_token = login(client, email="carol@example.com")
    # Carol is not a member of the owner's org.
    headers = {**auth_headers(carol_token), "X-Org-Id": owner["organization_id"]}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 403
