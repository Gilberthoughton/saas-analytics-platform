"""Event ingestion & explorer schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventIngest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    distinct_id: str = Field(min_length=1, max_length=255)
    properties: dict = Field(default_factory=dict)
    timestamp: datetime | None = None


class EventBatchIngest(BaseModel):
    events: list[EventIngest] = Field(min_length=1, max_length=500)


class IngestResult(BaseModel):
    ingested: int


class EventRead(BaseModel):
    id: UUID
    name: str
    distinct_id: str
    properties: dict
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class EventPage(BaseModel):
    """Paginated event explorer response."""

    items: list[EventRead]
    total: int
    limit: int
    offset: int
