"""Event ingestion, explorer, tenant isolation, and cached analytics."""

from tests.conftest import login, register


def _ingest(client, key, name, distinct_id="u1", props=None):
    return client.post(
        "/api/v1/events",
        json={"name": name, "distinct_id": distinct_id, "properties": props or {}},
        headers={"X-API-Key": key},
    )


def test_ingest_and_explore(client, owner, api_key):
    assert _ingest(client, api_key, "signup", "user-1").status_code == 202
    assert _ingest(client, api_key, "signup", "user-2").status_code == 202
    assert _ingest(client, api_key, "purchase", "user-1").status_code == 202

    page = client.get("/api/v1/events", headers=owner["headers"]).json()
    assert page["total"] == 3
    assert len(page["items"]) == 3

    # filter by name
    filtered = client.get("/api/v1/events?name=signup", headers=owner["headers"]).json()
    assert filtered["total"] == 2


def test_batch_ingest(client, owner, api_key):
    resp = client.post(
        "/api/v1/events/batch",
        json={"events": [{"name": "e", "distinct_id": f"u{i}"} for i in range(5)]},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 202
    assert resp.json()["ingested"] == 5


def test_tenant_isolation(client, owner, api_key):
    # owner ingests one event
    _ingest(client, api_key, "signup", "user-1")

    # second org with its own key ingests two events
    register(client, email="other@example.com", org="OtherCo")
    other_token = login(client, email="other@example.com")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    other_key = client.post(
        "/api/v1/api-keys", json={"name": "k"}, headers=other_headers
    ).json()["key"]
    _ingest(client, other_key, "signup", "x")
    _ingest(client, other_key, "signup", "y")

    # each org only sees its own events
    assert client.get("/api/v1/events", headers=owner["headers"]).json()["total"] == 1
    assert client.get("/api/v1/events", headers=other_headers).json()["total"] == 2


def test_analytics_overview_and_caching(client, owner, api_key):
    for i in range(4):
        _ingest(client, api_key, "signup", f"user-{i}")

    first = client.get("/api/v1/analytics/overview", headers=owner["headers"]).json()
    assert first["summary"]["total_events"] == 4
    assert first["summary"]["unique_users"] == 4
    assert first["summary"]["active_api_keys"] == 1
    assert first["cached"] is False
    assert len(first["events_per_day"]) == 14  # zero-filled window

    # second read is served from cache
    second = client.get("/api/v1/analytics/overview", headers=owner["headers"]).json()
    assert second["cached"] is True

    # ingestion invalidates the cache
    _ingest(client, api_key, "signup", "user-99")
    third = client.get("/api/v1/analytics/overview", headers=owner["headers"]).json()
    assert third["cached"] is False
    assert third["summary"]["total_events"] == 5
