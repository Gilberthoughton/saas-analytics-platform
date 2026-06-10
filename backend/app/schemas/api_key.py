"""API key schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ApiKeyRead(BaseModel):
    id: UUID
    name: str
    prefix: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreated(ApiKeyRead):
    """Returned once on creation, including the plaintext key."""

    key: str
