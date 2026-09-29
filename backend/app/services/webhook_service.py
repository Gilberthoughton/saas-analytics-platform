"""Webhook management and delivery.

Delivery is best-effort and synchronous here, with every attempt recorded as a
`WebhookDelivery` for observability. The HTTP sender is injectable so the
delivery path is unit-testable without real network calls. In production this
would move behind a durable queue with retries (documented in the README).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Protocol
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.ssrf import UnsafeWebhookDestination, resolve_and_validate
from app.models.webhook import Webhook, WebhookDelivery
from app.repositories.webhook_repository import WebhookRepository
from app.services.audit_service import AuditService


class WebhookSender(Protocol):
    def send(self, url: str, payload: dict, secret: str) -> tuple[int, bool]: ...


def sign_payload(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class HttpWebhookSender:
    """Default sender: POSTs JSON with an HMAC-SHA256 signature header.

    The destination is re-validated immediately before the request (see
    `app.core.ssrf`) rather than trusting the check made at creation time: a
    hostname that was public then may resolve elsewhere now, and rows created
    before destination validation existed are still in the table.
    """

    def __init__(self, timeout: float = 3.0) -> None:
        self.timeout = timeout

    def send(self, url: str, payload: dict, secret: str) -> tuple[int, bool]:
        import httpx

        try:
            validated_ips = resolve_and_validate(
                url, allow_private=settings.WEBHOOK_ALLOW_PRIVATE_DESTINATIONS
            )
        except UnsafeWebhookDestination:
            # Recorded as a failed attempt; the tenant learns nothing about what
            # the server could or could not reach.
            return 0, False

        body = json.dumps(payload).encode()
        signature = sign_payload(secret, body)
        target, headers = _pin_to_validated_address(url, validated_ips)
        headers |= {
            "Content-Type": "application/json",
            "X-Signature-256": f"sha256={signature}",
        }
        try:
            resp = httpx.post(
                target,
                content=body,
                headers=headers,
                timeout=self.timeout,
                # A redirect is resolved by the *destination*, so following one
                # would hand the tenant an unvalidated second hop.
                follow_redirects=False,
                extensions={"sni_hostname": urlsplit(url).hostname or ""},
            )
            return resp.status_code, 200 <= resp.status_code < 300
        except Exception:
            return 0, False


def _pin_to_validated_address(url: str, validated_ips: list[str]) -> tuple[str, dict]:
    """Rewrite the URL to connect to an address that was actually validated.

    Re-resolving at connection time would let a hostile DNS server return a
    private address on the second lookup (DNS rebinding). Connecting to the
    validated address with the original Host header preserves virtual hosting;
    the caller passes the original hostname as the TLS SNI name so certificate
    verification is still performed against the hostname.

    When no addresses were validated (local-development mode) the URL is used
    unchanged.
    """
    parsed = urlsplit(url)
    host = parsed.hostname
    if not validated_ips or not host:
        return url, {}

    chosen = validated_ips[0]
    literal = f"[{chosen}]" if ":" in chosen else chosen
    netloc = f"{literal}:{parsed.port}" if parsed.port else literal
    pinned = parsed._replace(netloc=netloc).geturl()
    host_header = f"{host}:{parsed.port}" if parsed.port else host
    return pinned, {"Host": host_header}


class WebhookService:
    def __init__(self, db: Session, sender: WebhookSender | None = None) -> None:
        self.db = db
        self.repo = WebhookRepository(db)
        self.audit = AuditService(db)
        self.sender = sender or HttpWebhookSender()

    def create(
        self, *, org_id: UUID, url: str, event_types: list[str], actor_user_id: UUID
    ) -> tuple[Webhook, str]:
        # Reject unreachable-by-policy destinations at creation so the tenant gets
        # an immediate, actionable error instead of silently failing deliveries.
        # Delivery re-validates regardless (see HttpWebhookSender.send).
        resolve_and_validate(
            url, allow_private=settings.WEBHOOK_ALLOW_PRIVATE_DESTINATIONS
        )
        secret = secrets.token_hex(16)
        webhook = self.repo.add(
            Webhook(
                organization_id=org_id,
                url=url,
                secret=secret,
                event_types=event_types,
            )
        )
        self.audit.record(
            organization_id=org_id,
            actor_user_id=actor_user_id,
            action="webhook.create",
            meta={"url": url},
        )
        self.db.commit()
        self.db.refresh(webhook)
        return webhook, secret

    def list(self, org_id: UUID) -> list[Webhook]:
        return self.repo.list_for_org(org_id)

    def get(self, org_id: UUID, webhook_id: UUID) -> Webhook | None:
        return self.repo.get_for_org(org_id, webhook_id)

    def delete(self, *, org_id: UUID, webhook_id: UUID, actor_user_id: UUID) -> bool:
        webhook = self.repo.get_for_org(org_id, webhook_id)
        if webhook is None:
            return False
        self.repo.delete(webhook)
        self.audit.record(
            organization_id=org_id,
            actor_user_id=actor_user_id,
            action="webhook.delete",
            meta={"url": webhook.url},
        )
        self.db.commit()
        return True

    def list_deliveries(self, webhook_id: UUID) -> list[WebhookDelivery]:
        return self.repo.list_deliveries(webhook_id)

    def dispatch(self, *, org_id: UUID, event_name: str, payload: dict) -> int:
        """Deliver one event to all subscribed webhooks. Returns attempt count."""
        hooks = self.repo.list_active_for_event(org_id, event_name)
        for hook in hooks:
            status_code, success = self.sender.send(hook.url, payload, hook.secret)
            self.repo.add_delivery(
                WebhookDelivery(
                    webhook_id=hook.id,
                    event_name=event_name,
                    status_code=status_code,
                    success=success,
                )
            )
        if hooks:
            self.db.commit()
        return len(hooks)
