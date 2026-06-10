"""Audit log tests."""


def test_actions_are_recorded(client, owner, api_key):
    # `owner` registration + `api_key` creation both write audit entries.
    logs = client.get("/api/v1/audit-logs", headers=owner["headers"]).json()
    actions = {log["action"] for log in logs}
    assert "user.register" in actions
    assert "api_key.create" in actions


def test_filter_by_action(client, owner, api_key):
    logs = client.get(
        "/api/v1/audit-logs?action=api_key.create", headers=owner["headers"]
    ).json()
    assert len(logs) >= 1
    assert all(log["action"] == "api_key.create" for log in logs)
