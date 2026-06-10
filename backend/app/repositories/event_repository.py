"""Data access for events: ingestion writes and explorer/analytics reads.

Every method is scoped by `organization_id`, enforcing tenant isolation at the
data layer.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.event import Event


class EventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def bulk_add(self, events: list[Event]) -> int:
        self.db.add_all(events)
        self.db.flush()
        return len(events)

    def list_for_org(
        self,
        org_id: UUID,
        *,
        name: str | None = None,
        distinct_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Event], int]:
        conditions = [Event.organization_id == org_id]
        if name:
            conditions.append(Event.name == name)
        if distinct_id:
            conditions.append(Event.distinct_id == distinct_id)

        total = self.db.scalar(
            select(func.count()).select_from(Event).where(*conditions)
        )
        items = list(
            self.db.scalars(
                select(Event)
                .where(*conditions)
                .order_by(desc(Event.timestamp))
                .limit(limit)
                .offset(offset)
            ).all()
        )
        return items, int(total or 0)

    # --- analytics aggregations ---------------------------------------------

    def count_for_org(self, org_id: UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Event)
                .where(Event.organization_id == org_id)
            )
            or 0
        )

    def count_since(self, org_id: UUID, since: datetime) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Event)
                .where(Event.organization_id == org_id, Event.timestamp >= since)
            )
            or 0
        )

    def count_unique_users(self, org_id: UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count(func.distinct(Event.distinct_id))).where(
                    Event.organization_id == org_id
                )
            )
            or 0
        )

    def events_per_day(self, org_id: UUID, days: int) -> dict[str, int]:
        since = datetime.now(UTC) - timedelta(days=days)
        rows = self.db.execute(
            select(
                func.date(Event.timestamp).label("day"),
                func.count().label("count"),
            )
            .where(Event.organization_id == org_id, Event.timestamp >= since)
            .group_by("day")
        ).all()
        return {str(day): int(count) for day, count in rows}

    def top_events(self, org_id: UUID, limit: int = 5) -> list[tuple[str, int]]:
        rows = self.db.execute(
            select(Event.name, func.count().label("count"))
            .where(Event.organization_id == org_id)
            .group_by(Event.name)
            .order_by(desc("count"))
            .limit(limit)
        ).all()
        return [(name, int(count)) for name, count in rows]
