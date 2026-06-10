"""API key lifecycle + ingestion authentication."""


def test_create_key_returns_plaintext_once(client, owner):
    resp = client.post(
        "/api/v1/api-keys", json={"name": "prod"}, headers=owner["headers"]
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["key"].startswith("sk_live_")
    assert body["prefix"].startswith("sk_live_")
    assert body["is_active"] is True

    # The plaintext is never returned again by the list endpoint.
    listed = client.get("/api/v1/api-keys", headers=owner["headers"]).json()
    assert len(listed) == 1
    assert "key" not in listed[0]


def test_ingestion_requires_valid_key(client, api_key):
    # missing key
    assert (
        client.post(
            "/api/v1/events", json={"name": "x", "distinct_id": "u1"}
        ).status_code
        == 401
    )
    # bogus key
    assert (
        client.post(
            "/api/v1/events",
            json={"name": "x", "distinct_id": "u1"},
            headers={"X-API-Key": "sk_live_bogus"},
        ).status_code
        == 401
    )
    # valid key
    assert (
        client.post(
            "/api/v1/events",
            json={"name": "x", "distinct_id": "u1"},
            headers={"X-API-Key": api_key},
        ).status_code
        == 202
    )


def test_revoked_key_cannot_ingest(client, owner, api_key):
    keys = client.get("/api/v1/api-keys", headers=owner["headers"]).json()
    key_id = keys[0]["id"]

    revoke = client.delete(f"/api/v1/api-keys/{key_id}", headers=owner["headers"])
    assert revoke.status_code == 200
    assert revoke.json()["is_active"] is False

    resp = client.post(
        "/api/v1/events",
        json={"name": "x", "distinct_id": "u1"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 401
