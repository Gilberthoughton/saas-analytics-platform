"""Analytics service with read-through caching.

The overview is relatively expensive (several aggregations), so results are
cached per-organization in Redis with a short TTL and invalidated on ingestion.
"""

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.cache import Cache
from app.core.config import settings
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.event_repository import EventRepository
from app.schemas.analytics import (
    AnalyticsOverview,
    MetricsSummary,
    TimeseriesPoint,
    TopEvent,
)
from app.services.event_service import analytics_cache_prefix


class AnalyticsService:
    def __init__(self, db: Session, cache: Cache) -> None:
        self.db = db
        self.cache = cache
        self.events = EventRepository(db)
        self.api_keys = ApiKeyRepository(db)

    def overview(self, org_id: UUID, *, days: int = 14) -> AnalyticsOverview:
        cache_key = f"{analytics_cache_prefix(org_id)}overview:{days}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            data = json.loads(cached)
            data["cached"] = True
            return AnalyticsOverview.model_validate(data)

        overview = self._compute(org_id, days=days)
        self.cache.set(
            cache_key,
            overview.model_dump_json(),
            settings.ANALYTICS_CACHE_TTL_SECONDS,
        )
        return overview

    def _compute(self, org_id: UUID, *, days: int) -> AnalyticsOverview:
        start_of_today = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        summary = MetricsSummary(
            total_events=self.events.count_for_org(org_id),
            events_today=self.events.count_since(org_id, start_of_today),
            unique_users=self.events.count_unique_users(org_id),
            active_api_keys=sum(
                1 for k in self.api_keys.list_for_org(org_id) if k.is_active
            ),
        )

        per_day = self.events.events_per_day(org_id, days)
        series = self._fill_series(per_day, days)
        top = [
            TopEvent(name=name, count=count)
            for name, count in self.events.top_events(org_id, limit=5)
        ]
        return AnalyticsOverview(
            summary=summary, events_per_day=series, top_events=top, cached=False
        )

    @staticmethod
    def _fill_series(per_day: dict[str, int], days: int) -> list[TimeseriesPoint]:
        """Produce a continuous daily series (zero-filled) for the window."""
        today = datetime.now(UTC).date()
        points: list[TimeseriesPoint] = []
        for offset in range(days - 1, -1, -1):
            day = today - timedelta(days=offset)
            key = day.isoformat()
            points.append(TimeseriesPoint(date=key, count=per_day.get(key, 0)))
        return points
