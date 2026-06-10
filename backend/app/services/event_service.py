"""Event ingestion + explorer service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.cache import Cache
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventIngest
from app.services.webhook_service import WebhookService


def analytics_cache_prefix(org_id: UUID) -> str:
    return f"analytics:{org_id}:"


class EventService:
    def __init__(
        self,
        db: Session,
        *,
        cache: Cache | None = None,
        webhook_service: WebhookService | None = None,
    ) -> None:
        self.db = db
        self.repo = EventRepository(db)
        self.cache = cache
        self.webhooks = webhook_service or WebhookService(db)

    def ingest(self, *, org_id: UUID, events: list[EventIngest]) -> int:
        models = [
            Event(
                organization_id=org_id,
                name=e.name,
                distinct_id=e.distinct_id,
                properties=e.properties,
                timestamp=e.timestamp or datetime.now(UTC),
            )
            for e in events
        ]
        count = self.repo.bulk_add(models)
        self.db.commit()

        # New events invalidate cached analytics for this tenant.
        if self.cache is not None:
            self.cache.delete_prefix(analytics_cache_prefix(org_id))

        # Best-effort webhook fan-out (recorded for observability).
        for e in events:
            self.webhooks.dispatch(
                org_id=org_id,
                event_name=e.name,
                payload={
                    "event": e.name,
                    "distinct_id": e.distinct_id,
                    "properties": e.properties,
                },
            )
        return count

    def explore(
        self,
        *,
        org_id: UUID,
        name: str | None,
        distinct_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Event], int]:
        return self.repo.list_for_org(
            org_id, name=name, distinct_id=distinct_id, limit=limit, offset=offset
        )
