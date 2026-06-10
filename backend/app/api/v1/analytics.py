"""Analytics dashboard data (JWT auth, cached)."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CacheDep, CurrentContext, DbSession
from app.schemas.analytics import AnalyticsOverview
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    summary="Metrics summary, time series, and top events",
)
def overview(
    context: CurrentContext,
    db: DbSession,
    cache: CacheDep,
    days: Annotated[int, Query(ge=1, le=90)] = 14,
) -> AnalyticsOverview:
    return AnalyticsService(db, cache).overview(context.organization_id, days=days)
