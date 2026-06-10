"""Webhook management + delivery recording.

The webhook points at a closed local port so delivery fails fast (connection
refused) without real network — what we assert is that the *delivery is recorded*
and that subscription filtering works.
"""

DEAD_URL = "http://127.0.0.1:1/webhook"  # nothing listens here -> fast refusal


def _ingest(client, key, name, distinct_id="u1"):
    return client.post(
        "/api/v1/events",
        json={"name": name, "distinct_id": distinct_id},
        headers={"X-API-Key": key},
    )


def test_create_webhook_returns_secret_once(client, owner):
    resp = client.post(
        "/api/v1/webhooks",
        json={"url": DEAD_URL, "event_types": ["signup"]},
        headers=owner["headers"],
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["secret"]
    assert body["event_types"] == ["signup"]

    listed = client.get("/api/v1/webhooks", headers=owner["headers"]).json()
    assert len(listed) == 1
    assert "secret" not in listed[0]


def test_delivery_recorded_for_subscribed_event(client, owner, api_key):
    webhook = client.post(
        "/api/v1/webhooks",
        json={"url": DEAD_URL, "event_types": ["signup"]},
        headers=owner["headers"],
    ).json()

    # subscribed event -> a delivery attempt is recorded (and fails fast)
    _ingest(client, api_key, "signup")
    deliveries = client.get(
        f"/api/v1/webhooks/{webhook['id']}/deliveries", headers=owner["headers"]
    ).json()
    assert len(deliveries) == 1
    assert deliveries[0]["event_name"] == "signup"
    assert deliveries[0]["success"] is False  # dead endpoint

    # non-subscribed event -> no new delivery
    _ingest(client, api_key, "pageview")
    deliveries = client.get(
        f"/api/v1/webhooks/{webhook['id']}/deliveries", headers=owner["headers"]
    ).json()
    assert len(deliveries) == 1


def test_delete_webhook(client, owner):
    webhook = client.post(
        "/api/v1/webhooks",
        json={"url": DEAD_URL, "event_types": []},
        headers=owner["headers"],
    ).json()
    assert (
        client.delete(
            f"/api/v1/webhooks/{webhook['id']}", headers=owner["headers"]
        ).status_code
        == 204
    )
    assert client.get("/api/v1/webhooks", headers=owner["headers"]).json() == []
