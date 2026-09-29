"""Guards for outbound requests to tenant-controlled destinations.

Webhook URLs are supplied by tenants, so the delivery path is a server-side
request forgery (SSRF) surface: without validation a tenant can point a webhook
at ``http://127.0.0.1:8000/`` or the cloud metadata service and use the recorded
delivery status as an oracle for what the server can reach.

Validation is deny-by-default. A destination is accepted only when:

* the scheme is ``http`` or ``https`` (no ``file``, ``gopher``, ``ftp``, ...),
* the URL carries no embedded credentials (``user:pass@host`` confuses parsers),
* the host resolves, and **every** address it resolves to is globally routable.

Checking every resolved address matters: a hostname with both a public and a
private A record would otherwise pass on the public one and connect to the
private one. IPv4-mapped IPv6 addresses (``::ffff:127.0.0.1``) are unwrapped
before classification, since the mapped form is not itself flagged as loopback.

The resolved addresses are returned so the caller can connect to an address that
was actually validated, rather than re-resolving and giving a hostile DNS server
a second answer (DNS rebinding).
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

ALLOWED_SCHEMES = frozenset({"http", "https"})


class UnsafeWebhookDestination(ValueError):
    """Raised when a destination URL is not a safe target for delivery."""


def _classify(raw_ip: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    address = ipaddress.ip_address(raw_ip)
    # ::ffff:127.0.0.1 is not flagged loopback in its mapped form; unwrap it.
    mapped = getattr(address, "ipv4_mapped", None)
    return mapped if mapped is not None else address


def _reject_reason(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> str | None:
    if address.is_loopback:
        return "loopback address"
    if address.is_link_local:
        return "link-local address (cloud metadata range)"
    if address.is_private:
        return "private address"
    if address.is_reserved:
        return "reserved address"
    if address.is_multicast:
        return "multicast address"
    if address.is_unspecified:
        return "unspecified address"
    if not address.is_global:
        # Catches shared address space (100.64.0.0/10) and anything else the
        # stdlib does not consider publicly routable.
        return "non-globally-routable address"
    return None


def resolve_and_validate(url: str, *, allow_private: bool = False) -> list[str]:
    """Validate a tenant-supplied destination URL.

    Returns the sorted list of validated IP addresses the host resolves to.

    :param allow_private: relax the address checks for local development and
        hermetic tests. Scheme and credential checks always apply. Production
        configuration must leave this off.
    :raises UnsafeWebhookDestination: if the destination must not be contacted.
    """
    parsed = urlsplit(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeWebhookDestination(f"scheme {parsed.scheme!r} is not allowed")
    if parsed.username or parsed.password:
        raise UnsafeWebhookDestination("URL must not embed credentials")

    host = parsed.hostname
    if not host:
        raise UnsafeWebhookDestination("URL has no host")

    if allow_private:
        return []

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        # Unresolvable means unverifiable, so it is not safe to contact.
        raise UnsafeWebhookDestination(f"host {host!r} does not resolve") from exc

    raw_ips = {info[4][0] for info in infos}
    if not raw_ips:
        raise UnsafeWebhookDestination(f"host {host!r} does not resolve")

    for raw_ip in sorted(raw_ips):
        reason = _reject_reason(_classify(raw_ip))
        if reason is not None:
            raise UnsafeWebhookDestination(
                f"host {host!r} resolves to {raw_ip} ({reason})"
            )

    return sorted(raw_ips)
