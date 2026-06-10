"""End-to-end smoke test against whatever DATABASE_URL / REDIS_URL are set.

Run locally it uses the hermetic defaults; in CI it points at real PostgreSQL +
Redis service containers, exercising the full stack (ORM + cache) the way the
unit suite (SQLite + in-memory) cannot. Exits non-zero on any failure.
"""

import sys

from fastapi.testclient import TestClient

from app.main import app


def main() -> int:
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200, "health failed"

        # register -> creates user + org + owner membership
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": "smoke@example.com",
                "password": "password123",
                "full_name": "Smoke Test",
                "organization_name": "SmokeCo",
            },
        )
        assert reg.status_code == 201, f"register: {reg.status_code} {reg.text}"

        # login
        login = client.post(
            "/api/v1/auth/login",
            data={"username": "smoke@example.com", "password": "password123"},
        )
        assert login.status_code == 200, "login failed"
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # create API key
        key_resp = client.post(
            "/api/v1/api-keys", json={"name": "smoke"}, headers=headers
        )
        assert key_resp.status_code == 201, "create key failed"
        api_key = key_resp.json()["key"]

        # ingest events
        for i in range(5):
            r = client.post(
                "/api/v1/events",
                json={"name": "signup", "distinct_id": f"u{i}"},
                headers={"X-API-Key": api_key},
            )
            assert r.status_code == 202, "ingest failed"

        # analytics (exercises the cache backend)
        first = client.get("/api/v1/analytics/overview", headers=headers)
        assert first.status_code == 200, "analytics failed"
        assert first.json()["summary"]["total_events"] == 5, "wrong count"
        assert first.json()["cached"] is False
        second = client.get("/api/v1/analytics/overview", headers=headers)
        assert second.json()["cached"] is True, "cache not working"

        # audit logs recorded
        audit = client.get("/api/v1/audit-logs", headers=headers)
        assert audit.status_code == 200 and len(audit.json()) >= 2, "audit failed"

    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
