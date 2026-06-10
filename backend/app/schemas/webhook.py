"""Webhook schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class WebhookCreate(BaseModel):
    url: HttpUrl
    event_types: list[str] = Field(
        default_factory=list,
        description="Event names to subscribe to; empty = all events.",
    )


class WebhookRead(BaseModel):
    id: UUID
    url: str
    event_types: list[str]
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WebhookCreated(WebhookRead):
    """Returned once on creation, including the signing secret."""

    secret: str


class WebhookDeliveryRead(BaseModel):
    id: UUID
    event_name: str
    status_code: int
    success: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
