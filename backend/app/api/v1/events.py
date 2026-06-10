"""Event ingestion (API-key auth) and the event explorer (JWT auth)."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import ApiKeyContext, CacheDep, CurrentContext, DbSession
from app.schemas.event import (
    EventBatchIngest,
    EventIngest,
    EventPage,
    EventRead,
    IngestResult,
)
from app.services.event_service import EventService

router = APIRouter(tags=["events"])


@router.post(
    "/events",
    response_model=IngestResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a single event (X-API-Key auth)",
)
def ingest_event(
    payload: EventIngest, db: DbSession, cache: CacheDep, api_key: ApiKeyContext
) -> IngestResult:
    count = EventService(db, cache=cache).ingest(
        org_id=api_key.organization_id, events=[payload]
    )
    return IngestResult(ingested=count)


@router.post(
    "/events/batch",
    response_model=IngestResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a batch of events (X-API-Key auth)",
)
def ingest_batch(
    payload: EventBatchIngest, db: DbSession, cache: CacheDep, api_key: ApiKeyContext
) -> IngestResult:
    count = EventService(db, cache=cache).ingest(
        org_id=api_key.organization_id, events=payload.events
    )
    return IngestResult(ingested=count)


@router.get(
    "/events",
    response_model=EventPage,
    summary="Explore events (JWT auth, filterable + paginated)",
)
def explore_events(
    context: CurrentContext,
    db: DbSession,
    name: Annotated[str | None, Query()] = None,
    distinct_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EventPage:
    items, total = EventService(db).explore(
        org_id=context.organization_id,
        name=name,
        distinct_id=distinct_id,
        limit=limit,
        offset=offset,
    )
    return EventPage(
        items=[EventRead.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    )
