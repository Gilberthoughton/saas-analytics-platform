"""Data access for webhooks and their deliveries."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.webhook import Webhook, WebhookDelivery


class WebhookRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, webhook: Webhook) -> Webhook:
        self.db.add(webhook)
        self.db.flush()
        return webhook

    def get_for_org(self, org_id: UUID, webhook_id: UUID) -> Webhook | None:
        return self.db.scalar(
            select(Webhook).where(
                Webhook.id == webhook_id, Webhook.organization_id == org_id
            )
        )

    def list_for_org(self, org_id: UUID) -> list[Webhook]:
        return list(
            self.db.scalars(
                select(Webhook)
                .where(Webhook.organization_id == org_id)
                .order_by(desc(Webhook.created_at))
            ).all()
        )

    def list_active_for_event(self, org_id: UUID, event_name: str) -> list[Webhook]:
        hooks = self.db.scalars(
            select(Webhook).where(
                Webhook.organization_id == org_id, Webhook.is_active.is_(True)
            )
        ).all()
        # Empty event_types means "subscribe to all".
        return [h for h in hooks if not h.event_types or event_name in h.event_types]

    def delete(self, webhook: Webhook) -> None:
        self.db.delete(webhook)
        self.db.flush()

    def add_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        self.db.add(delivery)
        self.db.flush()
        return delivery

    def list_deliveries(
        self, webhook_id: UUID, limit: int = 50
    ) -> list[WebhookDelivery]:
        return list(
            self.db.scalars(
                select(WebhookDelivery)
                .where(WebhookDelivery.webhook_id == webhook_id)
                .order_by(desc(WebhookDelivery.created_at))
                .limit(limit)
            ).all()
        )
