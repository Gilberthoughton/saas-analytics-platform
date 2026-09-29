"""Regression tests: tenant-supplied webhook destinations are untrusted.

Webhook delivery previously POSTed to any URL a tenant supplied, so a tenant
could aim it at loopback, a private range, or the cloud metadata service and read
the resulting status code back from the deliveries endpoint.

These tests run with the local-development relaxation explicitly OFF, which is
the production configuration.
"""

import socket

import pytest

from app.core.ssrf import (
    UnsafeWebhookDestination,
    resolve_and_validate,
)
from app.services.webhook_service import _pin_to_validated_address

BLOCKED_URLS = [
    pytest.param("http://127.0.0.1:8000/hook", id="ipv4-loopback"),
    pytest.param("http://localhost:8000/hook", id="localhost-name"),
    pytest.param("http://[::1]:8000/hook", id="ipv6-loopback"),
    pytest.param("http://169.254.169.254/latest/meta-data/", id="cloud-metadata"),
    pytest.param("http://10.0.0.5/hook", id="private-10"),
    pytest.param("http://192.168.1.10/hook", id="private-192168"),
    pytest.param("http://172.16.0.5/hook", id="private-172"),
    pytest.param("http://100.64.0.1/hook", id="carrier-grade-nat"),
    pytest.param("http://0.0.0.0/hook", id="unspecified"),
    pytest.param("http://[::ffff:127.0.0.1]/hook", id="ipv4-mapped-ipv6-loopback"),
]


@pytest.mark.parametrize("url", BLOCKED_URLS)
def test_internal_destinations_are_rejected(url):
    with pytest.raises(UnsafeWebhookDestination):
        resolve_and_validate(url, allow_private=False)


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("file:///etc/passwd", id="file"),
        pytest.param("gopher://example.com/", id="gopher"),
        pytest.param("ftp://example.com/", id="ftp"),
    ],
)
def test_non_http_schemes_are_rejected(url):
    with pytest.raises(UnsafeWebhookDestination, match="scheme"):
        resolve_and_validate(url, allow_private=False)


def test_embedded_credentials_are_rejected():
    """user:pass@host is a classic parser-confusion vector."""
    with pytest.raises(UnsafeWebhookDestination, match="credentials"):
        resolve_and_validate("http://user:pass@example.com/hook", allow_private=False)


def test_unresolvable_host_is_rejected():
    """Unverifiable is treated as unsafe rather than attempted."""
    with pytest.raises(UnsafeWebhookDestination, match="does not resolve"):
        resolve_and_validate("http://no-such-host.invalid/hook", allow_private=False)


def test_public_destination_is_accepted(monkeypatch):
    """A genuinely public host is allowed — the guard must not block real webhooks."""

    def fake_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    assert resolve_and_validate("https://example.com/hook") == ["93.184.216.34"]


def test_host_with_mixed_public_and_private_records_is_rejected(monkeypatch):
    """Every resolved address must pass, not just the first one."""

    def fake_getaddrinfo(host, port, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeWebhookDestination, match="127.0.0.1"):
        resolve_and_validate("http://split-horizon.example/hook")


def test_delivery_connects_to_the_validated_address_not_the_hostname():
    """DNS rebinding: the request must target an address we already validated."""
    target, headers = _pin_to_validated_address(
        "https://example.com/hook", ["93.184.216.34"]
    )
    assert target == "https://93.184.216.34/hook"
    assert headers["Host"] == "example.com"


def test_pinning_preserves_port_and_brackets_ipv6():
    target, headers = _pin_to_validated_address(
        "http://example.com:8443/hook", ["2606:2800:220:1:248:1893:25c8:1946"]
    )
    assert target == "http://[2606:2800:220:1:248:1893:25c8:1946]:8443/hook"
    assert headers["Host"] == "example.com:8443"


def test_create_webhook_rejects_internal_destination(client, owner, monkeypatch):
    """End to end through the API, with the production setting in force."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "WEBHOOK_ALLOW_PRIVATE_DESTINATIONS", False)
    resp = client.post(
        "/api/v1/webhooks",
        json={"url": "http://169.254.169.254/latest/meta-data/"},
        headers=owner["headers"],
    )
    assert resp.status_code == 400
    assert "Unsafe webhook destination" in resp.json()["detail"]


def test_delivery_to_internal_destination_is_not_attempted(monkeypatch):
    """A row that predates validation must still not be delivered to."""
    import httpx

    from app.core.config import settings
    from app.services.webhook_service import HttpWebhookSender

    monkeypatch.setattr(settings, "WEBHOOK_ALLOW_PRIVATE_DESTINATIONS", False)

    def explode(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("delivery must not be attempted to a blocked host")

    monkeypatch.setattr(httpx, "post", explode)
    status_code, success = HttpWebhookSender().send(
        "http://127.0.0.1:8000/hook", {"event": "signup"}, "secret"
    )
    assert (status_code, success) == (0, False)


def test_delivery_does_not_follow_redirects(monkeypatch):
    """Following a redirect would hand the tenant an unvalidated second hop."""
    import httpx

    from app.core.config import settings
    from app.services.webhook_service import HttpWebhookSender

    monkeypatch.setattr(settings, "WEBHOOK_ALLOW_PRIVATE_DESTINATIONS", False)
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)

        class _Resp:
            status_code = 200

        return _Resp()

    def fake_getaddrinfo(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(httpx, "post", fake_post)

    HttpWebhookSender().send("https://example.com/hook", {"e": 1}, "secret")

    assert captured["follow_redirects"] is False
    assert captured["url"] == "https://93.184.216.34/hook"
    assert captured["headers"]["Host"] == "example.com"
    assert captured["extensions"]["sni_hostname"] == "example.com"
    # The signature must still be computed and sent.
    assert captured["headers"]["X-Signature-256"].startswith("sha256=")
